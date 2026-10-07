import html
import re

BR = re.compile(r"\s*</?br\s*/?>\s*", re.I)
P = re.compile(r"</?p\s*/?>", re.I)
TAG = re.compile(r"<[^>]*>")


def strip_tags(s):
    if not s:
        return ""
    s = str(s)
    s = BR.sub("\n", s)
    s = P.sub("\n", s)
    s = TAG.sub("", s)
    s = html.unescape(s)
    lines = [ln.strip() for ln in s.splitlines()]
    return "\n".join(ln for ln in lines if ln)


def gv(o):
    if o is None:
        return ""
    return o if isinstance(o, str) else (o.get("value") if isinstance(o, dict) else "")


def collect_choose(info):
    out = []
    for xt in info.get("xtlist") or []:
        letter = (xt.get("answer") or "").strip()
        opt = next((x for x in (xt.get("xxlist") or []) if (x.get("xx_mc") or "").strip() == letter), None)
        if opt is not None:
            out.append((letter, strip_tags(gv(opt.get("xx_nr"))).strip()))
    return out


def collect_role(info):
    out = []
    for q in info.get("question") or []:
        std = q.get("std") or []
        if std:
            v = strip_tags(gv(std[0])).strip()
            if v:
                out.append(v)
    return out


def collect_picture(info):
    std = info.get("std") or []
    v = strip_tags(gv(std[0])).strip() if std else ""
    if not v:
        v = strip_tags(gv(info.get("keypoint"))).strip()
    return [v] if v else []


def collect_value(info):
    v = strip_tags(gv(info.get("value"))).strip()
    return [v] if v else []


COLLECTORS = {
    "choose": collect_choose,
    "role": collect_role,
    "picture": collect_picture,
    "read": collect_value,
    "word": collect_value,
    "repeat_essay": collect_value,
    "repeat_dialogue": collect_value,
}
TITLE = {"choose": "听后选择", "role": "听后回答", "picture": "听后转述", "read": "朗读短文"}
ORDER = ["choose", "role", "picture", "read"]


def flat(items, s):
    out = []
    for it in items.get(s) or []:
        out.extend(it if isinstance(it, list) else [it])
    return out


def render_blocks(items):
    blocks = []
    choose = flat(items, "choose")
    if choose:
        lines = ["%d.  %s  %s" % (i + 1, letter, content) for i, (letter, content) in enumerate(choose)]
        blocks.append(("听后选择", lines))
    role = flat(items, "role")
    if role:
        lines = ["%d. %s" % (i + 1, text) for i, text in enumerate(role)]
        blocks.append(("听后回答", lines))
    for s in ORDER[2:]:
        arr = flat(items, s)
        if arr:
            blocks.append((TITLE[s], arr))
    for s in sorted(items):
        if s not in ORDER:
            arr = flat(items, s)
            if arr:
                blocks.append((s, arr))
    return blocks


def render_text(items):
    blocks = render_blocks(items)
    return "\n\n".join(t + (":" if t == "听后选择" else "：") + "\n" + "\n".join(b) for t, b in blocks) + "\n"

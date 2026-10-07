# -*- coding: utf-8 -*-
"""
ets_answers.py  —— E听说(ETS) 试卷答题内容离线提取工具
参考 Intellect.exe 的实现思路：读取 ETS 数据目录里按类型（collector.*）组织的
content.json，按类型提取"答案/正文"，按试卷分节输出为 .txt：

    听后选择:     每题一行 “序号.  答案字母  选项内容”
    听后回答：    每题一行 “序号. 答案内容”
    听后转述：    整段正文
    朗读短文：    整段正文

仅使用 Python 标准库，完全离线运行。

用法：
    python ets_answers.py [目标]
      [目标] 可给：
        一份试卷文件夹（含 content_* 子目录），例如 ...\\ETS\\586649
        整个 ETS 数据目录（默认）→ 此时默认取最近一次下载的文件夹
  --output out.txt      输出文件路径（默认 ./ets_answers.txt）
  --mode newest|all     当目标是整个数据目录时：newest 只处理最近一次下载；all 处理全部
  --keep-tags           保留 value 里的 HTML 标签（默认去掉）

说明：各 collector 类型的提取规则
  choose          每题取 answer 指向的选项 → “字母 + 选项内容”
  role            每题取 question[i].std[0].value（一个 item 可能含多问，全部输出）
  picture         取 std[0].value（转述整段）
  read            取 info.value（朗读短文，去标签）
  word/repeat_*   保留在各自英文小节下
"""

import argparse
import json
import os
import sys

import ets_config
from ets_core import COLLECTORS, gv, render_text


def find_content_folders(top):
    """某文件夹下直接的 content_* 子目录里的 content.json。"""
    out = []
    for name in sorted(os.listdir(top)):
        if name.startswith("content_"):
            cp = os.path.join(top, name, "content.json")
            if os.path.isfile(cp):
                out.append(cp)
    return out


def iter_targets(root, mode):
    """返回要处理的 content.json 路径列表。"""
    # 1) root 本身就是试卷文件夹（直接含 content_*）
    direct = find_content_folders(root)
    if direct:
        return direct

    # 2) root 是数据目录：找含 content_* 的顶层文件夹
    tops = [os.path.join(root, n) for n in os.listdir(root)
            if os.path.isdir(os.path.join(root, n))]
    with_content = []
    for t in tops:
        if find_content_folders(t):
            with_content.append(t)

    if mode == "all":
        out = []
        for t in with_content:
            out.extend(find_content_folders(t))
        return out

    # newest：取 mtime 最新的顶层文件夹
    if with_content:
        newest = max(with_content, key=os.path.getmtime)
        return find_content_folders(newest)
    return []


def main():
    ap = argparse.ArgumentParser(description="E听说(ETS) 试卷答题内容离线提取")
    ap.add_argument("target", nargs="?", default=ets_config.load_root(), help="试卷文件夹或 ETS 数据目录")
    ap.add_argument("--output", default=os.path.join(os.path.dirname(os.path.abspath(__file__)), "ets_answers.txt"))
    ap.add_argument("--mode", choices=["newest", "all"], default="newest")
    ap.add_argument("--keep-tags", action="store_true")
    args = ap.parse_args()

    root = args.target
    if not os.path.isdir(root):
        sys.exit("目标目录不存在: " + root)

    # 收集：suffix -> list[(序号项)]  （choose/role 编号；picture/read 为文本块）
    by_type = {}
    unreadable = 0
    for cp in iter_targets(root, args.mode):
        try:
            with open(cp, "r", encoding="utf-8") as f:
                data = json.load(f)
        except Exception:
            unreadable += 1
            continue
        st = data.get("structure_type", "")
        if not st.startswith("collector."):
            continue
        suffix = st[len("collector."):]
        col = COLLECTORS.get(suffix)
        if col is None:
            continue
        info = data.get("info", {}) or {}
        try:
            if suffix in ("choose", "role", "picture"):
                items = col(info)
            else:
                items = [gv(info.get("value"))] if args.keep_tags else col(info)
        except Exception:
            continue
        by_type.setdefault(suffix, []).extend(items if isinstance(items, list) else [items])

    content = render_text(by_type)
    with open(args.output, "w", encoding="utf-8-sig") as f:
        f.write(content if content else "")

    print("已输出: {}".format(args.output))
    if unreadable:
        print("无法解析文件: {}".format(unreadable))


if __name__ == "__main__":
    main()

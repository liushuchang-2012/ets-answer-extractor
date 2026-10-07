import json
import os
import webbrowser
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import parse_qs, urlparse

import ets_config
from ets_core import COLLECTORS, render_blocks, render_text

BASE = os.path.dirname(os.path.abspath(__file__))
UI = os.path.join(BASE, "ets-ui")
PORT = 8890
MIME = {
    ".html": "text/html; charset=utf-8",
    ".css": "text/css; charset=utf-8",
    ".js": "application/javascript; charset=utf-8",
    ".png": "image/png",
    ".ico": "image/x-icon",
}

current_root = ets_config.load_root()


def log(msg):
    try:
        print(msg)
    except Exception:
        pass


def papers():
    out = []
    for name in os.listdir(current_root):
        p = os.path.join(current_root, name)
        if not os.path.isdir(p):
            continue
        dirs = [d for d in os.listdir(p) if d.startswith("content_") and os.path.isdir(os.path.join(p, d))]
        if not dirs:
            continue
        counts = {}
        for d in dirs:
            cp = os.path.join(p, d, "content.json")
            if not os.path.isfile(cp):
                continue
            try:
                data = json.load(open(cp, encoding="utf-8"))
            except Exception:
                continue
            st = data.get("structure_type", "")
            if st.startswith("collector."):
                s = st[len("collector."):]
                counts[s] = counts.get(s, 0) + 1
        out.append({"id": name, "dirs": len(dirs), "mtime": os.path.getmtime(p), "counts": counts})
    out.sort(key=lambda r: r["mtime"], reverse=True)
    return out


def paper(pid):
    p = os.path.join(current_root, pid)
    if not os.path.isdir(p):
        return None
    dirs = [d for d in os.listdir(p) if d.startswith("content_") and os.path.isdir(os.path.join(p, d))]
    items = {}
    for d in dirs:
        cp = os.path.join(p, d, "content.json")
        if not os.path.isfile(cp):
            continue
        try:
            data = json.load(open(cp, encoding="utf-8"))
        except Exception:
            continue
        st = data.get("structure_type", "")
        if not st.startswith("collector."):
            continue
        s = st[len("collector."):]
        col = COLLECTORS.get(s)
        if col is None:
            continue
        info = data.get("info", {}) or {}
        try:
            rec = col(info)
        except Exception:
            continue
        items.setdefault(s, []).append(rec if isinstance(rec, list) else [rec])
    counts = {s: len(items[s]) for s in items}
    blocks = render_blocks(items)
    sections = [{"title": t, "text": "\n".join(b)} for t, b in blocks]
    return {"id": pid, "counts": counts, "sections": sections, "rawText": render_text(items)}


class Handler(BaseHTTPRequestHandler):
    def log_message(self, *args):
        pass

    def send_json(self, obj, code=200):
        body = json.dumps(obj, ensure_ascii=False).encode("utf-8")
        self.send_response(code)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def read_body(self):
        n = int(self.headers.get("Content-Length") or 0)
        if n <= 0:
            return {}
        try:
            return json.loads(self.rfile.read(n).decode("utf-8"))
        except Exception:
            return {}

    def do_GET(self):
        u = urlparse(self.path)
        path = u.path
        if path == "/api/papers":
            self.send_json(papers())
            return
        if path == "/api/paper":
            q = parse_qs(u.query)
            pid = (q.get("id") or [""])[0]
            data = paper(pid)
            if data is None:
                self.send_json({"error": "not found"}, 404)
                return
            self.send_json(data)
            return
        if path == "/api/current-dir":
            self.send_json({"root": current_root, "default": ets_config.default_root()})
            return
        if path == "/":
            path = "/index.html"
        fp = os.path.join(UI, path.lstrip("/"))
        if not os.path.isfile(fp) or not os.path.abspath(fp).startswith(os.path.abspath(UI)):
            self.send_error(404)
            return
        ext = os.path.splitext(fp)[1]
        body = open(fp, "rb").read()
        self.send_response(200)
        self.send_header("Content-Type", MIME.get(ext, "application/octet-stream"))
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_POST(self):
        global current_root
        path = urlparse(self.path).path
        if path == "/api/set-dir":
            d = (self.read_body().get("dir") or "").strip()
            try:
                current_root = ets_config.save_root(d)
            except Exception as e:
                self.send_json({"error": str(e)}, 400)
                return
            self.send_json({"root": current_root, "papers": papers()})
            return
        if path == "/api/reset-dir":
            current_root = ets_config.reset_root()
            self.send_json({"root": current_root, "papers": papers()})
            return
        self.send_error(404)


class Server(ThreadingHTTPServer):
    allow_reuse_address = False


if __name__ == "__main__":
    try:
        srv = Server(("127.0.0.1", PORT), Handler)
    except OSError:
        try:
            webbrowser.open("http://127.0.0.1:%d/" % PORT)
        except Exception:
            pass
        raise SystemExit(0)
    log("已启动: http://127.0.0.1:%d/  数据目录: %s" % (PORT, current_root))
    try:
        webbrowser.open("http://127.0.0.1:%d/" % PORT)
    except Exception:
        pass
    try:
        srv.serve_forever()
    except KeyboardInterrupt:
        pass

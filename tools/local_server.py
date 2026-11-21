"""Local dev server: serves frontend/ and routes /api/* to the Lambda handler.

  python tools/local_server.py            # mock AWS (no credentials needed)
  python tools/local_server.py --real     # use real AWS with your local credentials
"""
import argparse
import json
import os
import sys
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
parser = argparse.ArgumentParser()
parser.add_argument("--real", action="store_true")
parser.add_argument("--port", type=int, default=8765)
args = parser.parse_args()
if not args.real:
    os.environ["MOCK_AWS"] = "1"
sys.path.insert(0, os.path.join(ROOT, "backend"))
import app  # noqa: E402


class Handler(SimpleHTTPRequestHandler):
    def __init__(self, *a, **kw):
        super().__init__(*a, directory=os.path.join(ROOT, "frontend"), **kw)

    def _api(self, method):
        length = int(self.headers.get("content-length") or 0)
        body = self.rfile.read(length).decode("utf-8") if length else ""
        event = {"rawPath": self.path.split("?")[0], "requestContext": {"http": {"method": method}}, "body": body}
        res = app.handler(event)
        payload = res["body"].encode("utf-8")
        self.send_response(res["statusCode"])
        for k, v in res["headers"].items():
            self.send_header(k, v)
        self.send_header("content-length", str(len(payload)))
        self.end_headers()
        self.wfile.write(payload)

    def do_GET(self):
        if self.path.startswith("/api/"):
            return self._api("GET")
        return super().do_GET()

    def do_POST(self):
        if self.path.startswith("/api/"):
            return self._api("POST")
        self.send_error(405)

    def log_message(self, fmt, *a):
        if "/api/" in (a[0] if a else ""):
            sys.stderr.write("%s\n" % (fmt % a))


if __name__ == "__main__":
    print(f"KagazCheck on http://localhost:{args.port} ({'REAL AWS' if args.real else 'mock'})")
    ThreadingHTTPServer(("127.0.0.1", args.port), Handler).serve_forever()

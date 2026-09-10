#!/usr/bin/env python3
"""
Local preview that behaves like Netlify.

  /pricing            serves pricing.html
  an unknown path     serves 404.html with a 404 status
  a form POST         is accepted, recorded, and redirected to the form's
                      action, the way Netlify Forms does it

Submissions land in _submissions.log so you can read back exactly what the
form sent. That file is outside site/ and is never published.

    python3 preview.py        then open http://localhost:8899
"""

import datetime
import http.server
import json
import os
import socketserver
import urllib.parse

PORT = 8899
HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.join(HERE, "site")
LOG = os.path.join(HERE, "_submissions.log")

# Matches the netlify-honeypot attribute on every form.
HONEYPOT = "company-website"


class Handler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *a, **kw):
        super().__init__(*a, directory=ROOT, **kw)

    # ------------------------------------------------------------- routing

    def translate_path(self, path):
        real = super().translate_path(path)
        if os.path.isdir(real):
            index = os.path.join(real, "index.html")
            if os.path.exists(index):
                return index
        if not os.path.exists(real) and not os.path.splitext(real)[1]:
            pretty = real.rstrip("/") + ".html"
            if os.path.exists(pretty):
                return pretty
            self._missing = True
            return os.path.join(ROOT, "404.html")
        return real

    def send_response(self, code, message=None):
        if code == 200 and getattr(self, "_missing", False):
            code = 404
        super().send_response(code, message)

    def end_headers(self):
        self.send_header("Cache-Control", "no-store")
        super().end_headers()

    def log_message(self, *a):
        pass

    # --------------------------------------------------------------- forms

    def do_POST(self):
        """Netlify accepts the POST at the form's action and then redirects
        the browser there with a GET. Without this the preview answers 501 and
        the form looks broken when it is not."""
        length = int(self.headers.get("Content-Length") or 0)
        raw = self.rfile.read(length).decode("utf-8", "replace") if length else ""
        fields = {
            k: v[0] for k, v in urllib.parse.parse_qs(raw, keep_blank_values=True).items()
        }

        spam = bool(fields.get(HONEYPOT, "").strip())
        form = fields.get("form-name", "(no form-name)")

        entry = {
            "at": datetime.datetime.now().isoformat(timespec="seconds"),
            "form": form,
            "action": self.path,
            "spam": spam,
            "fields": {k: v for k, v in fields.items()
                       if k not in ("form-name", HONEYPOT) and v.strip()},
        }
        with open(LOG, "a", encoding="utf-8") as f:
            f.write(json.dumps(entry, ensure_ascii=False) + "\n")

        print(f"  form '{form}' received"
              + (" and dropped as spam" if spam else "")
              + f", {len(entry['fields'])} fields, logged to _submissions.log")

        # 303 so the browser follows with GET and a refresh does not repost.
        self.send_response(303)
        self.send_header("Location", self.path)
        self.send_header("Content-Length", "0")
        self.end_headers()


if __name__ == "__main__":
    socketserver.TCPServer.allow_reuse_address = True
    with socketserver.TCPServer(("", PORT), Handler) as httpd:
        print(f"Kinvisit preview on http://localhost:{PORT}")
        print(f"Form submissions are recorded in {os.path.basename(LOG)}")
        httpd.serve_forever()

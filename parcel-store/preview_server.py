"""Local-only integration preview. NOT a production API or authentication layer."""
import json
import os
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlsplit, parse_qs
from tracking import TrackingCache, TrackingError, barcode

ROOT = Path(__file__).resolve().parent
CACHE = TrackingCache()
ALLOWED = {barcode(x) for x in os.getenv("POCHTA_ALLOWED_TRACKS", "").split(",") if x.strip()}

class Handler(BaseHTTPRequestHandler):
    def log_message(self, *args):
        pass  # Avoid recording tracking identifiers in access logs.
    def send_data(self, status, content, media):
        self.send_response(status)
        self.send_header("Content-Type", media)
        self.send_header("Cache-Control", "no-store")
        self.send_header("X-Content-Type-Options", "nosniff")
        self.send_header("Content-Length", str(len(content)))
        self.end_headers()
        self.wfile.write(content)
    def send_json(self, status, data):
        self.send_data(status, json.dumps(data, ensure_ascii=False).encode(), "application/json; charset=utf-8")
    def do_GET(self):
        # Restrict browser origins via Host check; no cross-origin API.
        if self.headers.get("Host") not in ("127.0.0.1:8080", "localhost:8080"):
            return self.send_json(403, {"error": "Local preview only"})
        url = urlsplit(self.path)
        if url.path in ("/", "/index.html"):
            return self.send_data(200, (ROOT / "index.html").read_bytes(), "text/html; charset=utf-8")
        if url.path != "/api/tracking":
            return self.send_json(404, {"error": "Not found"})
        try:
            track = barcode(parse_qs(url.query).get("barcode", [""])[0])
        except ValueError:
            return self.send_json(400, {"error": "Invalid tracking number"})
        if track not in ALLOWED:
            return self.send_json(403, {"error": "Tracking number not configured for local preview"})
        try:
            return self.send_json(200, CACHE.get(track))
        except TrackingError:
            return self.send_json(503, {"error": "Tracking unavailable; check server settings or retry later"})

if __name__ == "__main__":
    print("Local preview: http://127.0.0.1:8080")
    ThreadingHTTPServer(("127.0.0.1", 8080), Handler).serve_forever()

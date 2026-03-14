"""
Vercel serverless function — TaskPulse FastAPI backend.

Uses the handler class pattern (compatible with @vercel/python in builds config)
to serve the FastAPI app. A persistent event loop in a background thread ensures
SQLAlchemy async connections work across multiple requests in a warm container.
"""
import sys
import os
import io
import json
import asyncio
import threading
from http.server import BaseHTTPRequestHandler
from urllib.parse import urlparse, unquote

# Add backend to Python path
_backend_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'backend')
if _backend_dir not in sys.path:
    sys.path.insert(0, _backend_dir)

os.environ.setdefault("ENVIRONMENT", "development")

# ── Persistent event loop ─────────────────────────────────────────────────
# SQLAlchemy's async engine binds connections to the event loop that created
# them. Using asyncio.run() per request creates a NEW loop each time, causing
# "Future attached to a different loop" errors on warm containers.
# Solution: one long-lived loop in a daemon thread, shared across requests.
_loop = asyncio.new_event_loop()
_thread = threading.Thread(target=_loop.run_forever, daemon=True)
_thread.start()

# Import the FastAPI app (runs in the main thread; engine is created here
# but connections will be lazily opened on the persistent loop above)
_app = None
_import_error = None
try:
    from app.main import app as _app
except Exception:
    import traceback
    _import_error = traceback.format_exc()


def _run_asgi_sync(scope, body=b""):
    """Run an ASGI app on the persistent event loop and return (status, headers, body)."""
    response_started = False
    status_code = 500
    response_headers = []
    response_body = io.BytesIO()

    async def receive():
        return {"type": "http.request", "body": body, "more_body": False}

    async def send(message):
        nonlocal response_started, status_code, response_headers
        if message["type"] == "http.response.start":
            response_started = True
            status_code = message["status"]
            response_headers = [
                (k.decode() if isinstance(k, bytes) else k,
                 v.decode() if isinstance(v, bytes) else v)
                for k, v in message.get("headers", [])
            ]
        elif message["type"] == "http.response.body":
            response_body.write(message.get("body", b""))

    async def run():
        await _app(scope, receive, send)

    # Submit the coroutine to the persistent loop and wait for the result.
    # Timeout slightly under Vercel's 30 s limit so we can return an error.
    future = asyncio.run_coroutine_threadsafe(run(), _loop)
    future.result(timeout=28)

    return status_code, response_headers, response_body.getvalue()


class handler(BaseHTTPRequestHandler):
    def _handle(self):
        if _app is None:
            self.send_response(500)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps({
                "error": "Backend import failed",
                "traceback": _import_error,
            }).encode())
            return

        # Read request body
        content_length = int(self.headers.get("Content-Length", 0))
        body = self.rfile.read(content_length) if content_length > 0 else b""

        # Parse URL
        parsed = urlparse(self.path)
        path = unquote(parsed.path)
        query_string = (parsed.query or "").encode()

        # Build ASGI scope
        headers = [
            (k.lower().encode(), v.encode())
            for k, v in self.headers.items()
        ]

        scope = {
            "type": "http",
            "asgi": {"version": "3.0"},
            "http_version": "1.1",
            "method": self.command,
            "path": path,
            "root_path": "",
            "scheme": "https",
            "query_string": query_string,
            "headers": headers,
            "server": ("localhost", 443),
        }

        try:
            status_code, resp_headers, resp_body = _run_asgi_sync(scope, body)

            self.send_response(status_code)
            for key, value in resp_headers:
                if key.lower() not in ("transfer-encoding", "connection"):
                    self.send_header(key, value)
            self.end_headers()
            self.wfile.write(resp_body)
        except Exception as e:
            self.send_response(500)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            import traceback
            self.wfile.write(json.dumps({
                "error": "ASGI invocation failed",
                "detail": str(e),
                "traceback": traceback.format_exc(),
            }).encode())

    def do_GET(self):
        self._handle()

    def do_POST(self):
        self._handle()

    def do_PUT(self):
        self._handle()

    def do_PATCH(self):
        self._handle()

    def do_DELETE(self):
        self._handle()

    def do_OPTIONS(self):
        self._handle()

    def log_message(self, format, *args):
        pass  # Suppress default logging

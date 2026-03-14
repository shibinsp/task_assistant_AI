"""
Vercel serverless function entry point for FastAPI backend.
"""

import sys
import os

# Add backend to Python path
_backend_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'backend')
if _backend_dir not in sys.path:
    sys.path.insert(0, _backend_dir)

# Vercel provides env vars from dashboard — no .env file needed
os.environ.setdefault("ENVIRONMENT", "development")

try:
    from app.main import app
except Exception as exc:
    # Fallback: lightweight diagnostic app (no external deps)
    from http.server import BaseHTTPRequestHandler
    import json
    import traceback

    _tb = traceback.format_exc()

    class handler(BaseHTTPRequestHandler):
        def do_GET(self):
            self.send_response(500)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps({
                "error": "Backend import failed",
                "exception": str(exc),
                "traceback": _tb,
                "python": sys.version,
                "backend_dir": _backend_dir,
                "backend_exists": os.path.isdir(_backend_dir),
                "env_keys": sorted([k for k in os.environ if not k.startswith("_")]),
            }, indent=2).encode())

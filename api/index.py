"""Vercel serverless function — FastAPI backend."""
from http.server import BaseHTTPRequestHandler
import json
import sys
import os


class handler(BaseHTTPRequestHandler):
    """Fallback handler using stdlib only (no pip deps)."""

    def do_GET(self):
        # Try to import the main app and report results
        errors = []
        app_loaded = False
        backend_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'backend')

        try:
            if backend_dir not in sys.path:
                sys.path.insert(0, backend_dir)
            os.environ.setdefault("ENVIRONMENT", "development")

            from app.main import app  # noqa: F401
            app_loaded = True
        except Exception as e:
            import traceback
            errors.append(traceback.format_exc())

        self.send_response(200 if app_loaded else 500)
        self.send_header("Content-Type", "application/json")
        self.end_headers()
        self.wfile.write(json.dumps({
            "status": "ok" if app_loaded else "error",
            "app_loaded": app_loaded,
            "errors": errors,
            "python": sys.version,
            "cwd": os.getcwd(),
            "backend_dir": backend_dir,
            "backend_exists": os.path.isdir(backend_dir),
            "env_keys": sorted([k for k in os.environ if k.startswith(("SUPABASE", "DATABASE", "AI_", "SECRET", "ENV"))]),
        }, indent=2).encode())

    do_POST = do_GET
    do_PUT = do_GET
    do_PATCH = do_GET
    do_DELETE = do_GET
    do_OPTIONS = do_GET

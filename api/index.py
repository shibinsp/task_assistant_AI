"""
Vercel serverless function entry point for FastAPI backend.

Vercel Python runtime detects the `app` variable (ASGI application).
See: https://vercel.com/docs/functions/runtimes/python
"""

import sys
import os

# Add backend to Python path so 'app.*' imports resolve correctly
_backend_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'backend')
if _backend_dir not in sys.path:
    sys.path.insert(0, _backend_dir)

# Vercel provides env vars from dashboard — set development as fallback
# so production validation doesn't block the import
os.environ.setdefault("ENVIRONMENT", "development")

try:
    from app.main import app  # noqa: F401, E402
except Exception:
    # If full app fails, serve a diagnostic FastAPI app
    import traceback
    _error = traceback.format_exc()

    from fastapi import FastAPI
    app = FastAPI(title="TaskPulse API - Error")

    @app.get("/{path:path}")
    async def error_handler(path: str = ""):
        return {
            "error": "Backend failed to start",
            "traceback": _error,
            "python": sys.version,
            "backend_dir_exists": os.path.isdir(_backend_dir),
            "cwd": os.getcwd(),
        }

"""
Vercel serverless function entry point for FastAPI.
This wraps the FastAPI app so Vercel's Python runtime can serve it.
"""

import sys
import os
import traceback

# Add backend to Python path so 'app.*' imports resolve
_backend_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'backend')
sys.path.insert(0, _backend_dir)

# Vercel sets env vars from dashboard — no .env file needed.
# Override pydantic-settings env_file so it doesn't fail on missing .env
os.environ.setdefault("ENVIRONMENT", "production")

try:
    from app.main import app  # noqa: E402
except Exception as exc:
    # If the full app fails to import, serve a diagnostic app
    from fastapi import FastAPI
    app = FastAPI(title="TaskPulse API — Import Error")

    _error_detail = traceback.format_exc()

    @app.get("/api/{path:path}")
    @app.get("/api/v1")
    async def _import_error():
        return {
            "error": "Backend failed to import",
            "detail": str(exc),
            "traceback": _error_detail,
            "python_version": sys.version,
            "sys_path": sys.path[:5],
            "backend_dir": _backend_dir,
            "backend_exists": os.path.isdir(_backend_dir),
            "env_keys": [k for k in os.environ if k.startswith(("SUPABASE", "DATABASE", "AI_", "SECRET"))],
        }

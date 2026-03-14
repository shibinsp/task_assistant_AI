"""Vercel serverless function — FastAPI backend."""
import sys
import os
import traceback

# Pre-import FastAPI before anything else
from fastapi import FastAPI
from fastapi.responses import JSONResponse

# Add backend to Python path
_backend_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'backend')
if _backend_dir not in sys.path:
    sys.path.insert(0, _backend_dir)

# Don't override ENVIRONMENT if Vercel already set it
os.environ.setdefault("ENVIRONMENT", "development")

_import_error = None
_main_app = None

try:
    from app.main import app as _main_app  # noqa: E402
except Exception:
    _import_error = traceback.format_exc()

if _main_app is not None:
    app = _main_app
else:
    app = FastAPI(title="TaskPulse API - Import Error")

    @app.api_route("/{path:path}", methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"])
    async def error_handler(path: str = ""):
        return JSONResponse(
            status_code=500,
            content={
                "error": "Backend failed to import",
                "traceback": _import_error or "Unknown error",
                "python": sys.version,
                "cwd": os.getcwd(),
                "backend_dir_exists": os.path.isdir(_backend_dir),
                "env_vars": {
                    k: ("***" if "KEY" in k or "SECRET" in k or "PASSWORD" in k else v[:50])
                    for k, v in os.environ.items()
                    if k.startswith(("SUPABASE", "DATABASE", "AI_", "SECRET", "ENVIRONMENT"))
                },
            },
        )

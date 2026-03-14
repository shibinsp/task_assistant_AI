"""
Vercel serverless function — FastAPI backend (ASGI).

Vercel Python runtime detects the `app` variable as an ASGI application.
"""
import sys
import os

# Add backend to Python path
_backend_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'backend')
if _backend_dir not in sys.path:
    sys.path.insert(0, _backend_dir)

os.environ.setdefault("ENVIRONMENT", "development")

from app.main import app  # noqa: E402, F401

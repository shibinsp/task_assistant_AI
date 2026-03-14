"""
Vercel serverless function entry point for FastAPI.
This wraps the FastAPI app so Vercel's Python runtime can serve it.
"""

import sys
import os

# Add backend to Python path so 'app.*' imports resolve
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'backend'))

# Set env file path for pydantic-settings (Vercel runs from project root)
os.environ.setdefault("ENV_FILE", os.path.join(os.path.dirname(__file__), '..', 'backend', '.env'))

from app.main import app  # noqa: E402

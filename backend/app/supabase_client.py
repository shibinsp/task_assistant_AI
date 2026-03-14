"""
Supabase client singleton for server-side operations.
Uses SERVICE_ROLE_KEY to bypass Row-Level Security.
"""

from functools import lru_cache
from supabase import create_client, Client
from app.config import settings


@lru_cache()
def get_supabase_client() -> Client:
    """Get cached Supabase client instance using service role key."""
    if not settings.SUPABASE_URL or not settings.SUPABASE_SERVICE_ROLE_KEY:
        raise RuntimeError(
            "SUPABASE_URL and SUPABASE_SERVICE_ROLE_KEY must be set. "
            "Check your .env file."
        )
    return create_client(
        settings.SUPABASE_URL,
        settings.SUPABASE_SERVICE_ROLE_KEY
    )


def get_supabase_anon_client() -> Client:
    """Get Supabase client with anon key (respects RLS)."""
    if not settings.SUPABASE_URL or not settings.SUPABASE_ANON_KEY:
        raise RuntimeError(
            "SUPABASE_URL and SUPABASE_ANON_KEY must be set. "
            "Check your .env file."
        )
    return create_client(
        settings.SUPABASE_URL,
        settings.SUPABASE_ANON_KEY
    )

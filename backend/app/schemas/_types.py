"""
Shared Pydantic type utilities for TaskPulse schemas.

This module is imported early and must NOT import from app.schemas
to avoid circular imports.
"""

from typing import Annotated
from uuid import UUID as _PyUUID

from pydantic import BeforeValidator


def _uuid_to_str(v):
    """Convert UUID objects to strings for Pydantic schema compatibility."""
    return str(v) if isinstance(v, _PyUUID) else v


# Use this instead of `str` for any field that may receive a UUID object from the ORM.
# PostgreSQL returns native UUID objects via asyncpg/PG_UUID(as_uuid=True),
# but API schemas define IDs as strings for JSON serialization.
StrUUID = Annotated[str, BeforeValidator(_uuid_to_str)]

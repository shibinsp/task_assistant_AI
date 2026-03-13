"""
TaskPulse - AI Assistant - Security Utilities
JWT token handling, password hashing, and authentication helpers

Supabase Auth is the primary authentication provider.
Legacy local JWT functions are kept for migration backward compatibility.
"""

from datetime import datetime, timedelta, timezone
from typing import Optional, Any
import hashlib
import secrets
import logging

import bcrypt
from jose import JWTError, jwt

from app.config import settings

logger = logging.getLogger(__name__)


# ==================== Supabase Auth ====================

def verify_supabase_token(token: str) -> Optional[dict]:
    """
    Verify a Supabase-issued JWT token.

    Decodes the token using the project's SUPABASE_JWT_SECRET and validates
    the audience claim (must be "authenticated").

    Args:
        token: Supabase JWT access token string

    Returns:
        Decoded payload dict on success containing keys such as:
            sub             - Supabase user UUID
            email           - user email
            role            - Supabase role (e.g. "authenticated")
            aud             - audience ("authenticated")
            exp, iat        - timestamps
            app_metadata    - Supabase app metadata
            user_metadata   - Supabase user metadata
        None on any verification failure.
    """
    try:
        payload = jwt.decode(
            token,
            settings.SUPABASE_JWT_SECRET,
            algorithms=["HS256"],
            audience="authenticated",
        )
        return payload
    except JWTError as exc:
        logger.debug("Supabase token verification failed: %s", exc)
        return None


# ==================== Token Hash Utilities ====================

def hash_token(token: str) -> str:
    """
    Create a hash of a token for storage.

    Args:
        token: Token string to hash

    Returns:
        SHA-256 hash of the token
    """
    return hashlib.sha256(token.encode()).hexdigest()


# ==================== API Key Utilities ====================

def generate_api_key() -> tuple[str, str]:
    """
    Generate a new API key.

    Returns:
        Tuple of (api_key, api_key_hash)
    """
    # Generate a secure random key
    api_key = f"tp_{secrets.token_urlsafe(32)}"
    api_key_hash = hashlib.sha256(api_key.encode()).hexdigest()

    return api_key, api_key_hash


def verify_api_key(api_key: str, stored_hash: str) -> bool:
    """
    Verify an API key against its stored hash.

    Args:
        api_key: API key to verify
        stored_hash: Stored hash to verify against

    Returns:
        True if key matches, False otherwise
    """
    key_hash = hashlib.sha256(api_key.encode()).hexdigest()
    return secrets.compare_digest(key_hash, stored_hash)


# ==================== Token Payload Helpers ====================

class TokenPayload:
    """
    Helper class to work with token payloads.

    Handles both legacy local JWTs and Supabase JWTs:
    - Legacy: sub=local user ID, org_id, role, type="access"/"refresh"
    - Supabase: sub=supabase auth UUID, email, role="authenticated",
      aud="authenticated", app_metadata, user_metadata
    """

    def __init__(self, payload: dict):
        # sub is either the local user ID (legacy) or the Supabase auth UUID
        self.user_id: str = payload.get("sub", "")
        self.org_id: str = payload.get("org_id", "")
        self.role: str = payload.get("role", "")
        self.email: str = payload.get("email", "")
        self.token_type: str = payload.get("type", "access")

        # Supabase-specific fields
        self.aud: str = payload.get("aud", "")
        self.app_metadata: dict = payload.get("app_metadata", {})
        self.user_metadata: dict = payload.get("user_metadata", {})

        self.issued_at: Optional[datetime] = None
        self.expires_at: Optional[datetime] = None

        # Parse timestamps
        if "iat" in payload:
            self.issued_at = datetime.fromtimestamp(
                payload["iat"],
                tz=timezone.utc
            )
        if "exp" in payload:
            self.expires_at = datetime.fromtimestamp(
                payload["exp"],
                tz=timezone.utc
            )

    @property
    def is_supabase_token(self) -> bool:
        """Check if this payload originated from a Supabase JWT."""
        return self.aud == "authenticated"

    @property
    def is_expired(self) -> bool:
        """Check if token is expired."""
        if self.expires_at is None:
            return True
        return datetime.now(timezone.utc) > self.expires_at

    def to_dict(self) -> dict:
        """Convert to dictionary."""
        return {
            "user_id": self.user_id,
            "org_id": self.org_id,
            "role": self.role,
            "email": self.email,
            "token_type": self.token_type,
        }


# ============================================================
# DEPRECATED: Legacy local auth functions
# Kept only for the migration script and backward compatibility.
# All new authentication flows should use Supabase Auth.
# ============================================================

# DEPRECATED: Used only for migration
def hash_password(password: str) -> str:
    """
    Hash a password using bcrypt.

    Args:
        password: Plain text password

    Returns:
        Hashed password string
    """
    password_bytes = password.encode('utf-8')
    salt = bcrypt.gensalt()
    hashed = bcrypt.hashpw(password_bytes, salt)
    return hashed.decode('utf-8')


# DEPRECATED: Used only for migration and tests
def create_access_token(
    data: dict,
    expires_delta: Optional[timedelta] = None
) -> str:
    """
    Create a JWT access token.

    Args:
        data: Data to encode in the token
        expires_delta: Optional custom expiration time

    Returns:
        Encoded JWT token string
    """
    to_encode = data.copy()

    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(
            minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES
        )

    to_encode.update({
        "exp": expire,
        "iat": datetime.now(timezone.utc),
        "type": "access"
    })

    encoded_jwt = jwt.encode(
        to_encode,
        settings.SECRET_KEY,
        algorithm=settings.ALGORITHM
    )

    return encoded_jwt


# DEPRECATED: Used only for migration and tests
def decode_token(token: str) -> Optional[dict]:
    """
    Decode and validate a JWT token.

    Args:
        token: JWT token string

    Returns:
        Decoded token payload or None if invalid
    """
    try:
        payload = jwt.decode(
            token,
            settings.SECRET_KEY,
            algorithms=[settings.ALGORITHM]
        )
        return payload
    except JWTError:
        return None


# DEPRECATED: Used only for migration
def verify_token(token: str, token_type: str = "access") -> Optional[dict]:
    """
    Verify a token and check its type.

    Args:
        token: JWT token string
        token_type: Expected token type ("access" or "refresh")

    Returns:
        Decoded token payload or None if invalid
    """
    payload = decode_token(token)

    if payload is None:
        return None

    if payload.get("type") != token_type:
        return None

    return payload

"""
TaskPulse - AI Assistant - Security Utilities
JWT token handling, password hashing, and authentication helpers
"""

from datetime import datetime, timedelta, timezone
from typing import Optional, Any
import hashlib
import secrets

import bcrypt
from jose import JWTError, jwt

from app.config import settings


# ==================== Password Utilities ====================

def hash_password(password: str) -> str:
    """
    Hash a password using bcrypt.

    Args:
        password: Plain text password

    Returns:
        Hashed password string
    """
    # bcrypt requires bytes, encode the password
    password_bytes = password.encode('utf-8')
    # Generate salt and hash
    salt = bcrypt.gensalt()
    hashed = bcrypt.hashpw(password_bytes, salt)
    return hashed.decode('utf-8')


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Verify a password against its hash.

    Args:
        plain_password: Plain text password to verify
        hashed_password: Stored hash to verify against

    Returns:
        True if password matches, False otherwise
    """
    try:
        password_bytes = plain_password.encode('utf-8')
        hashed_bytes = hashed_password.encode('utf-8')
        return bcrypt.checkpw(password_bytes, hashed_bytes)
    except Exception:
        return False


# ==================== Token Utilities ====================

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


def create_refresh_token(
    data: dict,
    expires_delta: Optional[timedelta] = None
) -> str:
    """
    Create a JWT refresh token.

    Args:
        data: Data to encode in the token
        expires_delta: Optional custom expiration time

    Returns:
        Encoded JWT refresh token string
    """
    to_encode = data.copy()

    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(
            days=settings.REFRESH_TOKEN_EXPIRE_DAYS
        )

    to_encode.update({
        "exp": expire,
        "iat": datetime.now(timezone.utc),
        "type": "refresh"
    })

    encoded_jwt = jwt.encode(
        to_encode,
        settings.SECRET_KEY,
        algorithm=settings.ALGORITHM
    )

    return encoded_jwt


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


# ==================== Password Reset Utilities ====================

def generate_password_reset_token(email: str) -> str:
    """
    Generate a password reset token.

    Args:
        email: User's email address

    Returns:
        Password reset JWT token
    """
    expires = datetime.now(timezone.utc) + timedelta(hours=1)

    return jwt.encode(
        {
            "sub": email,
            "exp": expires,
            "type": "password_reset"
        },
        settings.SECRET_KEY,
        algorithm=settings.ALGORITHM
    )


def verify_password_reset_token(token: str) -> Optional[str]:
    """
    Verify a password reset token and extract email.

    Args:
        token: Password reset token

    Returns:
        Email address or None if invalid
    """
    try:
        payload = jwt.decode(
            token,
            settings.SECRET_KEY,
            algorithms=[settings.ALGORITHM]
        )

        if payload.get("type") != "password_reset":
            return None

        return payload.get("sub")
    except JWTError:
        return None


# ==================== Email Verification Utilities ====================

def generate_email_verification_token(email: str) -> str:
    """
    Generate an email verification token.

    Args:
        email: Email address to verify

    Returns:
        Email verification JWT token
    """
    expires = datetime.now(timezone.utc) + timedelta(days=7)

    return jwt.encode(
        {
            "sub": email,
            "exp": expires,
            "type": "email_verification"
        },
        settings.SECRET_KEY,
        algorithm=settings.ALGORITHM
    )


def verify_email_verification_token(token: str) -> Optional[str]:
    """
    Verify an email verification token and extract email.

    Args:
        token: Email verification token

    Returns:
        Email address or None if invalid
    """
    try:
        payload = jwt.decode(
            token,
            settings.SECRET_KEY,
            algorithms=[settings.ALGORITHM]
        )

        if payload.get("type") != "email_verification":
            return None

        return payload.get("sub")
    except JWTError:
        return None


# ==================== Token Payload Helpers ====================

class TokenPayload:
    """Helper class to work with token payloads."""

    def __init__(self, payload: dict):
        self.user_id: str = payload.get("sub", "")
        self.org_id: str = payload.get("org_id", "")
        self.role: str = payload.get("role", "")
        self.email: str = payload.get("email", "")
        self.token_type: str = payload.get("type", "access")
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
            "token_type": self.token_type
        }

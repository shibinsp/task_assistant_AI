"""
TaskPulse - AI Assistant - Helper Functions
Common utility functions used throughout the application
"""

import re
import uuid
from datetime import datetime, timezone
from typing import Optional


def generate_uuid() -> str:
    """Generate a new UUID4 string."""
    return str(uuid.uuid4())


def get_utc_now() -> datetime:
    """Get current UTC datetime."""
    return datetime.now(timezone.utc)


def slugify(text: str, max_length: int = 100) -> str:
    """
    Convert text to URL-safe slug.

    Args:
        text: The text to slugify
        max_length: Maximum length of the slug

    Returns:
        URL-safe slug string
    """
    # Convert to lowercase
    slug = text.lower()

    # Replace spaces and underscores with hyphens
    slug = re.sub(r'[\s_]+', '-', slug)

    # Remove non-alphanumeric characters except hyphens
    slug = re.sub(r'[^a-z0-9-]', '', slug)

    # Remove multiple consecutive hyphens
    slug = re.sub(r'-+', '-', slug)

    # Remove leading/trailing hyphens
    slug = slug.strip('-')

    # Truncate to max length
    if len(slug) > max_length:
        slug = slug[:max_length].rstrip('-')

    return slug


def truncate_string(text: str, max_length: int, suffix: str = "...") -> str:
    """
    Truncate string to max length with suffix.

    Args:
        text: The text to truncate
        max_length: Maximum length including suffix
        suffix: Suffix to add when truncated

    Returns:
        Truncated string
    """
    if len(text) <= max_length:
        return text

    truncate_at = max_length - len(suffix)
    if truncate_at <= 0:
        return text[:max_length]

    return text[:truncate_at] + suffix


def calculate_percentage(value: float, total: float, decimal_places: int = 2) -> float:
    """
    Calculate percentage safely (handles division by zero).

    Args:
        value: The numerator value
        total: The denominator (total) value
        decimal_places: Number of decimal places to round to

    Returns:
        Percentage value or 0 if total is 0
    """
    if total == 0:
        return 0.0
    return round((value / total) * 100, decimal_places)


def format_duration(seconds: float) -> str:
    """
    Format duration in seconds to human-readable string.

    Args:
        seconds: Duration in seconds

    Returns:
        Human-readable duration string
    """
    if seconds < 60:
        return f"{seconds:.1f}s"
    elif seconds < 3600:
        minutes = seconds / 60
        return f"{minutes:.1f}m"
    elif seconds < 86400:
        hours = seconds / 3600
        return f"{hours:.1f}h"
    else:
        days = seconds / 86400
        return f"{days:.1f}d"


def format_bytes(size_bytes: int) -> str:
    """
    Format bytes to human-readable string.

    Args:
        size_bytes: Size in bytes

    Returns:
        Human-readable size string
    """
    for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
        if size_bytes < 1024:
            return f"{size_bytes:.1f} {unit}"
        size_bytes /= 1024
    return f"{size_bytes:.1f} PB"


def mask_email(email: str) -> str:
    """
    Mask email address for privacy.

    Args:
        email: Email address to mask

    Returns:
        Masked email address
    """
    if "@" not in email:
        return email

    local, domain = email.split("@", 1)

    if len(local) <= 2:
        masked_local = "*" * len(local)
    else:
        masked_local = local[0] + "*" * (len(local) - 2) + local[-1]

    return f"{masked_local}@{domain}"


def parse_bool(value: Optional[str]) -> bool:
    """
    Parse string to boolean.

    Args:
        value: String value to parse

    Returns:
        Boolean value
    """
    if value is None:
        return False
    return value.lower() in ('true', '1', 'yes', 'on')


def safe_int(value: Optional[str], default: int = 0) -> int:
    """
    Safely parse string to integer.

    Args:
        value: String value to parse
        default: Default value if parsing fails

    Returns:
        Integer value
    """
    if value is None:
        return default
    try:
        return int(value)
    except (ValueError, TypeError):
        return default


def safe_float(value: Optional[str], default: float = 0.0) -> float:
    """
    Safely parse string to float.

    Args:
        value: String value to parse
        default: Default value if parsing fails

    Returns:
        Float value
    """
    if value is None:
        return default
    try:
        return float(value)
    except (ValueError, TypeError):
        return default


def deep_merge(base: dict, override: dict) -> dict:
    """
    Deep merge two dictionaries.

    Args:
        base: Base dictionary
        override: Dictionary with override values

    Returns:
        Merged dictionary
    """
    result = base.copy()

    for key, value in override.items():
        if key in result and isinstance(result[key], dict) and isinstance(value, dict):
            result[key] = deep_merge(result[key], value)
        else:
            result[key] = value

    return result


def chunks(lst: list, n: int):
    """
    Yield successive n-sized chunks from list.

    Args:
        lst: List to chunk
        n: Chunk size

    Yields:
        List chunks
    """
    for i in range(0, len(lst), n):
        yield lst[i:i + n]

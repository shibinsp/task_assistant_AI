"""
TaskPulse - AI Assistant - Validators
Custom validation functions for data integrity
"""

import re
from typing import Optional
from datetime import datetime


def validate_email(email: str) -> bool:
    """
    Validate email format.

    Args:
        email: Email address to validate

    Returns:
        True if valid, False otherwise
    """
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return bool(re.match(pattern, email))


def validate_password_strength(password: str) -> dict:
    """
    Validate password strength and return detailed results.

    Requirements:
    - At least 8 characters
    - At least one uppercase letter
    - At least one lowercase letter
    - At least one digit
    - At least one special character

    Args:
        password: Password to validate

    Returns:
        Dictionary with validation results
    """
    results = {
        "is_valid": True,
        "errors": [],
        "strength": "weak"
    }

    if len(password) < 8:
        results["is_valid"] = False
        results["errors"].append("Password must be at least 8 characters long")

    if not re.search(r'[A-Z]', password):
        results["is_valid"] = False
        results["errors"].append("Password must contain at least one uppercase letter")

    if not re.search(r'[a-z]', password):
        results["is_valid"] = False
        results["errors"].append("Password must contain at least one lowercase letter")

    if not re.search(r'\d', password):
        results["is_valid"] = False
        results["errors"].append("Password must contain at least one digit")

    if not re.search(r'[!@#$%^&*()\,.\?":{}|<>]', password):
        results["is_valid"] = False
        results["errors"].append("Password must contain at least one special character")

    # Calculate strength
    if results["is_valid"]:
        score = 0
        if len(password) >= 12:
            score += 1
        if len(password) >= 16:
            score += 1
        if re.search(r'[!@#$%^&*()\,.\?":{}|<>].*[!@#$%^&*()\,.\?":{}|<>]', password):
            score += 1

        if score >= 2:
            results["strength"] = "strong"
        elif score >= 1:
            results["strength"] = "medium"

    return results


def validate_uuid(value: str) -> bool:
    """
    Validate UUID format.

    Args:
        value: String to validate as UUID

    Returns:
        True if valid UUID, False otherwise
    """
    pattern = r'^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$'
    return bool(re.match(pattern, value.lower()))


def validate_slug(slug: str, min_length: int = 3, max_length: int = 100) -> bool:
    """
    Validate slug format.

    Args:
        slug: Slug to validate
        min_length: Minimum length
        max_length: Maximum length

    Returns:
        True if valid slug, False otherwise
    """
    if len(slug) < min_length or len(slug) > max_length:
        return False

    pattern = r'^[a-z0-9]+(-[a-z0-9]+)*$'
    return bool(re.match(pattern, slug))


def validate_url(url: str) -> bool:
    """
    Validate URL format.

    Args:
        url: URL to validate

    Returns:
        True if valid URL, False otherwise
    """
    pattern = r'^https?://[^\s/$.?#].[^\s]*$'
    return bool(re.match(pattern, url, re.IGNORECASE))


def validate_phone(phone: str) -> bool:
    """
    Validate phone number format (international).

    Args:
        phone: Phone number to validate

    Returns:
        True if valid phone, False otherwise
    """
    # Remove common formatting characters
    cleaned = re.sub(r'[\s\-\(\)\.]', '', phone)

    # Check for valid international format
    pattern = r'^\+?[1-9]\d{6,14}$'
    return bool(re.match(pattern, cleaned))


def validate_date_range(
    start_date: datetime,
    end_date: datetime,
    allow_same: bool = True
) -> bool:
    """
    Validate that start date is before or equal to end date.

    Args:
        start_date: Start date
        end_date: End date
        allow_same: Whether to allow same date

    Returns:
        True if valid range, False otherwise
    """
    if allow_same:
        return start_date <= end_date
    return start_date < end_date


def validate_priority(priority: str) -> bool:
    """
    Validate task priority value.

    Args:
        priority: Priority value to validate

    Returns:
        True if valid priority, False otherwise
    """
    valid_priorities = {'critical', 'high', 'medium', 'low'}
    return priority.lower() in valid_priorities


def validate_task_status(status: str) -> bool:
    """
    Validate task status value.

    Args:
        status: Status value to validate

    Returns:
        True if valid status, False otherwise
    """
    valid_statuses = {'todo', 'in_progress', 'blocked', 'review', 'done', 'archived'}
    return status.lower() in valid_statuses


def validate_user_role(role: str) -> bool:
    """
    Validate user role value.

    Args:
        role: Role value to validate

    Returns:
        True if valid role, False otherwise
    """
    valid_roles = {
        'super_admin', 'org_admin', 'manager',
        'team_lead', 'employee', 'viewer'
    }
    return role.lower() in valid_roles


def validate_skill_level(level: int) -> bool:
    """
    Validate skill level (1-10).

    Args:
        level: Skill level to validate

    Returns:
        True if valid level, False otherwise
    """
    return 1 <= level <= 10


def validate_confidence_score(score: float) -> bool:
    """
    Validate confidence/risk score (0.00-1.00).

    Args:
        score: Score to validate

    Returns:
        True if valid score, False otherwise
    """
    return 0.0 <= score <= 1.0


def sanitize_string(value: str, max_length: Optional[int] = None) -> str:
    """
    Sanitize string by removing potentially dangerous characters.

    Args:
        value: String to sanitize
        max_length: Maximum length to truncate to

    Returns:
        Sanitized string
    """
    # Remove null bytes and control characters
    sanitized = re.sub(r'[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]', '', value)

    # Truncate if max_length specified
    if max_length and len(sanitized) > max_length:
        sanitized = sanitized[:max_length]

    return sanitized.strip()


def validate_json_path(path: str) -> bool:
    """
    Validate JSON path format.

    Args:
        path: JSON path to validate

    Returns:
        True if valid JSON path, False otherwise
    """
    # Simple validation for common JSON path patterns
    pattern = r'^(\$|@)?(\.[\w-]+|\[\d+\]|\[\*\]|\[\'[\w-]+\'\])*$'
    return bool(re.match(pattern, path))

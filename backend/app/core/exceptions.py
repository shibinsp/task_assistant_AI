"""
TaskPulse - AI Assistant - Custom Exceptions
Centralized exception definitions for consistent error handling
"""

from typing import Any, Optional


class TaskPulseException(Exception):
    """Base exception for all TaskPulse errors."""

    def __init__(
        self,
        message: str = "An error occurred",
        status_code: int = 500,
        error_code: str = "INTERNAL_ERROR",
        details: Optional[dict[str, Any]] = None
    ):
        self.message = message
        self.status_code = status_code
        self.error_code = error_code
        self.details = details or {}
        super().__init__(self.message)

    def to_dict(self) -> dict[str, Any]:
        """Convert exception to dictionary for JSON response."""
        return {
            "error": {
                "code": self.error_code,
                "message": self.message,
                "details": self.details
            }
        }


# ==================== Authentication Exceptions ====================

class AuthenticationException(TaskPulseException):
    """Base authentication exception."""

    def __init__(
        self,
        message: str = "Authentication failed",
        error_code: str = "AUTH_ERROR",
        details: Optional[dict[str, Any]] = None
    ):
        super().__init__(message, 401, error_code, details)


class InvalidCredentialsException(AuthenticationException):
    """Invalid login credentials."""

    def __init__(self, message: str = "Invalid email or password"):
        super().__init__(message, "INVALID_CREDENTIALS")


class TokenExpiredException(AuthenticationException):
    """JWT token has expired."""

    def __init__(self, message: str = "Token has expired"):
        super().__init__(message, "TOKEN_EXPIRED")


class InvalidTokenException(AuthenticationException):
    """JWT token is invalid."""

    def __init__(self, message: str = "Invalid token"):
        super().__init__(message, "INVALID_TOKEN")


class InactiveUserException(AuthenticationException):
    """User account is inactive."""

    def __init__(self, message: str = "User account is inactive"):
        super().__init__(message, "INACTIVE_USER")


class AccountLockedException(AuthenticationException):
    """User account is locked due to too many failed login attempts."""

    def __init__(self, message: str = "Account temporarily locked due to too many failed login attempts. Please try again later."):
        super().__init__(message, "ACCOUNT_LOCKED")


# ==================== Authorization Exceptions ====================

class AuthorizationException(TaskPulseException):
    """Base authorization exception."""

    def __init__(
        self,
        message: str = "Access denied",
        error_code: str = "ACCESS_DENIED",
        details: Optional[dict[str, Any]] = None
    ):
        super().__init__(message, 403, error_code, details)


class InsufficientPermissionsException(AuthorizationException):
    """User lacks required permissions."""

    def __init__(
        self,
        message: str = "Insufficient permissions",
        required_permission: Optional[str] = None
    ):
        details = {}
        if required_permission:
            details["required_permission"] = required_permission
        super().__init__(message, "INSUFFICIENT_PERMISSIONS", details)


class OrganizationAccessDeniedException(AuthorizationException):
    """User doesn't have access to the organization."""

    def __init__(self, message: str = "You don't have access to this organization"):
        super().__init__(message, "ORG_ACCESS_DENIED")


class ForbiddenException(AuthorizationException):
    """Generic forbidden access exception."""

    def __init__(self, message: str = "Access forbidden"):
        super().__init__(message, "FORBIDDEN")


# ==================== Resource Exceptions ====================

class ResourceException(TaskPulseException):
    """Base resource exception."""

    def __init__(
        self,
        message: str = "Resource error",
        status_code: int = 400,
        error_code: str = "RESOURCE_ERROR",
        details: Optional[dict[str, Any]] = None
    ):
        super().__init__(message, status_code, error_code, details)


class NotFoundException(ResourceException):
    """Resource not found."""

    def __init__(
        self,
        resource: str = "Resource",
        resource_id: Optional[str] = None
    ):
        message = f"{resource} not found"
        details = {}
        if resource_id:
            details["resource_id"] = resource_id
        super().__init__(message, 404, "NOT_FOUND", details)


class AlreadyExistsException(ResourceException):
    """Resource already exists."""

    def __init__(
        self,
        resource: str = "Resource",
        field: Optional[str] = None,
        value: Optional[str] = None
    ):
        message = f"{resource} already exists"
        details = {}
        if field and value:
            message = f"{resource} with {field} '{value}' already exists"
            details["field"] = field
            details["value"] = value
        super().__init__(message, 409, "ALREADY_EXISTS", details)


class ValidationException(ResourceException):
    """Validation error."""

    def __init__(
        self,
        message: str = "Validation failed",
        errors: Optional[list[dict[str, Any]]] = None
    ):
        details = {"validation_errors": errors or []}
        super().__init__(message, 422, "VALIDATION_ERROR", details)


# ==================== Business Logic Exceptions ====================

class BusinessException(TaskPulseException):
    """Base business logic exception."""

    def __init__(
        self,
        message: str = "Business rule violation",
        error_code: str = "BUSINESS_ERROR",
        details: Optional[dict[str, Any]] = None
    ):
        super().__init__(message, 400, error_code, details)


class TaskStatusException(BusinessException):
    """Invalid task status transition."""

    def __init__(
        self,
        current_status: str,
        target_status: str,
        message: Optional[str] = None
    ):
        msg = message or f"Cannot transition task from '{current_status}' to '{target_status}'"
        details = {
            "current_status": current_status,
            "target_status": target_status
        }
        super().__init__(msg, "INVALID_STATUS_TRANSITION", details)


class CheckInException(BusinessException):
    """Check-in related error."""

    def __init__(
        self,
        message: str = "Check-in error",
        error_code: str = "CHECKIN_ERROR",
        details: Optional[dict[str, Any]] = None
    ):
        super().__init__(message, error_code, details)


class ConsentRequiredException(BusinessException):
    """User consent is required."""

    def __init__(self, feature: str = "this feature"):
        message = f"User consent is required for {feature}"
        super().__init__(message, "CONSENT_REQUIRED", {"feature": feature})


# ==================== AI/ML Exceptions ====================

class AIException(TaskPulseException):
    """Base AI/ML exception."""

    def __init__(
        self,
        message: str = "AI service error",
        error_code: str = "AI_ERROR",
        details: Optional[dict[str, Any]] = None
    ):
        super().__init__(message, 503, error_code, details)


class AIProviderException(AIException):
    """AI provider (OpenAI/Claude) error."""

    def __init__(
        self,
        provider: str,
        message: str = "AI provider error",
        original_error: Optional[str] = None
    ):
        details = {"provider": provider}
        if original_error:
            details["original_error"] = original_error
        super().__init__(message, "AI_PROVIDER_ERROR", details)


class AIRateLimitException(AIException):
    """AI rate limit exceeded."""

    def __init__(self, retry_after: Optional[int] = None):
        message = "AI rate limit exceeded"
        details = {}
        if retry_after:
            details["retry_after_seconds"] = retry_after
        super().__init__(message, "AI_RATE_LIMIT", details)


# ==================== Rate Limiting Exceptions ====================

class RateLimitException(TaskPulseException):
    """Rate limit exceeded."""

    def __init__(
        self,
        message: str = "Rate limit exceeded",
        retry_after: Optional[int] = None
    ):
        details = {}
        if retry_after:
            details["retry_after_seconds"] = retry_after
        super().__init__(message, 429, "RATE_LIMIT_EXCEEDED", details)


# ==================== Integration Exceptions ====================

class IntegrationException(TaskPulseException):
    """External integration error."""

    def __init__(
        self,
        integration: str,
        message: str = "Integration error",
        error_code: str = "INTEGRATION_ERROR",
        details: Optional[dict[str, Any]] = None
    ):
        full_details = {"integration": integration, **(details or {})}
        super().__init__(message, 502, error_code, full_details)

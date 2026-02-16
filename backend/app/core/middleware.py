"""
TaskPulse - AI Assistant - Middleware
Custom middleware for request/response processing

Security features:
- SEC-002: In-memory rate limiting per IP for auth and AI endpoints
- SEC-006: CSRF protection via double-submit cookie pattern
"""

import hashlib
import hmac
import logging
import secrets
import time
from collections import defaultdict
from typing import Callable, Dict, List, Tuple

from fastapi import FastAPI, Request, Response
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
from uuid import uuid4

from app.config import settings
from app.core.exceptions import TaskPulseException

logger = logging.getLogger(__name__)


# ==================== SEC-002: Rate Limiting ====================

class RateLimitStore:
    """
    In-memory sliding-window rate limiter keyed by client IP.
    Stores timestamps of recent requests and evicts stale entries.
    For production at scale, replace with Redis-backed implementation.
    """

    def __init__(self):
        # {key: [timestamps]}
        self._requests: Dict[str, List[float]] = defaultdict(list)

    def is_rate_limited(self, key: str, max_requests: int, window_seconds: int) -> Tuple[bool, int]:
        """
        Check if a key has exceeded the rate limit.

        Returns:
            Tuple of (is_limited, remaining_requests)
        """
        now = time.time()
        cutoff = now - window_seconds

        # Evict stale timestamps
        timestamps = self._requests[key]
        self._requests[key] = [t for t in timestamps if t > cutoff]

        current_count = len(self._requests[key])

        if current_count >= max_requests:
            return True, 0

        # Record this request
        self._requests[key].append(now)
        return False, max_requests - current_count - 1

    def cleanup(self):
        """Remove keys with no recent timestamps (housekeeping)."""
        now = time.time()
        empty_keys = []
        for key, timestamps in self._requests.items():
            self._requests[key] = [t for t in timestamps if t > now - 300]
            if not self._requests[key]:
                empty_keys.append(key)
        for key in empty_keys:
            del self._requests[key]


# Singleton rate limiter
_rate_limiter = RateLimitStore()


class RateLimitMiddleware(BaseHTTPMiddleware):
    """
    SEC-002: Rate limiting middleware.
    Applies stricter limits to auth and AI endpoints.
    """

    # Paths that get the stricter auth rate limit
    AUTH_PREFIXES = ("/api/v1/auth/login", "/api/v1/auth/register", "/api/v1/auth/refresh")
    AI_PREFIXES = ("/api/v1/ai/", "/api/v1/chat")

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        # Skip rate limiting for health checks and OPTIONS
        if request.url.path in ("/health", "/api/v1/health") or request.method == "OPTIONS":
            return await call_next(request)

        client_ip = request.client.host if request.client else "unknown"
        path = request.url.path

        # Determine rate limit tier
        if any(path.startswith(p) for p in self.AUTH_PREFIXES):
            max_req = settings.RATE_LIMIT_AUTH_REQUESTS
            window = settings.RATE_LIMIT_AUTH_WINDOW_SECONDS
            tier = "auth"
        elif any(path.startswith(p) for p in self.AI_PREFIXES):
            max_req = settings.RATE_LIMIT_AI_REQUESTS
            window = settings.RATE_LIMIT_AI_WINDOW_SECONDS
            tier = "ai"
        else:
            max_req = settings.RATE_LIMIT_REQUESTS
            window = settings.RATE_LIMIT_WINDOW_SECONDS
            tier = "general"

        rate_key = f"{tier}:{client_ip}"
        is_limited, remaining = _rate_limiter.is_rate_limited(rate_key, max_req, window)

        if is_limited:
            logger.warning(
                f"Rate limit exceeded for {client_ip} on {tier} tier (path: {path})"
            )
            return JSONResponse(
                status_code=429,
                content={
                    "error": {
                        "code": "RATE_LIMITED",
                        "message": "Too many requests. Please try again later.",
                    }
                },
                headers={
                    "Retry-After": str(window),
                    "X-RateLimit-Limit": str(max_req),
                    "X-RateLimit-Remaining": "0",
                },
            )

        response = await call_next(request)
        response.headers["X-RateLimit-Limit"] = str(max_req)
        response.headers["X-RateLimit-Remaining"] = str(remaining)
        return response


# ==================== SEC-006: CSRF Protection ====================

class CSRFMiddleware(BaseHTTPMiddleware):
    """
    SEC-006: CSRF protection using double-submit cookie pattern.

    For state-changing requests (POST/PUT/PATCH/DELETE) to API endpoints,
    the client must send an X-CSRF-Token header that matches the csrf_token cookie.

    Excluded: login, register, token refresh, and WebSocket upgrades.
    """

    SAFE_METHODS = {"GET", "HEAD", "OPTIONS"}
    CSRF_EXEMPT_PATHS = (
        "/api/v1/auth/login",
        "/api/v1/auth/register",
        "/api/v1/auth/refresh",
        "/api/v1/auth/google",
        "/health",
        "/docs",
        "/openapi.json",
        "/redoc",
    )

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        path = request.url.path

        # Skip for safe methods, exempt paths, and non-API paths
        is_safe = request.method in self.SAFE_METHODS
        is_exempt = any(path.startswith(p) for p in self.CSRF_EXEMPT_PATHS)
        is_api = path.startswith("/api/")
        is_websocket = "upgrade" in request.headers.get("connection", "").lower()

        if is_safe or is_exempt or not is_api or is_websocket:
            response = await call_next(request)
        else:
            # Validate CSRF token
            cookie_token = request.cookies.get("csrf_token")
            header_token = request.headers.get("X-CSRF-Token")

            if not cookie_token or not header_token:
                return JSONResponse(
                    status_code=403,
                    content={
                        "error": {
                            "code": "CSRF_VALIDATION_FAILED",
                            "message": "CSRF token missing. Include X-CSRF-Token header.",
                        }
                    },
                )

            if not hmac.compare_digest(cookie_token, header_token):
                return JSONResponse(
                    status_code=403,
                    content={
                        "error": {
                            "code": "CSRF_VALIDATION_FAILED",
                            "message": "CSRF token mismatch.",
                        }
                    },
                )

            response = await call_next(request)

        # Always set/refresh the CSRF cookie so the client can read it
        if not request.cookies.get("csrf_token"):
            csrf_token = secrets.token_urlsafe(32)
            response.set_cookie(
                key="csrf_token",
                value=csrf_token,
                httponly=False,  # Must be readable by JS
                samesite="strict",
                secure=settings.is_production,
                max_age=86400,  # 24 hours
            )

        return response


# ==================== Existing Middleware ====================

class RequestIDMiddleware(BaseHTTPMiddleware):
    """
    Add unique request ID to each request for tracing.
    The request ID is available in request.state.request_id
    and is returned in the X-Request-ID response header.
    """

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        # Generate or get request ID
        request_id = request.headers.get("X-Request-ID", str(uuid4()))
        request.state.request_id = request_id

        # Process request
        response = await call_next(request)

        # Add request ID to response
        response.headers["X-Request-ID"] = request_id
        return response


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    """
    Log all incoming requests and their responses.
    Includes timing information for performance monitoring.
    """

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        # Start timing
        start_time = time.time()

        # Get request ID if available
        request_id = getattr(request.state, "request_id", "unknown")

        # Log incoming request
        logger.info(
            f"[{request_id}] {request.method} {request.url.path} - Started",
            extra={
                "request_id": request_id,
                "method": request.method,
                "path": request.url.path,
                "client_ip": request.client.host if request.client else "unknown"
            }
        )

        # Process request
        response = await call_next(request)

        # Calculate duration
        duration = time.time() - start_time

        # Log response
        logger.info(
            f"[{request_id}] {request.method} {request.url.path} - "
            f"{response.status_code} ({duration:.3f}s)",
            extra={
                "request_id": request_id,
                "method": request.method,
                "path": request.url.path,
                "status_code": response.status_code,
                "duration_seconds": duration
            }
        )

        # Add timing header
        response.headers["X-Response-Time"] = f"{duration:.3f}s"
        return response


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """
    Add security headers to all responses.
    """

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        response = await call_next(request)

        # Security headers
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"

        # Only add HSTS in production
        if settings.is_production:
            response.headers["Strict-Transport-Security"] = (
                "max-age=31536000; includeSubDomains"
            )

        return response


def setup_exception_handlers(app: FastAPI) -> None:
    """
    Configure exception handlers for the FastAPI app.
    """

    @app.exception_handler(TaskPulseException)
    async def taskpulse_exception_handler(
        request: Request,
        exc: TaskPulseException
    ) -> JSONResponse:
        """Handle custom TaskPulse exceptions."""
        request_id = getattr(request.state, "request_id", "unknown")

        logger.warning(
            f"[{request_id}] TaskPulseException: {exc.error_code} - {exc.message}",
            extra={
                "request_id": request_id,
                "error_code": exc.error_code,
                "details": exc.details
            }
        )

        return JSONResponse(
            status_code=exc.status_code,
            content={
                "error": {
                    "code": exc.error_code,
                    "message": exc.message,
                    "details": exc.details,
                    "request_id": request_id
                }
            }
        )

    @app.exception_handler(Exception)
    async def general_exception_handler(
        request: Request,
        exc: Exception
    ) -> JSONResponse:
        """Handle unexpected exceptions."""
        request_id = getattr(request.state, "request_id", "unknown")

        # Log the full exception in development, minimal in production
        if settings.is_development:
            logger.exception(
                f"[{request_id}] Unhandled exception: {str(exc)}",
                extra={"request_id": request_id}
            )
        else:
            logger.error(
                f"[{request_id}] Unhandled exception: {type(exc).__name__}",
                extra={"request_id": request_id}
            )

        # Return generic error in production, detailed in development
        message = str(exc) if settings.is_development else "An unexpected error occurred"

        return JSONResponse(
            status_code=500,
            content={
                "error": {
                    "code": "INTERNAL_ERROR",
                    "message": message,
                    "details": {},
                    "request_id": request_id
                }
            }
        )


def setup_middleware(app: FastAPI) -> None:
    """
    Configure all middleware for the FastAPI app.
    Order matters - middleware is executed in reverse order.
    """
    # Add middleware in reverse order of execution
    # (last added = first executed)
    app.add_middleware(SecurityHeadersMiddleware)
    app.add_middleware(RequestLoggingMiddleware)
    app.add_middleware(RateLimitMiddleware)   # SEC-002
    app.add_middleware(CSRFMiddleware)        # SEC-006
    app.add_middleware(RequestIDMiddleware)

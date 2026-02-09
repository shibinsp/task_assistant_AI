"""
TaskPulse - AI Assistant - Middleware
Custom middleware for request/response processing
"""

import time
import logging
from typing import Callable
from uuid import uuid4

from fastapi import FastAPI, Request, Response
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware

from app.config import settings
from app.core.exceptions import TaskPulseException

logger = logging.getLogger(__name__)


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
    app.add_middleware(SecurityHeadersMiddleware)
    app.add_middleware(RequestLoggingMiddleware)
    app.add_middleware(RequestIDMiddleware)

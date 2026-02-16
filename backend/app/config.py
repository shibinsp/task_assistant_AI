"""
TaskPulse - AI Assistant - Configuration Management
Handles all application settings using Pydantic Settings
"""

import secrets
import logging
from functools import lru_cache
from typing import Literal, Optional
from pydantic_settings import BaseSettings, SettingsConfigDict

logger = logging.getLogger(__name__)

# SEC-001: Generate a random SECRET_KEY at startup if none is provided via env.
# This ensures no hardcoded default is ever used. In production, always set
# SECRET_KEY via environment variable for persistence across restarts.
_GENERATED_SECRET_KEY = secrets.token_urlsafe(64)


class Settings(BaseSettings):
    """
    Application settings loaded from environment variables.
    Create a .env file in the backend directory for local development.
    """

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore"
    )

    # ==================== Application ====================
    APP_NAME: str = "TaskPulse - AI Assistant"
    APP_VERSION: str = "1.0.0"
    APP_DESCRIPTION: str = "AI-Powered Task Completion for Every Team"
    DEBUG: bool = False
    ENVIRONMENT: Literal["development", "staging", "production"] = "development"

    # ==================== Server ====================
    HOST: str = "0.0.0.0"
    PORT: int = 8000
    RELOAD: bool = False  # SEC-015: Default to False; enable explicitly in dev
    WORKERS: int = 1

    # ==================== Database ====================
    DATABASE_URL: str = "sqlite+aiosqlite:///./taskpulse.db"
    DATABASE_ECHO: bool = False  # Set to True to see SQL queries

    # ==================== Security ====================
    # SEC-001: No hardcoded secret. Random key generated per startup if env var is missing.
    SECRET_KEY: str = _GENERATED_SECRET_KEY
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    # ==================== CORS ====================
    CORS_ORIGINS: list[str] = ["http://localhost:3000", "http://localhost:8080", "http://127.0.0.1:3000"]
    CORS_ALLOW_CREDENTIALS: bool = True
    # SEC-012: Restrict CORS methods and headers to only what's needed
    CORS_ALLOW_METHODS: list[str] = ["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"]
    CORS_ALLOW_HEADERS: list[str] = [
        "Authorization", "Content-Type", "Accept", "Origin",
        "X-Request-ID", "X-CSRF-Token"
    ]

    # ==================== AI Configuration ====================
    AI_PROVIDER: Literal["mock", "openai", "anthropic", "mistral", "kimi", "ollama"] = "mock"
    OPENAI_API_KEY: str = ""
    ANTHROPIC_API_KEY: str = ""
    MISTRAL_API_KEY: str = ""
    KIMI_API_KEY: str = ""
    KIMI_MODEL: str = "moonshot-v1-8k"
    KIMI_BASE_URL: str = "https://api.moonshot.cn/v1"
    OLLAMA_BASE_URL: str = "http://localhost:11434/v1"
    OLLAMA_MODEL: str = "glm-4.7:cloud"
    AI_MODEL: str = "gpt-4"
    MISTRAL_MODEL: str = "mistral-large-latest"
    AI_MAX_TOKENS: int = 4096
    AI_TEMPERATURE: float = 0.7
    AI_CACHE_TTL: int = 3600  # Cache TTL in seconds
    AI_CACHE_MAX_SIZE: int = 1000  # SEC-010: Maximum number of cached AI responses

    # ==================== Check-In Engine ====================
    DEFAULT_CHECKIN_INTERVAL_HOURS: int = 3
    MIN_CHECKIN_INTERVAL_HOURS: int = 1
    MAX_CHECKIN_INTERVAL_HOURS: int = 8
    CHECKIN_CONFIDENCE_THRESHOLD: float = 0.7

    # ==================== Rate Limiting ====================
    RATE_LIMIT_REQUESTS: int = 100
    RATE_LIMIT_WINDOW_SECONDS: int = 60
    RATE_LIMIT_AUTH_REQUESTS: int = 10  # Stricter limit for auth endpoints
    RATE_LIMIT_AUTH_WINDOW_SECONDS: int = 60
    RATE_LIMIT_AI_REQUESTS: int = 30  # Limit for AI endpoints
    RATE_LIMIT_AI_WINDOW_SECONDS: int = 60

    # ==================== Pagination ====================
    DEFAULT_PAGE_SIZE: int = 20
    MAX_PAGE_SIZE: int = 100

    # ==================== File Upload ====================
    MAX_UPLOAD_SIZE_MB: int = 10
    ALLOWED_UPLOAD_EXTENSIONS: list[str] = [".pdf", ".doc", ".docx", ".txt", ".md"]

    # ==================== Google OAuth ====================
    GOOGLE_CLIENT_ID: str = ""

    # ==================== Email (for notifications) ====================
    SMTP_HOST: str = ""
    SMTP_PORT: int = 587
    SMTP_USER: str = ""
    SMTP_PASSWORD: str = ""
    SMTP_FROM_EMAIL: str = "noreply@taskpulse.ai"

    # ==================== Logging ====================
    LOG_LEVEL: Literal["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"] = "INFO"
    LOG_FORMAT: str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"

    # ==================== API Documentation ====================
    # SEC-016: Disabled in production; auto-enabled in development
    # Can be explicitly overridden via ENABLE_API_DOCS env var
    ENABLE_API_DOCS: Optional[bool] = None

    @property
    def is_development(self) -> bool:
        return self.ENVIRONMENT == "development"

    @property
    def is_production(self) -> bool:
        return self.ENVIRONMENT == "production"

    @property
    def max_upload_size_bytes(self) -> int:
        """Return max upload size in bytes."""
        return self.MAX_UPLOAD_SIZE_MB * 1024 * 1024

    def validate_production_settings(self) -> None:
        """Validate that production-critical settings are properly configured."""
        if self.is_production:
            # SEC-001: Reject startup if SECRET_KEY wasn't explicitly set in production
            if self.SECRET_KEY == _GENERATED_SECRET_KEY:
                raise ValueError(
                    "CRITICAL: SECRET_KEY must be explicitly set via environment variable in production! "
                    "Generate a secure key with: python -c \"import secrets; print(secrets.token_urlsafe(64))\""
                )
            if len(self.SECRET_KEY) < 32:
                raise ValueError("SECRET_KEY must be at least 32 characters in production")
            if self.DEBUG:
                raise ValueError("DEBUG must be False in production")
            # SEC-017: Warn if using SQLite in production
            if "sqlite" in self.DATABASE_URL.lower():
                logger.warning(
                    "WARNING: SQLite is not recommended for production. "
                    "Consider using PostgreSQL: DATABASE_URL=postgresql+asyncpg://user:pass@host/db"
                )
            if self.ENABLE_API_DOCS is True:
                logger.warning(
                    "WARNING: API documentation is explicitly enabled in production. "
                    "Set ENABLE_API_DOCS=false unless intentionally exposing docs."
                )
            if self.RELOAD:
                raise ValueError("RELOAD must be False in production")


@lru_cache()
def get_settings() -> Settings:
    """
    Get cached settings instance.
    Uses lru_cache to ensure settings are only loaded once.
    """
    return Settings()


# Convenience instance for imports
settings = get_settings()

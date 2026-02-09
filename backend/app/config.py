"""
TaskPulse - AI Assistant - Configuration Management
Handles all application settings using Pydantic Settings
"""

from functools import lru_cache
from typing import Literal
from pydantic_settings import BaseSettings, SettingsConfigDict


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
    RELOAD: bool = True
    WORKERS: int = 1

    # ==================== Database ====================
    DATABASE_URL: str = "sqlite+aiosqlite:///./taskpulse.db"
    DATABASE_ECHO: bool = False  # Set to True to see SQL queries

    # ==================== Security ====================
    SECRET_KEY: str = "your-super-secret-key-change-in-production-min-32-chars"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    # ==================== CORS ====================
    CORS_ORIGINS: list[str] = ["http://localhost:3000", "http://localhost:8080", "http://127.0.0.1:3000"]
    CORS_ALLOW_CREDENTIALS: bool = True
    CORS_ALLOW_METHODS: list[str] = ["*"]
    CORS_ALLOW_HEADERS: list[str] = ["*"]

    # ==================== AI Configuration ====================
    AI_PROVIDER: Literal["mock", "openai", "anthropic", "mistral"] = "mock"
    OPENAI_API_KEY: str = ""
    ANTHROPIC_API_KEY: str = ""
    MISTRAL_API_KEY: str = ""
    AI_MODEL: str = "gpt-4"
    MISTRAL_MODEL: str = "mistral-large-latest"
    AI_MAX_TOKENS: int = 4096
    AI_TEMPERATURE: float = 0.7
    AI_CACHE_TTL: int = 3600  # Cache TTL in seconds

    # ==================== Check-In Engine ====================
    DEFAULT_CHECKIN_INTERVAL_HOURS: int = 3
    MIN_CHECKIN_INTERVAL_HOURS: int = 1
    MAX_CHECKIN_INTERVAL_HOURS: int = 8
    CHECKIN_CONFIDENCE_THRESHOLD: float = 0.7

    # ==================== Rate Limiting ====================
    RATE_LIMIT_REQUESTS: int = 100
    RATE_LIMIT_WINDOW_SECONDS: int = 60

    # ==================== Pagination ====================
    DEFAULT_PAGE_SIZE: int = 20
    MAX_PAGE_SIZE: int = 100

    # ==================== File Upload ====================
    MAX_UPLOAD_SIZE_MB: int = 10
    ALLOWED_UPLOAD_EXTENSIONS: list[str] = [".pdf", ".doc", ".docx", ".txt", ".md"]

    # ==================== Email (for notifications) ====================
    SMTP_HOST: str = ""
    SMTP_PORT: int = 587
    SMTP_USER: str = ""
    SMTP_PASSWORD: str = ""
    SMTP_FROM_EMAIL: str = "noreply@taskpulse.ai"

    # ==================== Logging ====================
    LOG_LEVEL: Literal["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"] = "INFO"
    LOG_FORMAT: str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"

    @property
    def is_development(self) -> bool:
        return self.ENVIRONMENT == "development"

    @property
    def is_production(self) -> bool:
        return self.ENVIRONMENT == "production"

    def validate_production_settings(self) -> None:
        """Validate that production-critical settings are properly configured."""
        if self.is_production:
            if self.SECRET_KEY == "your-super-secret-key-change-in-production-min-32-chars":
                raise ValueError(
                    "CRITICAL: SECRET_KEY must be changed in production! "
                    "Generate a secure key with: python -c \"import secrets; print(secrets.token_urlsafe(64))\""
                )
            if len(self.SECRET_KEY) < 32:
                raise ValueError("SECRET_KEY must be at least 32 characters in production")
            if self.DEBUG:
                raise ValueError("DEBUG must be False in production")


@lru_cache()
def get_settings() -> Settings:
    """
    Get cached settings instance.
    Uses lru_cache to ensure settings are only loaded once.
    """
    return Settings()


# Convenience instance for imports
settings = get_settings()

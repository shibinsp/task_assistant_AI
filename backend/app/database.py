"""
TaskPulse - AI Assistant - Database Configuration
PostgreSQL (Supabase) database setup with SQLAlchemy async support
"""

import enum as _enum
import logging
import ssl
import uuid
from typing import AsyncGenerator

from sqlalchemy import Column, DateTime, JSON, String, func
from sqlalchemy import Enum as _SQLAlchemyEnum
from sqlalchemy.dialects.postgresql import UUID as PG_UUID, JSONB
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase, declared_attr


# Cross-database compatible JSONB: uses JSONB on PostgreSQL, JSON on SQLite
CompatibleJSONB = JSONB().with_variant(JSON(), "sqlite")

# Cross-database compatible UUID: uses native UUID on PostgreSQL, String on SQLite
CompatibleUUID = PG_UUID(as_uuid=True).with_variant(String(36), "sqlite")


class Enum(_SQLAlchemyEnum):
    """
    Custom SQLAlchemy Enum that uses Python enum *values* (not names) for DB storage.

    PostgreSQL enum types were created with lowercase values (e.g. 'super_admin'),
    matching the Python enum values. SQLAlchemy's default Enum uses enum names
    (e.g. 'SUPER_ADMIN'), causing a mismatch. This custom class fixes that.
    """

    def __init__(self, *enums, **kw):
        if (
            len(enums) == 1
            and isinstance(enums[0], type)
            and issubclass(enums[0], _enum.Enum)
        ):
            kw.setdefault("values_callable", lambda x: [e.value for e in x])
        super().__init__(*enums, **kw)

from app.config import settings

logger = logging.getLogger(__name__)

# SSL context for Supabase connection pooler (uses self-signed certs)
_ssl_context = ssl.create_default_context()
_ssl_context.check_hostname = False
_ssl_context.verify_mode = ssl.CERT_NONE

# Create async engine for PostgreSQL (Supabase)
engine = create_async_engine(
    settings.DATABASE_URL,
    echo=settings.DATABASE_ECHO,
    future=True,
    pool_size=5,
    max_overflow=10,
    pool_pre_ping=True,
    connect_args=(
        {"ssl": _ssl_context, "statement_cache_size": 0}
        if "asyncpg" in settings.DATABASE_URL
        else {}
    ),
)

# Create async session factory
AsyncSessionLocal = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False
)


class Base(DeclarativeBase):
    """
    Base class for all SQLAlchemy models.
    Provides common columns and functionality.
    """

    # Generate table name automatically from class name
    @declared_attr.directive
    def __tablename__(cls) -> str:
        """Convert CamelCase class name to snake_case table name."""
        name = cls.__name__
        return ''.join(
            ['_' + c.lower() if c.isupper() else c for c in name]
        ).lstrip('_') + 's'

    # Common columns for all models — using cross-DB compatible UUID
    id = Column(
        CompatibleUUID,
        primary_key=True,
        default=uuid.uuid4,
        index=True
    )
    created_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
        index=True
    )
    updated_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False
    )

    def to_dict(self) -> dict:
        """Convert model to dictionary."""
        result = {}
        for column in self.__table__.columns:
            value = getattr(self, column.name)
            # Convert UUID to string for JSON serialization
            if isinstance(value, uuid.UUID):
                value = str(value)
            result[column.name] = value
        return result


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """
    Dependency to get database session.
    Use with FastAPI's Depends.

    Example:
        @app.get("/users")
        async def get_users(db: AsyncSession = Depends(get_db)):
            ...
    """
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


async def init_db() -> None:
    """
    Initialize database by creating all tables.
    Called on application startup.
    """
    async with engine.begin() as conn:
        # Import ALL models to ensure they're registered with Base.metadata
        from app.models import (  # noqa: F401
            # Phase 2 - Auth & Users
            Organization, User,
            # Phase 4 - Tasks
            Task, TaskDependency, TaskHistory, TaskComment,
            # Phase 6 - Check-ins
            CheckIn, CheckInConfig, CheckInReminder,
            # Phase 7 - Knowledge Base / AI Unblock
            Document, DocumentChunk, UnblockSession,
            # Phase 8 - Skills
            Skill, UserSkill, SkillGap, SkillMetrics, LearningPath,
            # Phase 10 - Predictions
            Prediction, VelocitySnapshot,
            # Phase 11 - Automation
            AutomationPattern, AIAgent, AgentRun,
            # Phase 12 - Workforce
            WorkforceScore, ManagerEffectiveness, OrgHealthSnapshot, RestructuringScenario,
            # Phase 13 - Notifications & Integrations
            Notification, NotificationPreference, Integration, Webhook, WebhookDelivery,
            # Phase 14 - Admin & Audit
            AuditLog, GDPRRequest, APIKey, SystemHealth,
            # Phase 15 - Agent Orchestration
            Agent, AgentExecution, AgentConversation, AgentSchedule,
        )

        # Create all tables
        await conn.run_sync(Base.metadata.create_all)


async def close_db() -> None:
    """
    Close database connections.
    Called on application shutdown.
    """
    await engine.dispose()


# Utility functions for common database operations
class DatabaseUtils:
    """Utility class for common database operations."""

    @staticmethod
    async def get_by_id(db: AsyncSession, model: type[Base], id: str):
        """Get a record by ID."""
        from sqlalchemy import select
        result = await db.execute(select(model).where(model.id == id))
        return result.scalar_one_or_none()

    @staticmethod
    async def get_all(
        db: AsyncSession,
        model: type[Base],
        skip: int = 0,
        limit: int = 100
    ):
        """Get all records with pagination."""
        from sqlalchemy import select
        result = await db.execute(
            select(model).offset(skip).limit(limit)
        )
        return result.scalars().all()

    @staticmethod
    async def create(db: AsyncSession, model: type[Base], **kwargs):
        """Create a new record."""
        instance = model(**kwargs)
        db.add(instance)
        await db.flush()
        await db.refresh(instance)
        return instance

    @staticmethod
    async def update(db: AsyncSession, instance: Base, **kwargs):
        """Update an existing record."""
        for key, value in kwargs.items():
            if hasattr(instance, key):
                setattr(instance, key, value)
        await db.flush()
        await db.refresh(instance)
        return instance

    @staticmethod
    async def delete(db: AsyncSession, instance: Base):
        """Delete a record."""
        await db.delete(instance)
        await db.flush()

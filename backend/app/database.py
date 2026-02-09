"""
TaskPulse - AI Assistant - Database Configuration
SQLite database setup with SQLAlchemy async support
"""

from datetime import datetime
from typing import AsyncGenerator
import uuid

from sqlalchemy import Column, DateTime, String, event
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase, declared_attr

from app.config import settings


# Create async engine for SQLite
engine = create_async_engine(
    settings.DATABASE_URL,
    echo=settings.DATABASE_ECHO,
    future=True,
    connect_args={"check_same_thread": False}  # Required for SQLite
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

    # Common columns for all models
    id = Column(
        String(36),
        primary_key=True,
        default=lambda: str(uuid.uuid4()),
        index=True
    )
    created_at = Column(
        DateTime,
        default=datetime.utcnow,
        nullable=False,
        index=True
    )
    updated_at = Column(
        DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        nullable=False
    )

    def to_dict(self) -> dict:
        """Convert model to dictionary."""
        return {
            column.name: getattr(self, column.name)
            for column in self.__table__.columns
        }


# Enable foreign key support for SQLite
@event.listens_for(engine.sync_engine, "connect")
def set_sqlite_pragma(dbapi_connection, connection_record):
    """Enable foreign keys and other optimizations for SQLite."""
    cursor = dbapi_connection.cursor()
    cursor.execute("PRAGMA foreign_keys=ON")
    cursor.execute("PRAGMA journal_mode=WAL")  # Write-Ahead Logging for better concurrency
    cursor.execute("PRAGMA synchronous=NORMAL")
    cursor.execute("PRAGMA cache_size=10000")
    cursor.execute("PRAGMA temp_store=MEMORY")
    cursor.close()


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
            Organization, User, Session,
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

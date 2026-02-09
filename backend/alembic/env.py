"""
TaskPulse - AI Assistant - Alembic Environment Configuration
Async SQLAlchemy support for database migrations
"""

import asyncio
from logging.config import fileConfig

from sqlalchemy import pool
from sqlalchemy.engine import Connection
from sqlalchemy.ext.asyncio import async_engine_from_config

from alembic import context

# Import the SQLAlchemy Base and all models
from app.database import Base
from app.config import settings

# Import all models to ensure they're registered with Base.metadata
from app.models import (
    # Organization & Users
    Organization, User, Session,
    # Tasks
    Task, TaskDependency, TaskHistory, TaskComment,
    # Check-ins
    CheckIn, CheckInConfig, CheckInReminder,
    # Knowledge Base
    Document, DocumentChunk, UnblockSession,
    # Skills
    Skill, UserSkill, SkillGap, SkillMetrics, LearningPath,
    # Predictions
    Prediction, VelocitySnapshot,
    # Automation
    AutomationPattern, AIAgent, AgentRun,
    # Workforce
    WorkforceScore, ManagerEffectiveness, OrgHealthSnapshot, RestructuringScenario,
    # Notifications
    Notification, NotificationPreference, Integration, Webhook, WebhookDelivery,
    # Audit
    AuditLog, GDPRRequest, APIKey, SystemHealth,
    # Agent Orchestration
    Agent, AgentExecution, AgentConversation, AgentSchedule,
)

# Alembic Config object
config = context.config

# Override sqlalchemy.url with settings from app
config.set_main_option("sqlalchemy.url", settings.DATABASE_URL)

# Interpret the config file for Python logging
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# Target metadata for autogenerate support
target_metadata = Base.metadata


def run_migrations_offline() -> None:
    """
    Run migrations in 'offline' mode.

    This configures the context with just a URL
    and not an Engine, though an Engine is acceptable
    here as well. By skipping the Engine creation
    we don't even need a DBAPI to be available.

    Calls to context.execute() here emit the given string to the
    script output.
    """
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()


def do_run_migrations(connection: Connection) -> None:
    """Run migrations with the given connection."""
    context.configure(connection=connection, target_metadata=target_metadata)

    with context.begin_transaction():
        context.run_migrations()


async def run_async_migrations() -> None:
    """
    Run migrations in 'online' mode with async engine.

    In this scenario we need to create an Engine
    and associate a connection with the context.
    """
    connectable = async_engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    async with connectable.connect() as connection:
        await connection.run_sync(do_run_migrations)

    await connectable.dispose()


def run_migrations_online() -> None:
    """Run migrations in 'online' mode."""
    asyncio.run(run_async_migrations())


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()

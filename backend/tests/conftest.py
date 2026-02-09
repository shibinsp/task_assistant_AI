"""
TaskPulse - AI Assistant - Test Configuration
Pytest fixtures and test utilities
"""

import pytest
import asyncio
from typing import AsyncGenerator, Generator
from datetime import datetime, timedelta
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker

from app.main import app
from app.database import Base, get_db
from app.models.user import User, UserRole
from app.models.organization import Organization, PlanTier
from app.core.security import hash_password, create_access_token
from app.utils.helpers import generate_uuid

# Test database URL
TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"


@pytest.fixture(scope="session")
def event_loop() -> Generator:
    """Create event loop for async tests."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="function")
async def test_engine():
    """Create test database engine."""
    engine = create_async_engine(
        TEST_DATABASE_URL,
        echo=False,
        future=True
    )

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    yield engine

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)

    await engine.dispose()


@pytest.fixture(scope="function")
async def test_session(test_engine) -> AsyncGenerator[AsyncSession, None]:
    """Create test database session."""
    async_session = async_sessionmaker(
        test_engine,
        class_=AsyncSession,
        expire_on_commit=False
    )

    async with async_session() as session:
        yield session
        await session.rollback()


@pytest.fixture(scope="function")
async def client(test_session) -> AsyncGenerator[AsyncClient, None]:
    """Create test HTTP client with database override."""

    async def override_get_db():
        yield test_session

    app.dependency_overrides[get_db] = override_get_db

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac

    app.dependency_overrides.clear()


@pytest.fixture
async def test_org(test_session) -> Organization:
    """Create a test organization."""
    org = Organization(
        id=generate_uuid(),
        name="Test Organization",
        slug="test-org",
        plan=PlanTier.PROFESSIONAL,
        is_active=True
    )
    test_session.add(org)
    await test_session.commit()
    await test_session.refresh(org)
    return org


@pytest.fixture
async def test_user(test_session, test_org) -> User:
    """Create a test user (employee role)."""
    user = User(
        id=generate_uuid(),
        org_id=test_org.id,
        email="testuser@example.com",
        password_hash=hash_password("password123"),
        first_name="Test",
        last_name="User",
        role=UserRole.EMPLOYEE,
        is_active=True,
        is_email_verified=True
    )
    test_session.add(user)
    await test_session.commit()
    await test_session.refresh(user)
    return user


@pytest.fixture
async def test_admin(test_session, test_org) -> User:
    """Create a test admin user."""
    admin = User(
        id=generate_uuid(),
        org_id=test_org.id,
        email="admin@example.com",
        password_hash=hash_password("adminpass123"),
        first_name="Admin",
        last_name="User",
        role=UserRole.ORG_ADMIN,
        is_active=True,
        is_email_verified=True
    )
    test_session.add(admin)
    await test_session.commit()
    await test_session.refresh(admin)
    return admin


@pytest.fixture
async def test_super_admin(test_session, test_org) -> User:
    """Create a test super admin user."""
    super_admin = User(
        id=generate_uuid(),
        org_id=test_org.id,
        email="superadmin@example.com",
        password_hash=hash_password("superpass123"),
        first_name="Super",
        last_name="Admin",
        role=UserRole.SUPER_ADMIN,
        is_active=True,
        is_email_verified=True
    )
    test_session.add(super_admin)
    await test_session.commit()
    await test_session.refresh(super_admin)
    return super_admin


@pytest.fixture
async def test_manager(test_session, test_org) -> User:
    """Create a test manager user."""
    manager = User(
        id=generate_uuid(),
        org_id=test_org.id,
        email="manager@example.com",
        password_hash=hash_password("managerpass123"),
        first_name="Test",
        last_name="Manager",
        role=UserRole.MANAGER,
        is_active=True,
        is_email_verified=True
    )
    test_session.add(manager)
    await test_session.commit()
    await test_session.refresh(manager)
    return manager


@pytest.fixture
async def user_token(test_user) -> str:
    """Generate JWT token for test user."""
    return create_access_token(data={
        "sub": test_user.id,
        "org_id": test_user.org_id,
        "role": test_user.role.value,
        "email": test_user.email
    })


@pytest.fixture
async def admin_token(test_admin) -> str:
    """Generate JWT token for test admin."""
    return create_access_token(data={
        "sub": test_admin.id,
        "org_id": test_admin.org_id,
        "role": test_admin.role.value,
        "email": test_admin.email
    })


@pytest.fixture
async def super_admin_token(test_super_admin) -> str:
    """Generate JWT token for test super admin."""
    return create_access_token(data={
        "sub": test_super_admin.id,
        "org_id": test_super_admin.org_id,
        "role": test_super_admin.role.value,
        "email": test_super_admin.email
    })


@pytest.fixture
async def manager_token(test_manager) -> str:
    """Generate JWT token for test manager."""
    return create_access_token(data={
        "sub": test_manager.id,
        "org_id": test_manager.org_id,
        "role": test_manager.role.value,
        "email": test_manager.email
    })


def auth_headers(token: str) -> dict:
    """Create authorization headers."""
    return {"Authorization": f"Bearer {token}"}


# Utility functions for tests
def create_task_data(
    title: str = "Test Task",
    description: str = "Test description",
    priority: str = "medium",
    estimated_hours: float = 8.0
) -> dict:
    """Create task data for tests."""
    return {
        "title": title,
        "description": description,
        "priority": priority,
        "estimated_hours": estimated_hours
    }


def create_checkin_response_data(
    progress: int = 50,
    status: str = "on_track",
    notes: str = "Making good progress"
) -> dict:
    """Create check-in response data for tests."""
    return {
        "progress_percentage": progress,
        "status": status,
        "notes": notes
    }

"""
TaskPulse - AI Assistant - Check-in Tests
Tests for check-in endpoints
"""

import pytest
from httpx import AsyncClient
from datetime import datetime, timedelta

from tests.conftest import auth_headers
from app.models.task import Task, TaskStatus, TaskPriority
from app.models.checkin import CheckIn, CheckInConfig
from app.utils.helpers import generate_uuid


class TestCheckInEndpoints:
    """Test check-in management endpoints."""

    @pytest.mark.asyncio
    async def test_list_checkins(
        self, client: AsyncClient, test_session, test_user, user_token, test_org
    ):
        """Test listing check-ins."""
        # Create a task
        task = Task(
            id=generate_uuid(),
            org_id=test_org.id,
            title="Task with Checkins",
            status=TaskStatus.IN_PROGRESS,
            priority=TaskPriority.MEDIUM,
            created_by=test_user.id,
            assigned_to=test_user.id
        )
        test_session.add(task)
        await test_session.flush()

        # Create check-ins
        for i in range(3):
            checkin = CheckIn(
                id=generate_uuid(),
                org_id=test_org.id,
                task_id=task.id,
                user_id=test_user.id,
                cycle_number=i + 1,
                scheduled_at=datetime.utcnow() - timedelta(hours=3 * i)
            )
            test_session.add(checkin)
        await test_session.commit()

        response = await client.get(
            "/api/v1/checkins",
            headers=auth_headers(user_token)
        )
        assert response.status_code == 200
        data = response.json()
        assert "checkins" in data
        assert "total" in data

    @pytest.mark.asyncio
    async def test_get_checkin(
        self, client: AsyncClient, test_session, test_user, user_token, test_org
    ):
        """Test getting a specific check-in."""
        task = Task(
            id=generate_uuid(),
            org_id=test_org.id,
            title="Task",
            status=TaskStatus.IN_PROGRESS,
            priority=TaskPriority.MEDIUM,
            created_by=test_user.id,
            assigned_to=test_user.id
        )
        test_session.add(task)
        await test_session.flush()

        checkin = CheckIn(
            id=generate_uuid(),
            org_id=test_org.id,
            task_id=task.id,
            user_id=test_user.id,
            cycle_number=1,
            scheduled_at=datetime.utcnow()
        )
        test_session.add(checkin)
        await test_session.commit()

        response = await client.get(
            f"/api/v1/checkins/{checkin.id}",
            headers=auth_headers(user_token)
        )
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == checkin.id
        assert data["task_id"] == task.id

    @pytest.mark.asyncio
    async def test_respond_to_checkin(
        self, client: AsyncClient, test_session, test_user, user_token, test_org
    ):
        """Test responding to a check-in."""
        task = Task(
            id=generate_uuid(),
            org_id=test_org.id,
            title="Task",
            status=TaskStatus.IN_PROGRESS,
            priority=TaskPriority.MEDIUM,
            created_by=test_user.id,
            assigned_to=test_user.id
        )
        test_session.add(task)
        await test_session.flush()

        checkin = CheckIn(
            id=generate_uuid(),
            org_id=test_org.id,
            task_id=task.id,
            user_id=test_user.id,
            cycle_number=1,
            scheduled_at=datetime.utcnow(),
            response_status="pending"
        )
        test_session.add(checkin)
        await test_session.commit()

        response = await client.post(
            f"/api/v1/checkins/{checkin.id}/respond",
            headers=auth_headers(user_token),
            json={
                "progress_percentage": 50,
                "status": "on_track",
                "notes": "Making good progress"
            }
        )
        assert response.status_code == 200
        data = response.json()
        assert data["response_status"] == "responded"
        assert data["progress_percentage"] == 50

    @pytest.mark.asyncio
    async def test_respond_with_blocker(
        self, client: AsyncClient, test_session, test_user, user_token, test_org
    ):
        """Test responding to a check-in with a blocker."""
        task = Task(
            id=generate_uuid(),
            org_id=test_org.id,
            title="Blocked Task",
            status=TaskStatus.IN_PROGRESS,
            priority=TaskPriority.HIGH,
            created_by=test_user.id,
            assigned_to=test_user.id
        )
        test_session.add(task)
        await test_session.flush()

        checkin = CheckIn(
            id=generate_uuid(),
            org_id=test_org.id,
            task_id=task.id,
            user_id=test_user.id,
            cycle_number=1,
            scheduled_at=datetime.utcnow(),
            response_status="pending"
        )
        test_session.add(checkin)
        await test_session.commit()

        response = await client.post(
            f"/api/v1/checkins/{checkin.id}/respond",
            headers=auth_headers(user_token),
            json={
                "progress_percentage": 30,
                "status": "blocked",
                "has_blocker": True,
                "blocker_type": "dependency",
                "blocker_description": "Waiting for API from other team"
            }
        )
        assert response.status_code == 200
        data = response.json()
        assert data["has_blocker"] is True
        assert data["blocker_type"] == "dependency"

    @pytest.mark.asyncio
    async def test_get_checkin_config(
        self, client: AsyncClient, test_admin, admin_token
    ):
        """Test getting check-in configuration."""
        response = await client.get(
            "/api/v1/checkins/config",
            headers=auth_headers(admin_token)
        )
        assert response.status_code == 200
        data = response.json()
        # Should return default config if none exists
        assert "default_interval_hours" in data

    @pytest.mark.asyncio
    async def test_update_checkin_config(
        self, client: AsyncClient, test_session, test_admin, admin_token, test_org
    ):
        """Test updating check-in configuration."""
        # Create config first
        config = CheckInConfig(
            id=generate_uuid(),
            org_id=test_org.id,
            default_interval_hours=3
        )
        test_session.add(config)
        await test_session.commit()

        response = await client.patch(
            "/api/v1/checkins/config",
            headers=auth_headers(admin_token),
            json={
                "default_interval_hours": 4,
                "auto_escalate_after_missed": 2
            }
        )
        assert response.status_code == 200
        data = response.json()
        assert data["default_interval_hours"] == 4

    @pytest.mark.asyncio
    async def test_get_pending_checkins(
        self, client: AsyncClient, test_session, test_user, user_token, test_org
    ):
        """Test getting pending check-ins for user."""
        task = Task(
            id=generate_uuid(),
            org_id=test_org.id,
            title="Task with Pending Checkin",
            status=TaskStatus.IN_PROGRESS,
            priority=TaskPriority.MEDIUM,
            created_by=test_user.id,
            assigned_to=test_user.id
        )
        test_session.add(task)
        await test_session.flush()

        # Create a pending check-in
        checkin = CheckIn(
            id=generate_uuid(),
            org_id=test_org.id,
            task_id=task.id,
            user_id=test_user.id,
            cycle_number=1,
            scheduled_at=datetime.utcnow() - timedelta(hours=1),
            response_status="pending"
        )
        test_session.add(checkin)
        await test_session.commit()

        response = await client.get(
            "/api/v1/checkins?pending_only=true",
            headers=auth_headers(user_token)
        )
        assert response.status_code == 200
        data = response.json()
        assert all(c["response_status"] == "pending" for c in data["checkins"])

    @pytest.mark.asyncio
    async def test_escalate_checkin(
        self, client: AsyncClient, test_session, test_manager, manager_token, test_user, test_org
    ):
        """Test escalating a check-in."""
        task = Task(
            id=generate_uuid(),
            org_id=test_org.id,
            title="Task to Escalate",
            status=TaskStatus.BLOCKED,
            priority=TaskPriority.HIGH,
            created_by=test_user.id,
            assigned_to=test_user.id
        )
        test_session.add(task)
        await test_session.flush()

        checkin = CheckIn(
            id=generate_uuid(),
            org_id=test_org.id,
            task_id=task.id,
            user_id=test_user.id,
            cycle_number=1,
            scheduled_at=datetime.utcnow(),
            response_status="responded",
            has_blocker=True
        )
        test_session.add(checkin)
        await test_session.commit()

        response = await client.post(
            f"/api/v1/checkins/{checkin.id}/escalate",
            headers=auth_headers(manager_token),
            json={
                "reason": "Critical blocker needs attention",
                "escalate_to": test_manager.id
            }
        )
        assert response.status_code == 200
        data = response.json()
        assert data["was_escalated"] is True

    @pytest.mark.asyncio
    async def test_get_checkin_statistics(
        self, client: AsyncClient, test_manager, manager_token
    ):
        """Test getting check-in statistics."""
        response = await client.get(
            "/api/v1/checkins/statistics",
            headers=auth_headers(manager_token)
        )
        assert response.status_code == 200
        data = response.json()
        assert "total_checkins" in data
        assert "response_rate" in data

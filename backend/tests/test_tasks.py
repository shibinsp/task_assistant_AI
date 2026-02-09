"""
TaskPulse - AI Assistant - Task Tests
Tests for task management endpoints
"""

import pytest
from httpx import AsyncClient

from tests.conftest import auth_headers, create_task_data
from app.models.task import Task, TaskStatus, TaskPriority
from app.utils.helpers import generate_uuid


class TestTaskEndpoints:
    """Test task management endpoints."""

    @pytest.mark.asyncio
    async def test_create_task(self, client: AsyncClient, test_admin, admin_token):
        """Test creating a task (requires admin/manager role)."""
        task_data = create_task_data(title="New Test Task")

        response = await client.post(
            "/api/v1/tasks",
            headers=auth_headers(admin_token),
            json=task_data
        )
        assert response.status_code == 201
        data = response.json()
        assert data["title"] == "New Test Task"
        assert data["status"] == "todo"
        assert data["priority"] == "medium"

    @pytest.mark.asyncio
    async def test_create_task_with_priority(self, client: AsyncClient, test_admin, admin_token):
        """Test creating a task with specific priority."""
        task_data = create_task_data(title="High Priority Task", priority="critical")

        response = await client.post(
            "/api/v1/tasks",
            headers=auth_headers(admin_token),
            json=task_data
        )
        assert response.status_code == 201
        assert response.json()["priority"] == "critical"

    @pytest.mark.asyncio
    async def test_list_tasks(self, client: AsyncClient, test_session, test_user, user_token, test_org):
        """Test listing tasks."""
        # Create some tasks
        for i in range(3):
            task = Task(
                id=generate_uuid(),
                org_id=test_org.id,
                title=f"Task {i}",
                status=TaskStatus.TODO,
                priority=TaskPriority.MEDIUM,
                created_by=test_user.id,
                assigned_to=test_user.id
            )
            test_session.add(task)
        await test_session.commit()

        response = await client.get(
            "/api/v1/tasks",
            headers=auth_headers(user_token)
        )
        assert response.status_code == 200
        data = response.json()
        assert "tasks" in data
        assert "total" in data
        assert len(data["tasks"]) >= 3

    @pytest.mark.asyncio
    async def test_list_tasks_with_status_filter(
        self, client: AsyncClient, test_session, test_user, user_token, test_org
    ):
        """Test listing tasks with status filter."""
        # Create tasks with different statuses
        for status in [TaskStatus.TODO, TaskStatus.IN_PROGRESS, TaskStatus.DONE]:
            task = Task(
                id=generate_uuid(),
                org_id=test_org.id,
                title=f"Task {status.value}",
                status=status,
                priority=TaskPriority.MEDIUM,
                created_by=test_user.id,
                assigned_to=test_user.id
            )
            test_session.add(task)
        await test_session.commit()

        response = await client.get(
            "/api/v1/tasks?status=in_progress",
            headers=auth_headers(user_token)
        )
        assert response.status_code == 200
        data = response.json()
        for task in data["tasks"]:
            assert task["status"] == "in_progress"

    @pytest.mark.asyncio
    async def test_get_task(self, client: AsyncClient, test_session, test_user, user_token, test_org):
        """Test getting a specific task."""
        task = Task(
            id=generate_uuid(),
            org_id=test_org.id,
            title="Specific Task",
            description="Task description",
            status=TaskStatus.TODO,
            priority=TaskPriority.HIGH,
            created_by=test_user.id,
            assigned_to=test_user.id
        )
        test_session.add(task)
        await test_session.commit()

        response = await client.get(
            f"/api/v1/tasks/{task.id}",
            headers=auth_headers(user_token)
        )
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == task.id
        assert data["title"] == "Specific Task"

    @pytest.mark.asyncio
    async def test_get_nonexistent_task(self, client: AsyncClient, user_token):
        """Test getting a non-existent task."""
        response = await client.get(
            f"/api/v1/tasks/{generate_uuid()}",
            headers=auth_headers(user_token)
        )
        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_update_task(self, client: AsyncClient, test_session, test_user, user_token, test_org):
        """Test updating a task."""
        task = Task(
            id=generate_uuid(),
            org_id=test_org.id,
            title="Original Title",
            status=TaskStatus.TODO,
            priority=TaskPriority.MEDIUM,
            created_by=test_user.id,
            assigned_to=test_user.id
        )
        test_session.add(task)
        await test_session.commit()

        response = await client.patch(
            f"/api/v1/tasks/{task.id}",
            headers=auth_headers(user_token),
            json={"title": "Updated Title", "priority": "high"}
        )
        assert response.status_code == 200
        data = response.json()
        assert data["title"] == "Updated Title"
        assert data["priority"] == "high"

    @pytest.mark.asyncio
    async def test_update_task_status(
        self, client: AsyncClient, test_session, test_user, user_token, test_org
    ):
        """Test updating task status."""
        task = Task(
            id=generate_uuid(),
            org_id=test_org.id,
            title="Status Test Task",
            status=TaskStatus.TODO,
            priority=TaskPriority.MEDIUM,
            created_by=test_user.id,
            assigned_to=test_user.id
        )
        test_session.add(task)
        await test_session.commit()

        response = await client.patch(
            f"/api/v1/tasks/{task.id}/status",
            headers=auth_headers(user_token),
            json={"status": "in_progress"}
        )
        assert response.status_code == 200
        assert response.json()["status"] == "in_progress"

    @pytest.mark.asyncio
    async def test_invalid_status_transition(
        self, client: AsyncClient, test_session, test_user, user_token, test_org
    ):
        """Test invalid status transition."""
        task = Task(
            id=generate_uuid(),
            org_id=test_org.id,
            title="Invalid Transition Task",
            status=TaskStatus.TODO,
            priority=TaskPriority.MEDIUM,
            created_by=test_user.id,
            assigned_to=test_user.id
        )
        test_session.add(task)
        await test_session.commit()

        # Can't go directly from TODO to DONE
        response = await client.patch(
            f"/api/v1/tasks/{task.id}/status",
            headers=auth_headers(user_token),
            json={"status": "done"}
        )
        assert response.status_code == 400

    @pytest.mark.asyncio
    async def test_delete_task(self, client: AsyncClient, test_session, test_admin, admin_token, test_org):
        """Test deleting a task."""
        task = Task(
            id=generate_uuid(),
            org_id=test_org.id,
            title="Task to Delete",
            status=TaskStatus.TODO,
            priority=TaskPriority.LOW,
            created_by=test_admin.id
        )
        test_session.add(task)
        await test_session.commit()

        response = await client.delete(
            f"/api/v1/tasks/{task.id}",
            headers=auth_headers(admin_token)
        )
        assert response.status_code == 204

    @pytest.mark.asyncio
    async def test_create_subtask(
        self, client: AsyncClient, test_session, test_user, user_token, test_org
    ):
        """Test creating a subtask."""
        parent_task = Task(
            id=generate_uuid(),
            org_id=test_org.id,
            title="Parent Task",
            status=TaskStatus.IN_PROGRESS,
            priority=TaskPriority.HIGH,
            created_by=test_user.id,
            assigned_to=test_user.id
        )
        test_session.add(parent_task)
        await test_session.commit()

        response = await client.post(
            f"/api/v1/tasks/{parent_task.id}/subtasks",
            headers=auth_headers(user_token),
            json={"title": "Subtask 1", "description": "First subtask"}
        )
        assert response.status_code == 201
        data = response.json()
        assert data["title"] == "Subtask 1"
        assert data["parent_task_id"] == parent_task.id
        assert data["is_subtask"] is True

    @pytest.mark.asyncio
    async def test_get_subtasks(
        self, client: AsyncClient, test_session, test_user, user_token, test_org
    ):
        """Test getting subtasks."""
        parent_task = Task(
            id=generate_uuid(),
            org_id=test_org.id,
            title="Parent Task",
            status=TaskStatus.IN_PROGRESS,
            priority=TaskPriority.HIGH,
            created_by=test_user.id,
            assigned_to=test_user.id
        )
        test_session.add(parent_task)
        await test_session.flush()

        # Create subtasks
        for i in range(2):
            subtask = Task(
                id=generate_uuid(),
                org_id=test_org.id,
                title=f"Subtask {i}",
                status=TaskStatus.TODO,
                priority=TaskPriority.MEDIUM,
                created_by=test_user.id,
                parent_task_id=parent_task.id
            )
            test_session.add(subtask)
        await test_session.commit()

        response = await client.get(
            f"/api/v1/tasks/{parent_task.id}/subtasks",
            headers=auth_headers(user_token)
        )
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 2

    @pytest.mark.asyncio
    async def test_add_comment(
        self, client: AsyncClient, test_session, test_user, user_token, test_org
    ):
        """Test adding a comment to a task."""
        task = Task(
            id=generate_uuid(),
            org_id=test_org.id,
            title="Task with Comments",
            status=TaskStatus.IN_PROGRESS,
            priority=TaskPriority.MEDIUM,
            created_by=test_user.id,
            assigned_to=test_user.id
        )
        test_session.add(task)
        await test_session.commit()

        response = await client.post(
            f"/api/v1/tasks/{task.id}/comments",
            headers=auth_headers(user_token),
            json={"content": "This is a test comment"}
        )
        assert response.status_code == 201
        data = response.json()
        assert data["content"] == "This is a test comment"
        assert data["user_id"] == test_user.id

    @pytest.mark.asyncio
    async def test_get_task_statistics(self, client: AsyncClient, test_user, user_token):
        """Test getting task statistics."""
        response = await client.get(
            "/api/v1/tasks/statistics",
            headers=auth_headers(user_token)
        )
        assert response.status_code == 200
        data = response.json()
        assert "by_status" in data
        assert "by_priority" in data

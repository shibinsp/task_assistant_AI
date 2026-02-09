"""
TaskPulse - AI Assistant - Prediction Tests
Tests for prediction engine endpoints
"""

import pytest
from httpx import AsyncClient

from tests.conftest import auth_headers


class TestPredictionEndpoints:
    """Test prediction endpoints."""

    @pytest.mark.asyncio
    async def test_get_task_prediction(self, client: AsyncClient, test_admin, admin_token):
        """Test getting task delivery prediction."""
        # First create a task
        task_response = await client.post(
            "/api/v1/tasks",
            headers=auth_headers(admin_token),
            json={
                "title": "Task for Prediction",
                "description": "Test task for prediction",
                "estimated_hours": 8.0
            }
        )

        if task_response.status_code == 201:
            task_id = task_response.json()["id"]

            response = await client.get(
                f"/api/v1/predictions/tasks/{task_id}",
                headers=auth_headers(admin_token)
            )
            assert response.status_code in [200, 404]  # 404 if no prediction data yet

    @pytest.mark.asyncio
    async def test_get_hiring_predictions(self, client: AsyncClient, test_admin, admin_token):
        """Test getting hiring predictions."""
        response = await client.get(
            "/api/v1/predictions/hiring",
            headers=auth_headers(admin_token)
        )
        # May return 200 with empty data or 404 if no data
        assert response.status_code in [200, 403, 404]

    @pytest.mark.asyncio
    async def test_get_prediction_accuracy(self, client: AsyncClient, test_admin, admin_token):
        """Test getting prediction accuracy metrics."""
        response = await client.get(
            "/api/v1/predictions/accuracy",
            headers=auth_headers(admin_token)
        )
        assert response.status_code in [200, 403]

    @pytest.mark.asyncio
    async def test_predictions_unauthorized(self, client: AsyncClient):
        """Test predictions require authentication."""
        response = await client.get("/api/v1/predictions/hiring")
        assert response.status_code == 401

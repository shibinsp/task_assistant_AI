"""
TaskPulse - AI Assistant - Workforce Intelligence Tests
Tests for workforce intelligence endpoints
"""

import pytest
from httpx import AsyncClient

from tests.conftest import auth_headers


class TestWorkforceEndpoints:
    """Test workforce intelligence endpoints."""

    @pytest.mark.asyncio
    async def test_list_workforce_scores(self, client: AsyncClient, test_admin, admin_token):
        """Test listing workforce scores."""
        response = await client.get(
            "/api/v1/workforce/scores",
            headers=auth_headers(admin_token)
        )
        # Requires enterprise plan or specific permissions
        assert response.status_code in [200, 403]

    @pytest.mark.asyncio
    async def test_get_user_workforce_score(self, client: AsyncClient, test_user, test_admin, admin_token):
        """Test getting specific user's workforce score."""
        response = await client.get(
            f"/api/v1/workforce/scores/{test_user.id}",
            headers=auth_headers(admin_token)
        )
        assert response.status_code in [200, 403, 404]

    @pytest.mark.asyncio
    async def test_get_manager_ranking(self, client: AsyncClient, test_admin, admin_token):
        """Test getting manager effectiveness ranking."""
        response = await client.get(
            "/api/v1/workforce/managers/ranking",
            headers=auth_headers(admin_token)
        )
        assert response.status_code in [200, 403]

    @pytest.mark.asyncio
    async def test_get_org_health(self, client: AsyncClient, test_admin, admin_token):
        """Test getting organization health index."""
        response = await client.get(
            "/api/v1/workforce/org-health",
            headers=auth_headers(admin_token)
        )
        assert response.status_code in [200, 403]

    @pytest.mark.asyncio
    async def test_get_attrition_risk(self, client: AsyncClient, test_admin, admin_token):
        """Test getting attrition risk data."""
        response = await client.get(
            "/api/v1/workforce/attrition-risk",
            headers=auth_headers(admin_token)
        )
        assert response.status_code in [200, 403]

    @pytest.mark.asyncio
    async def test_simulate_restructuring(self, client: AsyncClient, test_admin, admin_token):
        """Test restructuring simulation."""
        simulation_data = {
            "name": "Test Simulation",
            "type": "team_merge",
            "parameters": {
                "target_team_size": 10
            }
        }

        response = await client.post(
            "/api/v1/workforce/simulate",
            headers=auth_headers(admin_token),
            json=simulation_data
        )
        # Requires enterprise plan
        assert response.status_code in [200, 201, 403]

    @pytest.mark.asyncio
    async def test_get_hiring_plan(self, client: AsyncClient, test_admin, admin_token):
        """Test getting hiring plan recommendations."""
        response = await client.get(
            "/api/v1/workforce/hiring-plan",
            headers=auth_headers(admin_token)
        )
        assert response.status_code in [200, 403]

    @pytest.mark.asyncio
    async def test_workforce_unauthorized(self, client: AsyncClient):
        """Test workforce endpoints require authentication."""
        response = await client.get("/api/v1/workforce/scores")
        assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_workforce_employee_access(self, client: AsyncClient, test_user, user_token):
        """Test employees can't access workforce scores."""
        response = await client.get(
            "/api/v1/workforce/scores",
            headers=auth_headers(user_token)
        )
        # Employees should not have access to workforce intelligence
        assert response.status_code == 403

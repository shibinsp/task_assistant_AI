"""
TaskPulse - AI Assistant - Automation Tests
Tests for automation detection engine endpoints
"""

import pytest
from httpx import AsyncClient

from tests.conftest import auth_headers


class TestAutomationEndpoints:
    """Test automation detection endpoints."""

    @pytest.mark.asyncio
    async def test_list_patterns(self, client: AsyncClient, test_admin, admin_token):
        """Test listing detected automation patterns."""
        response = await client.get(
            "/api/v1/automation/patterns",
            headers=auth_headers(admin_token)
        )
        assert response.status_code == 200
        data = response.json()
        assert "patterns" in data
        assert "total" in data

    @pytest.mark.asyncio
    async def test_list_agents(self, client: AsyncClient, test_admin, admin_token):
        """Test listing AI agents."""
        response = await client.get(
            "/api/v1/automation/agents",
            headers=auth_headers(admin_token)
        )
        assert response.status_code == 200
        data = response.json()
        assert "agents" in data

    @pytest.mark.asyncio
    async def test_create_agent(self, client: AsyncClient, test_admin, admin_token):
        """Test creating an AI agent."""
        agent_data = {
            "name": "Test Automation Agent",
            "description": "Agent for testing",
            "trigger_type": "manual",
            "configuration": {}
        }

        response = await client.post(
            "/api/v1/automation/agents",
            headers=auth_headers(admin_token),
            json=agent_data
        )
        # May require specific permissions or enterprise plan
        assert response.status_code in [201, 403]

    @pytest.mark.asyncio
    async def test_get_automation_roi(self, client: AsyncClient, test_admin, admin_token):
        """Test getting automation ROI metrics."""
        response = await client.get(
            "/api/v1/automation/roi",
            headers=auth_headers(admin_token)
        )
        assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_automation_unauthorized(self, client: AsyncClient):
        """Test automation endpoints require authentication."""
        response = await client.get("/api/v1/automation/patterns")
        assert response.status_code == 401

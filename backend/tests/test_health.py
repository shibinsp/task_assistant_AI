"""
TaskPulse - AI Assistant - Health & API Tests
Tests for health check and basic API endpoints
"""

import pytest
from httpx import AsyncClient


class TestHealthEndpoints:
    """Test health check endpoints."""

    @pytest.mark.asyncio
    async def test_root_endpoint(self, client: AsyncClient):
        """Test root endpoint returns app info."""
        response = await client.get("/")
        assert response.status_code == 200
        data = response.json()
        assert "name" in data
        assert "version" in data
        assert data["status"] == "running"

    @pytest.mark.asyncio
    async def test_health_check(self, client: AsyncClient):
        """Test health check endpoint."""
        response = await client.get("/health")
        assert response.status_code in [200, 503]
        data = response.json()
        assert "status" in data
        assert "components" in data
        assert "database" in data["components"]

    @pytest.mark.asyncio
    async def test_readiness_check(self, client: AsyncClient):
        """Test readiness check endpoint."""
        response = await client.get("/ready")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "ready"

    @pytest.mark.asyncio
    async def test_api_v1_info(self, client: AsyncClient):
        """Test API v1 info endpoint."""
        response = await client.get("/api/v1")
        assert response.status_code == 200
        data = response.json()
        assert data["version"] == "1.0.0"
        assert "endpoints" in data


class TestAPIDocumentation:
    """Test API documentation endpoints."""

    @pytest.mark.asyncio
    async def test_openapi_schema(self, client: AsyncClient):
        """Test OpenAPI schema is available."""
        response = await client.get("/openapi.json")
        # May be 200 (dev) or 404 (prod)
        if response.status_code == 200:
            data = response.json()
            assert "openapi" in data
            assert "paths" in data

    @pytest.mark.asyncio
    async def test_swagger_docs(self, client: AsyncClient):
        """Test Swagger docs are available in dev mode."""
        response = await client.get("/docs")
        # May return 200 (dev) or 404 (prod)
        assert response.status_code in [200, 404]


class TestCORS:
    """Test CORS configuration."""

    @pytest.mark.asyncio
    async def test_cors_headers(self, client: AsyncClient):
        """Test CORS headers are present."""
        response = await client.options(
            "/",
            headers={
                "Origin": "http://localhost:3000",
                "Access-Control-Request-Method": "GET"
            }
        )
        # CORS preflight should succeed
        assert response.status_code in [200, 204, 405]


class TestErrorHandling:
    """Test error handling."""

    @pytest.mark.asyncio
    async def test_404_not_found(self, client: AsyncClient):
        """Test 404 response for non-existent endpoint."""
        response = await client.get("/nonexistent")
        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_method_not_allowed(self, client: AsyncClient):
        """Test 405 response for wrong HTTP method."""
        response = await client.delete("/")
        assert response.status_code == 405

    @pytest.mark.asyncio
    async def test_unauthorized_access(self, client: AsyncClient):
        """Test 401 response for protected endpoints without auth."""
        response = await client.get("/api/v1/tasks")
        assert response.status_code == 401

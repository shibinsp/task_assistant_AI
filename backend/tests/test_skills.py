"""
TaskPulse - AI Assistant - Skills Tests
Tests for skill management endpoints
"""

import pytest
from httpx import AsyncClient

from tests.conftest import auth_headers
from app.models.skill import Skill, UserSkill, SkillCategory
from app.utils.helpers import generate_uuid


class TestSkillEndpoints:
    """Test skill management endpoints."""

    @pytest.mark.asyncio
    async def test_get_skill_graph(
        self, client: AsyncClient, test_session, test_user, user_token, test_org
    ):
        """Test getting user skill graph."""
        # Create skills
        skill = Skill(
            id=generate_uuid(),
            org_id=test_org.id,
            name="Python",
            category=SkillCategory.TECHNICAL
        )
        test_session.add(skill)
        await test_session.flush()

        # Link skill to user
        user_skill = UserSkill(
            id=generate_uuid(),
            org_id=test_org.id,
            user_id=test_user.id,
            skill_id=skill.id,
            proficiency_level=7,
            confidence_score=0.85
        )
        test_session.add(user_skill)
        await test_session.commit()

        response = await client.get(
            f"/api/v1/skills/{test_user.id}/graph",
            headers=auth_headers(user_token)
        )
        assert response.status_code == 200
        data = response.json()
        assert "skills" in data
        assert len(data["skills"]) >= 1

    @pytest.mark.asyncio
    async def test_get_skill_velocity(
        self, client: AsyncClient, test_user, user_token
    ):
        """Test getting skill velocity metrics."""
        response = await client.get(
            f"/api/v1/skills/{test_user.id}/velocity",
            headers=auth_headers(user_token)
        )
        assert response.status_code == 200
        data = response.json()
        assert "velocity_metrics" in data

    @pytest.mark.asyncio
    async def test_get_team_skill_composition(
        self, client: AsyncClient, test_session, test_manager, manager_token, test_org
    ):
        """Test getting team skill composition."""
        response = await client.get(
            f"/api/v1/skills/team/test-team/composition",
            headers=auth_headers(manager_token)
        )
        assert response.status_code == 200
        data = response.json()
        assert "skills" in data

    @pytest.mark.asyncio
    async def test_get_skill_gaps(
        self, client: AsyncClient, test_user, user_token
    ):
        """Test getting skill gaps for user."""
        response = await client.get(
            f"/api/v1/skills/{test_user.id}/gaps",
            headers=auth_headers(user_token)
        )
        assert response.status_code == 200
        data = response.json()
        assert "gaps" in data

    @pytest.mark.asyncio
    async def test_get_learning_path(
        self, client: AsyncClient, test_user, user_token
    ):
        """Test getting learning path recommendations."""
        response = await client.get(
            f"/api/v1/skills/{test_user.id}/learning-path",
            headers=auth_headers(user_token)
        )
        assert response.status_code == 200
        data = response.json()
        assert "recommendations" in data

    @pytest.mark.asyncio
    async def test_get_self_sufficiency_index(
        self, client: AsyncClient, test_user, user_token
    ):
        """Test getting self-sufficiency index."""
        response = await client.get(
            f"/api/v1/skills/{test_user.id}/self-sufficiency",
            headers=auth_headers(user_token)
        )
        assert response.status_code == 200
        data = response.json()
        assert "index" in data or "self_sufficiency_score" in data

    @pytest.mark.asyncio
    async def test_update_skill_proficiency(
        self, client: AsyncClient, test_session, test_user, user_token, test_org
    ):
        """Test updating skill proficiency."""
        # Create skill and link
        skill = Skill(
            id=generate_uuid(),
            org_id=test_org.id,
            name="JavaScript",
            category=SkillCategory.TECHNICAL
        )
        test_session.add(skill)
        await test_session.flush()

        user_skill = UserSkill(
            id=generate_uuid(),
            org_id=test_org.id,
            user_id=test_user.id,
            skill_id=skill.id,
            proficiency_level=5
        )
        test_session.add(user_skill)
        await test_session.commit()

        response = await client.patch(
            f"/api/v1/skills/{test_user.id}/skills/{skill.id}",
            headers=auth_headers(user_token),
            json={"proficiency_level": 7}
        )
        assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_get_org_skill_matrix(
        self, client: AsyncClient, test_admin, admin_token
    ):
        """Test getting organization skill matrix."""
        response = await client.get(
            "/api/v1/skills/org/matrix",
            headers=auth_headers(admin_token)
        )
        assert response.status_code == 200
        data = response.json()
        assert "matrix" in data or "skills" in data

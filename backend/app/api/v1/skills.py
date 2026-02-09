"""
TaskPulse - AI Assistant - Skills API
Endpoints for employee skill tracking
"""

from typing import Optional, List
from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.user import User, UserRole
from app.models.skill import SkillCategory
from app.schemas.skill import (
    SkillCreate, SkillUpdate, SkillResponse, SkillListResponse,
    UserSkillCreate, UserSkillUpdate, UserSkillResponse,
    SkillGraphResponse, SkillVelocityResponse, TeamSkillComposition,
    SkillGapResponse, SkillGapSummary, LearningPathCreate, LearningPathResponse,
    SelfSufficiencyMetrics
)
from app.services.skill_service import SkillService
from app.api.v1.dependencies import (
    get_current_active_user, require_roles, get_pagination, PaginationParams
)
from app.core.permissions import Permission, has_permission
from app.core.exceptions import NotFoundException, ForbiddenException

router = APIRouter()


def get_skill_service(db: AsyncSession = Depends(get_db)) -> SkillService:
    return SkillService(db)


# ==================== Skill Catalog ====================

@router.get(
    "",
    response_model=SkillListResponse,
    summary="List skills",
    description="List skills in the organization catalog"
)
async def list_skills(
    pagination: PaginationParams = Depends(get_pagination),
    category: Optional[SkillCategory] = Query(None),
    search: Optional[str] = Query(None),
    current_user: User = Depends(get_current_active_user),
    service: SkillService = Depends(get_skill_service)
):
    """List skills in the catalog."""
    skills, total = await service.get_skills(
        org_id=current_user.org_id,
        category=category,
        search=search,
        skip=pagination.skip,
        limit=pagination.limit
    )
    return SkillListResponse(
        skills=[SkillResponse(
            id=s.id, org_id=s.org_id, name=s.name, description=s.description,
            category=s.category, aliases=s.aliases, related_skills=s.related_skills,
            org_average_level=s.org_average_level, is_active=s.is_active,
            created_at=s.created_at, updated_at=s.updated_at
        ) for s in skills],
        total=total, page=pagination.page, page_size=pagination.page_size
    )


@router.post(
    "",
    response_model=SkillResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create skill"
)
async def create_skill(
    skill_data: SkillCreate,
    current_user: User = Depends(require_roles(UserRole.SUPER_ADMIN, UserRole.ORG_ADMIN)),
    service: SkillService = Depends(get_skill_service)
):
    """Create a new skill in the catalog."""
    if not has_permission(current_user.role, Permission.SKILLS_CONFIGURE_PATHS):
        raise ForbiddenException("Not authorized")
    skill = await service.create_skill(current_user.org_id, skill_data)
    return SkillResponse(
        id=skill.id, org_id=skill.org_id, name=skill.name, description=skill.description,
        category=skill.category, aliases=skill.aliases, related_skills=skill.related_skills,
        org_average_level=skill.org_average_level, is_active=skill.is_active,
        created_at=skill.created_at, updated_at=skill.updated_at
    )


# ==================== User Skills ====================

@router.get(
    "/{user_id}/graph",
    response_model=SkillGraphResponse,
    summary="Get skill graph"
)
async def get_skill_graph(
    user_id: str,
    current_user: User = Depends(get_current_active_user),
    service: SkillService = Depends(get_skill_service)
):
    """Get user's skill graph."""
    can_view = (
        user_id == current_user.id or
        has_permission(current_user.role, Permission.SKILLS_READ) or
        has_permission(current_user.role, Permission.SKILLS_READ_TEAM)
    )
    if not can_view:
        raise ForbiddenException("Not authorized")
    result = await service.get_skill_graph(user_id, current_user.org_id)
    return SkillGraphResponse(**result)


@router.get(
    "/{user_id}/velocity",
    response_model=SkillVelocityResponse,
    summary="Get skill velocity"
)
async def get_skill_velocity(
    user_id: str,
    days: int = Query(30, ge=7, le=365),
    current_user: User = Depends(get_current_active_user),
    service: SkillService = Depends(get_skill_service)
):
    """Get user's skill velocity metrics."""
    can_view = (
        user_id == current_user.id or
        has_permission(current_user.role, Permission.SKILLS_READ)
    )
    if not can_view:
        raise ForbiddenException("Not authorized")
    result = await service.get_skill_velocity(user_id, current_user.org_id, days)
    return SkillVelocityResponse(**result)


@router.get(
    "/team/{team_id}/composition",
    response_model=TeamSkillComposition,
    summary="Get team composition"
)
async def get_team_composition(
    team_id: str,
    current_user: User = Depends(get_current_active_user),
    service: SkillService = Depends(get_skill_service)
):
    """Get team's skill composition."""
    if not has_permission(current_user.role, Permission.SKILLS_READ_TEAM):
        raise ForbiddenException("Not authorized")
    result = await service.get_team_composition(team_id, current_user.org_id)
    return TeamSkillComposition(**result)


@router.post(
    "/{user_id}/skills",
    response_model=UserSkillResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Add skill to user"
)
async def add_user_skill(
    user_id: str,
    skill_data: UserSkillCreate,
    current_user: User = Depends(get_current_active_user),
    service: SkillService = Depends(get_skill_service)
):
    """Add a skill to user's profile."""
    can_modify = (
        user_id == current_user.id or
        has_permission(current_user.role, Permission.SKILLS_CONFIGURE_PATHS)
    )
    if not can_modify:
        raise ForbiddenException("Not authorized")
    us = await service.add_user_skill(user_id, current_user.org_id, skill_data)
    return UserSkillResponse(
        id=us.id, user_id=us.user_id, skill_id=us.skill_id,
        skill_name=us.skill.name if us.skill else None,
        skill_category=us.skill.category if us.skill else None,
        level=us.level, confidence=us.confidence, trend=us.trend,
        last_demonstrated=us.last_demonstrated, demonstration_count=us.demonstration_count,
        source=us.source, is_certified=us.is_certified, level_history=us.level_history,
        created_at=us.created_at, updated_at=us.updated_at
    )


@router.get(
    "/{user_id}/skills",
    response_model=List[UserSkillResponse],
    summary="Get user skills"
)
async def get_user_skills(
    user_id: str,
    current_user: User = Depends(get_current_active_user),
    service: SkillService = Depends(get_skill_service)
):
    """Get user's skills."""
    can_view = (
        user_id == current_user.id or
        has_permission(current_user.role, Permission.SKILLS_READ)
    )
    if not can_view:
        raise ForbiddenException("Not authorized")
    skills = await service.get_user_skills(user_id, current_user.org_id)
    return [UserSkillResponse(
        id=us.id, user_id=us.user_id, skill_id=us.skill_id,
        skill_name=us.skill.name if us.skill else None,
        skill_category=us.skill.category if us.skill else None,
        level=us.level, confidence=us.confidence, trend=us.trend,
        last_demonstrated=us.last_demonstrated, demonstration_count=us.demonstration_count,
        source=us.source, is_certified=us.is_certified, level_history=us.level_history,
        created_at=us.created_at, updated_at=us.updated_at
    ) for us in skills]


# ==================== Skill Gaps ====================

@router.get(
    "/{user_id}/gaps",
    response_model=SkillGapSummary,
    summary="Get skill gaps"
)
async def get_skill_gaps(
    user_id: str,
    current_user: User = Depends(get_current_active_user),
    service: SkillService = Depends(get_skill_service)
):
    """Get user's skill gaps."""
    can_view = user_id == current_user.id or has_permission(current_user.role, Permission.SKILLS_READ)
    if not can_view:
        raise ForbiddenException("Not authorized")

    gaps = await service.get_user_skill_gaps(user_id, current_user.org_id)
    from app.models.skill import GapType

    return SkillGapSummary(
        user_id=user_id,
        total_gaps=len(gaps),
        critical_gaps=sum(1 for g in gaps if g.gap_type == GapType.CRITICAL),
        growth_gaps=sum(1 for g in gaps if g.gap_type == GapType.GROWTH),
        stretch_gaps=sum(1 for g in gaps if g.gap_type == GapType.STRETCH),
        gaps=[SkillGapResponse(
            id=g.id, user_id=g.user_id, skill_id=g.skill_id,
            skill_name=g.skill.name if g.skill else None,
            gap_type=g.gap_type, current_level=g.current_level, required_level=g.required_level,
            gap_size=g.gap_size, for_role=g.for_role, priority=g.priority,
            learning_resources=g.learning_resources, is_resolved=g.is_resolved,
            identified_at=g.identified_at
        ) for g in gaps]
    )


@router.post(
    "/{user_id}/gaps/analyze",
    response_model=SkillGapSummary,
    summary="Analyze skill gaps"
)
async def analyze_skill_gaps(
    user_id: str,
    target_role: Optional[str] = Query(None),
    current_user: User = Depends(get_current_active_user),
    service: SkillService = Depends(get_skill_service)
):
    """Analyze and identify skill gaps."""
    can_analyze = user_id == current_user.id or has_permission(current_user.role, Permission.SKILLS_CONFIGURE_PATHS)
    if not can_analyze:
        raise ForbiddenException("Not authorized")

    gaps = await service.identify_skill_gaps(user_id, current_user.org_id, target_role)
    from app.models.skill import GapType

    return SkillGapSummary(
        user_id=user_id,
        total_gaps=len(gaps),
        critical_gaps=sum(1 for g in gaps if g.gap_type == GapType.CRITICAL),
        growth_gaps=sum(1 for g in gaps if g.gap_type == GapType.GROWTH),
        stretch_gaps=sum(1 for g in gaps if g.gap_type == GapType.STRETCH),
        gaps=[SkillGapResponse(
            id=g.id, user_id=g.user_id, skill_id=g.skill_id,
            skill_name=None, gap_type=g.gap_type, current_level=g.current_level,
            required_level=g.required_level, gap_size=g.gap_size, for_role=g.for_role,
            priority=g.priority, learning_resources=g.learning_resources,
            is_resolved=g.is_resolved, identified_at=g.identified_at
        ) for g in gaps]
    )


# ==================== Learning Path ====================

@router.get(
    "/{user_id}/learning-path",
    response_model=List[LearningPathResponse],
    summary="Get learning paths"
)
async def get_learning_paths(
    user_id: str,
    active_only: bool = Query(True),
    current_user: User = Depends(get_current_active_user),
    service: SkillService = Depends(get_skill_service)
):
    """Get user's learning paths."""
    can_view = user_id == current_user.id or has_permission(current_user.role, Permission.SKILLS_READ)
    if not can_view:
        raise ForbiddenException("Not authorized")

    paths = await service.get_learning_paths(user_id, current_user.org_id, active_only)
    return [LearningPathResponse(
        id=p.id, user_id=p.user_id, title=p.title, description=p.description,
        target_role=p.target_role, skills=p.skills, milestones=p.milestones,
        progress_percentage=p.progress_percentage, started_at=p.started_at,
        target_completion=p.target_completion, completed_at=p.completed_at,
        is_active=p.is_active, is_ai_generated=p.is_ai_generated, created_at=p.created_at
    ) for p in paths]


@router.post(
    "/{user_id}/learning-path",
    response_model=LearningPathResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create learning path"
)
async def create_learning_path(
    user_id: str,
    path_data: LearningPathCreate,
    current_user: User = Depends(get_current_active_user),
    service: SkillService = Depends(get_skill_service)
):
    """Create a learning path."""
    can_create = user_id == current_user.id or has_permission(current_user.role, Permission.SKILLS_CONFIGURE_PATHS)
    if not can_create:
        raise ForbiddenException("Not authorized")

    path = await service.create_learning_path(user_id, current_user.org_id, path_data)
    return LearningPathResponse(
        id=path.id, user_id=path.user_id, title=path.title, description=path.description,
        target_role=path.target_role, skills=path.skills, milestones=path.milestones,
        progress_percentage=path.progress_percentage, started_at=path.started_at,
        target_completion=path.target_completion, completed_at=path.completed_at,
        is_active=path.is_active, is_ai_generated=path.is_ai_generated, created_at=path.created_at
    )


# ==================== Self-Sufficiency ====================

@router.get(
    "/{user_id}/self-sufficiency",
    response_model=SelfSufficiencyMetrics,
    summary="Get self-sufficiency"
)
async def get_self_sufficiency(
    user_id: str,
    current_user: User = Depends(get_current_active_user),
    service: SkillService = Depends(get_skill_service)
):
    """Get user's self-sufficiency metrics."""
    can_view = user_id == current_user.id or has_permission(current_user.role, Permission.SKILLS_READ)
    if not can_view:
        raise ForbiddenException("Not authorized")

    result = await service.get_self_sufficiency(user_id, current_user.org_id)
    return SelfSufficiencyMetrics(**result)

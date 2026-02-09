"""
TaskPulse - AI Assistant - Automation API
Pattern detection and AI agent management
"""

from typing import Optional, List
from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from datetime import datetime
import random

from app.database import get_db
from app.models.user import User, UserRole
from app.models.automation import (
    AutomationPattern, AIAgent, AgentRun,
    PatternStatus, AgentStatus
)
from app.api.v1.dependencies import get_current_active_user, require_roles, get_pagination, PaginationParams
from app.core.permissions import Permission, has_permission
from app.core.exceptions import NotFoundException, ForbiddenException
from app.utils.helpers import generate_uuid
from pydantic import BaseModel, Field

router = APIRouter()


# Schemas
class PatternResponse(BaseModel):
    id: str
    name: str
    description: Optional[str]
    pattern_type: Optional[str]
    status: PatternStatus
    frequency_per_week: Optional[float]
    consistency_score: Optional[float]
    users_affected: int
    estimated_hours_saved_weekly: Optional[float]
    implementation_complexity: int
    created_at: datetime

    class Config:
        from_attributes = True


class AgentCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=200)
    description: Optional[str] = None
    pattern_id: Optional[str] = None
    config: dict = Field(default_factory=dict)


class AgentResponse(BaseModel):
    id: str
    name: str
    description: Optional[str]
    status: AgentStatus
    pattern_id: Optional[str]
    shadow_match_rate: Optional[float]
    shadow_runs: int
    total_runs: int
    successful_runs: int
    hours_saved_total: float
    last_run_at: Optional[datetime]
    created_at: datetime

    class Config:
        from_attributes = True


class AgentStatusUpdate(BaseModel):
    status: AgentStatus


class ShadowReport(BaseModel):
    agent_id: str
    shadow_period_days: int
    total_runs: int
    match_rate: float
    mismatches: List[dict]
    recommendation: str


class ROIDashboard(BaseModel):
    total_agents: int
    active_agents: int
    total_hours_saved: float
    total_cost_savings: float
    patterns_detected: int
    patterns_implemented: int


# Endpoints
@router.get(
    "/patterns",
    response_model=List[PatternResponse],
    summary="Get automation patterns"
)
async def get_patterns(
    status_filter: Optional[PatternStatus] = Query(None, alias="status"),
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """Get detected automation patterns."""
    if not has_permission(current_user.role, Permission.AUTOMATION_VIEW):
        raise ForbiddenException("Not authorized")

    query = select(AutomationPattern).where(AutomationPattern.org_id == current_user.org_id)
    if status_filter:
        query = query.where(AutomationPattern.status == status_filter)

    result = await db.execute(query.order_by(AutomationPattern.created_at.desc()))
    patterns = result.scalars().all()

    return [PatternResponse(
        id=p.id, name=p.name, description=p.description, pattern_type=p.pattern_type,
        status=p.status, frequency_per_week=p.frequency_per_week,
        consistency_score=p.consistency_score, users_affected=p.users_affected,
        estimated_hours_saved_weekly=p.estimated_hours_saved_weekly,
        implementation_complexity=p.implementation_complexity, created_at=p.created_at
    ) for p in patterns]


@router.post(
    "/patterns/{pattern_id}/accept",
    response_model=PatternResponse,
    summary="Accept automation pattern"
)
async def accept_pattern(
    pattern_id: str,
    current_user: User = Depends(require_roles(
        UserRole.SUPER_ADMIN, UserRole.ORG_ADMIN, UserRole.MANAGER
    )),
    db: AsyncSession = Depends(get_db)
):
    """Accept an automation pattern suggestion."""
    if not has_permission(current_user.role, Permission.AUTOMATION_APPROVE):
        raise ForbiddenException("Not authorized")

    result = await db.execute(
        select(AutomationPattern).where(
            AutomationPattern.id == pattern_id,
            AutomationPattern.org_id == current_user.org_id
        )
    )
    pattern = result.scalar_one_or_none()
    if not pattern:
        raise NotFoundException("Pattern", pattern_id)

    pattern.status = PatternStatus.ACCEPTED
    pattern.accepted_by = current_user.id
    pattern.accepted_at = datetime.utcnow()
    await db.flush()
    await db.refresh(pattern)

    return PatternResponse(
        id=pattern.id, name=pattern.name, description=pattern.description,
        pattern_type=pattern.pattern_type, status=pattern.status,
        frequency_per_week=pattern.frequency_per_week, consistency_score=pattern.consistency_score,
        users_affected=pattern.users_affected, estimated_hours_saved_weekly=pattern.estimated_hours_saved_weekly,
        implementation_complexity=pattern.implementation_complexity, created_at=pattern.created_at
    )


@router.post(
    "/agents",
    response_model=AgentResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create AI agent"
)
async def create_agent(
    agent_data: AgentCreate,
    current_user: User = Depends(require_roles(
        UserRole.SUPER_ADMIN, UserRole.ORG_ADMIN, UserRole.MANAGER
    )),
    db: AsyncSession = Depends(get_db)
):
    """Create a new AI agent."""
    if not has_permission(current_user.role, Permission.AUTOMATION_CREATE_AGENTS):
        raise ForbiddenException("Not authorized")

    agent = AIAgent(
        id=generate_uuid(),
        org_id=current_user.org_id,
        name=agent_data.name,
        description=agent_data.description,
        pattern_id=agent_data.pattern_id,
        created_by=current_user.id,
        status=AgentStatus.CREATED
    )
    agent.config_json = str(agent_data.config)

    db.add(agent)
    await db.flush()
    await db.refresh(agent)

    return AgentResponse(
        id=agent.id, name=agent.name, description=agent.description,
        status=agent.status, pattern_id=agent.pattern_id,
        shadow_match_rate=agent.shadow_match_rate, shadow_runs=agent.shadow_runs,
        total_runs=agent.total_runs, successful_runs=agent.successful_runs,
        hours_saved_total=agent.hours_saved_total, last_run_at=agent.last_run_at,
        created_at=agent.created_at
    )


@router.get(
    "/agents",
    response_model=List[AgentResponse],
    summary="List AI agents"
)
async def list_agents(
    status_filter: Optional[AgentStatus] = Query(None, alias="status"),
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """List AI agents."""
    if not has_permission(current_user.role, Permission.AUTOMATION_VIEW):
        raise ForbiddenException("Not authorized")

    query = select(AIAgent).where(AIAgent.org_id == current_user.org_id)
    if status_filter:
        query = query.where(AIAgent.status == status_filter)

    result = await db.execute(query.order_by(AIAgent.created_at.desc()))
    agents = result.scalars().all()

    return [AgentResponse(
        id=a.id, name=a.name, description=a.description, status=a.status,
        pattern_id=a.pattern_id, shadow_match_rate=a.shadow_match_rate,
        shadow_runs=a.shadow_runs, total_runs=a.total_runs,
        successful_runs=a.successful_runs, hours_saved_total=a.hours_saved_total,
        last_run_at=a.last_run_at, created_at=a.created_at
    ) for a in agents]


@router.get(
    "/agents/{agent_id}",
    response_model=AgentResponse,
    summary="Get AI agent"
)
async def get_agent(
    agent_id: str,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """Get AI agent details."""
    result = await db.execute(
        select(AIAgent).where(AIAgent.id == agent_id, AIAgent.org_id == current_user.org_id)
    )
    agent = result.scalar_one_or_none()
    if not agent:
        raise NotFoundException("Agent", agent_id)

    return AgentResponse(
        id=agent.id, name=agent.name, description=agent.description,
        status=agent.status, pattern_id=agent.pattern_id,
        shadow_match_rate=agent.shadow_match_rate, shadow_runs=agent.shadow_runs,
        total_runs=agent.total_runs, successful_runs=agent.successful_runs,
        hours_saved_total=agent.hours_saved_total, last_run_at=agent.last_run_at,
        created_at=agent.created_at
    )


@router.patch(
    "/agents/{agent_id}/status",
    response_model=AgentResponse,
    summary="Update agent status"
)
async def update_agent_status(
    agent_id: str,
    status_data: AgentStatusUpdate,
    current_user: User = Depends(require_roles(
        UserRole.SUPER_ADMIN, UserRole.ORG_ADMIN, UserRole.MANAGER
    )),
    db: AsyncSession = Depends(get_db)
):
    """Update AI agent status."""
    if not has_permission(current_user.role, Permission.AUTOMATION_MANAGE_AGENTS):
        raise ForbiddenException("Not authorized")

    result = await db.execute(
        select(AIAgent).where(AIAgent.id == agent_id, AIAgent.org_id == current_user.org_id)
    )
    agent = result.scalar_one_or_none()
    if not agent:
        raise NotFoundException("Agent", agent_id)

    old_status = agent.status
    agent.status = status_data.status

    # Track shadow mode start
    if status_data.status == AgentStatus.SHADOW and old_status != AgentStatus.SHADOW:
        agent.shadow_started_at = datetime.utcnow()

    # Track approval for live
    if status_data.status == AgentStatus.LIVE:
        agent.approved_by = current_user.id
        agent.approved_at = datetime.utcnow()

    await db.flush()
    await db.refresh(agent)

    return AgentResponse(
        id=agent.id, name=agent.name, description=agent.description,
        status=agent.status, pattern_id=agent.pattern_id,
        shadow_match_rate=agent.shadow_match_rate, shadow_runs=agent.shadow_runs,
        total_runs=agent.total_runs, successful_runs=agent.successful_runs,
        hours_saved_total=agent.hours_saved_total, last_run_at=agent.last_run_at,
        created_at=agent.created_at
    )


@router.get(
    "/agents/{agent_id}/shadow-report",
    response_model=ShadowReport,
    summary="Get shadow mode report"
)
async def get_shadow_report(
    agent_id: str,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """Get shadow mode validation report."""
    result = await db.execute(
        select(AIAgent).where(AIAgent.id == agent_id, AIAgent.org_id == current_user.org_id)
    )
    agent = result.scalar_one_or_none()
    if not agent:
        raise NotFoundException("Agent", agent_id)

    # Mock shadow report
    match_rate = agent.shadow_match_rate or random.uniform(0.85, 0.98)
    return ShadowReport(
        agent_id=agent_id,
        shadow_period_days=14,
        total_runs=agent.shadow_runs or 50,
        match_rate=match_rate,
        mismatches=[
            {"run_id": "r1", "reason": "Different output format", "severity": "low"},
            {"run_id": "r2", "reason": "Timing difference", "severity": "low"}
        ],
        recommendation="Ready for supervised mode" if match_rate > 0.9 else "Continue shadow mode"
    )


@router.get(
    "/roi",
    response_model=ROIDashboard,
    summary="Get automation ROI"
)
async def get_roi_dashboard(
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """Get automation ROI dashboard."""
    if not has_permission(current_user.role, Permission.AUTOMATION_VIEW):
        raise ForbiddenException("Not authorized")

    # Aggregate stats
    agent_count = await db.execute(
        select(func.count()).select_from(AIAgent).where(AIAgent.org_id == current_user.org_id)
    )
    total_agents = agent_count.scalar() or 0

    active_count = await db.execute(
        select(func.count()).select_from(AIAgent).where(
            AIAgent.org_id == current_user.org_id,
            AIAgent.status == AgentStatus.LIVE
        )
    )
    active_agents = active_count.scalar() or 0

    hours_saved = await db.execute(
        select(func.sum(AIAgent.hours_saved_total)).where(AIAgent.org_id == current_user.org_id)
    )
    total_hours = hours_saved.scalar() or 0

    pattern_count = await db.execute(
        select(func.count()).select_from(AutomationPattern).where(
            AutomationPattern.org_id == current_user.org_id
        )
    )
    patterns_detected = pattern_count.scalar() or 0

    implemented = await db.execute(
        select(func.count()).select_from(AutomationPattern).where(
            AutomationPattern.org_id == current_user.org_id,
            AutomationPattern.status == PatternStatus.IMPLEMENTED
        )
    )
    patterns_implemented = implemented.scalar() or 0

    return ROIDashboard(
        total_agents=total_agents,
        active_agents=active_agents,
        total_hours_saved=total_hours,
        total_cost_savings=total_hours * 50,  # Mock hourly rate
        patterns_detected=patterns_detected,
        patterns_implemented=patterns_implemented
    )

"""
TaskPulse - AI Assistant - Automation API
Pattern detection, AI agent management, and execution engine
"""

from typing import Optional, List
from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from datetime import datetime

from app.database import get_db
from app.models.user import User, UserRole
from app.models.automation import (
    AutomationPattern, AIAgent, AgentRun,
    PatternStatus, AgentStatus
)
from app.api.v1.dependencies import get_current_active_user, require_roles, get_pagination, PaginationParams
from app.core.permissions import Permission, has_permission
from app.core.exceptions import NotFoundException, ForbiddenException, ValidationException
from app.utils.helpers import generate_uuid
from pydantic import BaseModel, Field

router = APIRouter()


# ==================== Schemas ====================

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


class ManualTriggerRequest(BaseModel):
    trigger_data: dict = Field(default_factory=dict)


class AgentRunResponse(BaseModel):
    id: str
    agent_id: str
    status: str
    started_at: datetime
    completed_at: Optional[datetime]
    execution_time_ms: Optional[int]
    is_shadow: bool
    output: dict
    error_message: Optional[str]


class ROIDashboard(BaseModel):
    total_agents: int
    active_agents: int
    total_hours_saved: float
    total_cost_savings: float
    patterns_detected: int
    patterns_implemented: int


# ==================== Pattern Endpoints ====================

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


# ==================== Agent CRUD Endpoints ====================

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
    agent.config = agent_data.config

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

    # Track approval and live start
    if status_data.status == AgentStatus.LIVE:
        agent.approved_by = current_user.id
        agent.approved_at = datetime.utcnow()
        agent.live_started_at = datetime.utcnow()

    await db.flush()
    await db.refresh(agent)

    # Register/unregister cron jobs based on status change
    from app.services.automation_scheduler import register_agent_cron, unregister_agent_cron
    if status_data.status in (AgentStatus.SHADOW, AgentStatus.LIVE):
        await register_agent_cron(agent)
    elif status_data.status in (AgentStatus.PAUSED, AgentStatus.RETIRED):
        await unregister_agent_cron(agent.id)

    return AgentResponse(
        id=agent.id, name=agent.name, description=agent.description,
        status=agent.status, pattern_id=agent.pattern_id,
        shadow_match_rate=agent.shadow_match_rate, shadow_runs=agent.shadow_runs,
        total_runs=agent.total_runs, successful_runs=agent.successful_runs,
        hours_saved_total=agent.hours_saved_total, last_run_at=agent.last_run_at,
        created_at=agent.created_at
    )


# ==================== Execution Endpoints ====================

@router.post(
    "/agents/{agent_id}/trigger",
    response_model=AgentRunResponse,
    summary="Manually trigger an agent"
)
async def trigger_agent(
    agent_id: str,
    trigger_request: ManualTriggerRequest,
    current_user: User = Depends(require_roles(
        UserRole.SUPER_ADMIN, UserRole.ORG_ADMIN, UserRole.MANAGER
    )),
    db: AsyncSession = Depends(get_db)
):
    """Manually trigger an automation agent execution."""
    if not has_permission(current_user.role, Permission.AUTOMATION_MANAGE_AGENTS):
        raise ForbiddenException("Not authorized")

    result = await db.execute(
        select(AIAgent).where(AIAgent.id == agent_id, AIAgent.org_id == current_user.org_id)
    )
    agent = result.scalar_one_or_none()
    if not agent:
        raise NotFoundException("Agent", agent_id)

    if agent.status not in (AgentStatus.LIVE, AgentStatus.SHADOW, AgentStatus.SUPERVISED):
        raise ValidationException(
            f"Agent must be in LIVE, SHADOW, or SUPERVISED status to trigger. Current: {agent.status.value}"
        )

    from app.services.automation_executor import AutomationExecutor
    executor = AutomationExecutor(db)

    trigger_data = {
        "trigger_type": "manual",
        "triggered_by": current_user.id,
        "triggered_at": datetime.utcnow().isoformat(),
        **trigger_request.trigger_data,
    }

    is_shadow = (agent.status == AgentStatus.SHADOW)
    run = await executor.execute_agent(agent, trigger_data, is_shadow=is_shadow)

    return AgentRunResponse(
        id=run.id,
        agent_id=run.agent_id,
        status=run.status,
        started_at=run.started_at,
        completed_at=run.completed_at,
        execution_time_ms=run.execution_time_ms,
        is_shadow=run.is_shadow,
        output=run.output_data,
        error_message=run.error_message,
    )


@router.get(
    "/agents/{agent_id}/runs",
    response_model=List[AgentRunResponse],
    summary="Get agent execution history"
)
async def get_agent_runs(
    agent_id: str,
    is_shadow: Optional[bool] = Query(None),
    status_filter: Optional[str] = Query(None, alias="status"),
    limit: int = Query(50, le=100),
    offset: int = Query(0, ge=0),
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """Get execution history for an agent."""
    if not has_permission(current_user.role, Permission.AUTOMATION_VIEW):
        raise ForbiddenException("Not authorized")

    # Verify agent exists and belongs to org
    agent_result = await db.execute(
        select(AIAgent).where(AIAgent.id == agent_id, AIAgent.org_id == current_user.org_id)
    )
    if not agent_result.scalar_one_or_none():
        raise NotFoundException("Agent", agent_id)

    query = select(AgentRun).where(AgentRun.agent_id == agent_id)

    if is_shadow is not None:
        query = query.where(AgentRun.is_shadow == is_shadow)
    if status_filter:
        query = query.where(AgentRun.status == status_filter)

    query = query.order_by(AgentRun.started_at.desc()).offset(offset).limit(limit)
    result = await db.execute(query)
    runs = result.scalars().all()

    return [AgentRunResponse(
        id=r.id,
        agent_id=r.agent_id,
        status=r.status,
        started_at=r.started_at,
        completed_at=r.completed_at,
        execution_time_ms=r.execution_time_ms,
        is_shadow=r.is_shadow,
        output=r.output_data,
        error_message=r.error_message,
    ) for r in runs]


@router.get(
    "/agents/{agent_id}/shadow-report",
    summary="Get shadow mode report"
)
async def get_shadow_report(
    agent_id: str,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """Get shadow mode validation report from real execution data."""
    from app.services.automation_service import AutomationService
    service = AutomationService(db)
    report = await service.get_shadow_report(agent_id, current_user.org_id)
    if "error" in report:
        raise NotFoundException("Agent", agent_id)
    return report


# ==================== ROI Dashboard ====================

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
        total_cost_savings=total_hours * 50,
        patterns_detected=patterns_detected,
        patterns_implemented=patterns_implemented
    )

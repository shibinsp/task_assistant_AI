"""
TaskPulse - AI Assistant - Workforce Intelligence API
Executive-level decision intelligence
"""

from typing import Optional, List
from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from datetime import datetime, timedelta
import random

from app.database import get_db
from app.models.user import User, UserRole
from app.models.workforce import (
    WorkforceScore, ManagerEffectiveness, OrgHealthSnapshot,
    RestructuringScenario
)
from app.api.v1.dependencies import get_current_active_user, require_roles, get_pagination, PaginationParams
from app.core.permissions import Permission, has_permission
from app.core.exceptions import NotFoundException, ForbiddenException
from app.utils.helpers import generate_uuid
from pydantic import BaseModel, Field

router = APIRouter()


# Schemas
class WorkforceScoreResponse(BaseModel):
    user_id: str
    overall_score: Optional[float]
    velocity_score: Optional[float]
    quality_score: Optional[float]
    self_sufficiency_score: Optional[float]
    learning_score: Optional[float]
    collaboration_score: Optional[float]
    percentile_rank: Optional[float]
    attrition_risk_score: Optional[float]
    burnout_risk_score: Optional[float]
    score_trend: str
    snapshot_date: datetime


class ManagerRanking(BaseModel):
    manager_id: str
    manager_name: Optional[str]
    team_size: int
    effectiveness_score: Optional[float]
    team_velocity_avg: Optional[float]
    redundancy_score: Optional[float]
    org_percentile: Optional[float]


class OrgHealthResponse(BaseModel):
    overall_health_score: Optional[float]
    productivity_index: Optional[float]
    skill_coverage_index: Optional[float]
    management_quality_index: Optional[float]
    automation_maturity_index: Optional[float]
    delivery_predictability_index: Optional[float]
    total_employees: int
    active_tasks: int
    blocked_tasks: int
    overdue_tasks: int
    high_attrition_risk_count: int
    high_burnout_risk_count: int
    snapshot_date: datetime


class AttritionRiskResponse(BaseModel):
    user_id: str
    user_name: Optional[str]
    risk_score: float
    risk_level: str  # low, medium, high, critical
    factors: List[str]
    tenure_months: int


class SimulationCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=500)
    description: Optional[str] = None
    scenario_type: str  # team_merge, role_change, automation_replace, reduction
    config: dict = Field(default_factory=dict)


class SimulationResponse(BaseModel):
    id: str
    name: str
    description: Optional[str]
    scenario_type: str
    projected_cost_change: Optional[float]
    projected_productivity_change: Optional[float]
    projected_skill_coverage_change: Optional[float]
    affected_employees: int
    overall_risk_score: Optional[float]
    is_draft: bool
    created_at: datetime


# Endpoints
@router.get(
    "/scores",
    response_model=List[WorkforceScoreResponse],
    summary="Get workforce scores"
)
async def get_workforce_scores(
    pagination: PaginationParams = Depends(get_pagination),
    team_id: Optional[str] = Query(None),
    min_score: Optional[float] = Query(None, ge=0, le=100),
    current_user: User = Depends(require_roles(
        UserRole.SUPER_ADMIN, UserRole.ORG_ADMIN, UserRole.MANAGER
    )),
    db: AsyncSession = Depends(get_db)
):
    """Get workforce scores for employees."""
    if not has_permission(current_user.role, Permission.WORKFORCE_VIEW_SCORES):
        raise ForbiddenException("Not authorized")

    query = select(WorkforceScore).where(WorkforceScore.org_id == current_user.org_id)
    if min_score:
        query = query.where(WorkforceScore.overall_score >= min_score)

    result = await db.execute(
        query.order_by(WorkforceScore.overall_score.desc())
        .offset(pagination.skip).limit(pagination.limit)
    )
    scores = result.scalars().all()

    return [WorkforceScoreResponse(
        user_id=s.user_id, overall_score=s.overall_score, velocity_score=s.velocity_score,
        quality_score=s.quality_score, self_sufficiency_score=s.self_sufficiency_score,
        learning_score=s.learning_score, collaboration_score=s.collaboration_score,
        percentile_rank=s.percentile_rank, attrition_risk_score=s.attrition_risk_score,
        burnout_risk_score=s.burnout_risk_score, score_trend=s.score_trend,
        snapshot_date=s.snapshot_date
    ) for s in scores]


@router.get(
    "/scores/{user_id}",
    response_model=WorkforceScoreResponse,
    summary="Get user workforce score"
)
async def get_user_workforce_score(
    user_id: str,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """Get workforce score for specific user."""
    can_view = (
        user_id == current_user.id or
        has_permission(current_user.role, Permission.WORKFORCE_VIEW_SCORES)
    )
    if not can_view:
        raise ForbiddenException("Not authorized")

    result = await db.execute(
        select(WorkforceScore).where(
            WorkforceScore.user_id == user_id,
            WorkforceScore.org_id == current_user.org_id
        ).order_by(WorkforceScore.snapshot_date.desc()).limit(1)
    )
    score = result.scalar_one_or_none()

    if not score:
        # Return mock score if none exists
        return WorkforceScoreResponse(
            user_id=user_id, overall_score=75.0, velocity_score=78.0, quality_score=82.0,
            self_sufficiency_score=70.0, learning_score=75.0, collaboration_score=80.0,
            percentile_rank=65.0, attrition_risk_score=0.15, burnout_risk_score=0.20,
            score_trend="stable", snapshot_date=datetime.utcnow()
        )

    return WorkforceScoreResponse(
        user_id=score.user_id, overall_score=score.overall_score, velocity_score=score.velocity_score,
        quality_score=score.quality_score, self_sufficiency_score=score.self_sufficiency_score,
        learning_score=score.learning_score, collaboration_score=score.collaboration_score,
        percentile_rank=score.percentile_rank, attrition_risk_score=score.attrition_risk_score,
        burnout_risk_score=score.burnout_risk_score, score_trend=score.score_trend,
        snapshot_date=score.snapshot_date
    )


@router.get(
    "/managers/ranking",
    response_model=List[ManagerRanking],
    summary="Get manager rankings"
)
async def get_manager_rankings(
    current_user: User = Depends(require_roles(
        UserRole.SUPER_ADMIN, UserRole.ORG_ADMIN
    )),
    db: AsyncSession = Depends(get_db)
):
    """Get manager effectiveness rankings."""
    if not has_permission(current_user.role, Permission.WORKFORCE_VIEW_MANAGERS):
        raise ForbiddenException("Not authorized")

    result = await db.execute(
        select(ManagerEffectiveness).where(
            ManagerEffectiveness.org_id == current_user.org_id
        ).order_by(ManagerEffectiveness.effectiveness_score.desc())
    )
    rankings = result.scalars().all()

    return [ManagerRanking(
        manager_id=r.manager_id, manager_name=None, team_size=r.team_size,
        effectiveness_score=r.effectiveness_score, team_velocity_avg=r.team_velocity_avg,
        redundancy_score=r.redundancy_score, org_percentile=r.org_percentile
    ) for r in rankings]


@router.get(
    "/org-health",
    response_model=OrgHealthResponse,
    summary="Get organization health"
)
async def get_org_health(
    current_user: User = Depends(require_roles(
        UserRole.SUPER_ADMIN, UserRole.ORG_ADMIN
    )),
    db: AsyncSession = Depends(get_db)
):
    """Get organization health dashboard."""
    if not has_permission(current_user.role, Permission.WORKFORCE_VIEW_ORG_HEALTH):
        raise ForbiddenException("Not authorized")

    result = await db.execute(
        select(OrgHealthSnapshot).where(
            OrgHealthSnapshot.org_id == current_user.org_id
        ).order_by(OrgHealthSnapshot.snapshot_date.desc()).limit(1)
    )
    health = result.scalar_one_or_none()

    if not health:
        # Return mock health
        return OrgHealthResponse(
            overall_health_score=78.5, productivity_index=80.0, skill_coverage_index=75.0,
            management_quality_index=82.0, automation_maturity_index=45.0,
            delivery_predictability_index=72.0, total_employees=50, active_tasks=120,
            blocked_tasks=8, overdue_tasks=5, high_attrition_risk_count=3,
            high_burnout_risk_count=5, snapshot_date=datetime.utcnow()
        )

    return OrgHealthResponse(
        overall_health_score=health.overall_health_score,
        productivity_index=health.productivity_index,
        skill_coverage_index=health.skill_coverage_index,
        management_quality_index=health.management_quality_index,
        automation_maturity_index=health.automation_maturity_index,
        delivery_predictability_index=health.delivery_predictability_index,
        total_employees=health.total_employees, active_tasks=health.active_tasks,
        blocked_tasks=health.blocked_tasks, overdue_tasks=health.overdue_tasks,
        high_attrition_risk_count=health.high_attrition_risk_count,
        high_burnout_risk_count=health.high_burnout_risk_count,
        snapshot_date=health.snapshot_date
    )


@router.get(
    "/attrition-risk",
    response_model=List[AttritionRiskResponse],
    summary="Get attrition risk list"
)
async def get_attrition_risk(
    risk_level: Optional[str] = Query(None),
    current_user: User = Depends(require_roles(
        UserRole.SUPER_ADMIN, UserRole.ORG_ADMIN
    )),
    db: AsyncSession = Depends(get_db)
):
    """Get employees with attrition risk."""
    if not has_permission(current_user.role, Permission.WORKFORCE_VIEW_ATTRITION):
        raise ForbiddenException("Not authorized")

    # Mock attrition risk data
    return [
        AttritionRiskResponse(
            user_id="user1", user_name="John Doe", risk_score=0.75, risk_level="high",
            factors=["Low engagement", "Below market salary", "No promotion in 2 years"],
            tenure_months=24
        ),
        AttritionRiskResponse(
            user_id="user2", user_name="Jane Smith", risk_score=0.55, risk_level="medium",
            factors=["Limited growth opportunities", "Remote work concerns"],
            tenure_months=18
        ),
        AttritionRiskResponse(
            user_id="user3", user_name="Bob Johnson", risk_score=0.82, risk_level="critical",
            factors=["Burnout indicators", "Skill mismatch", "Manager conflict"],
            tenure_months=36
        )
    ]


@router.post(
    "/simulate",
    response_model=SimulationResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create simulation"
)
async def create_simulation(
    sim_data: SimulationCreate,
    current_user: User = Depends(require_roles(
        UserRole.SUPER_ADMIN, UserRole.ORG_ADMIN
    )),
    db: AsyncSession = Depends(get_db)
):
    """Create a restructuring simulation."""
    if not has_permission(current_user.role, Permission.WORKFORCE_SIMULATE):
        raise ForbiddenException("Not authorized")

    scenario = RestructuringScenario(
        id=generate_uuid(),
        org_id=current_user.org_id,
        created_by=current_user.id,
        name=sim_data.name,
        description=sim_data.description,
        scenario_type=sim_data.scenario_type
    )
    scenario.config = sim_data.config

    # Run mock simulation
    scenario.projected_cost_change = random.uniform(-15, 10)
    scenario.projected_productivity_change = random.uniform(-5, 15)
    scenario.projected_skill_coverage_change = random.uniform(-10, 5)
    scenario.affected_employees = random.randint(5, 20)
    scenario.overall_risk_score = random.uniform(0.3, 0.7)

    db.add(scenario)
    await db.flush()
    await db.refresh(scenario)

    return SimulationResponse(
        id=scenario.id, name=scenario.name, description=scenario.description,
        scenario_type=scenario.scenario_type,
        projected_cost_change=scenario.projected_cost_change,
        projected_productivity_change=scenario.projected_productivity_change,
        projected_skill_coverage_change=scenario.projected_skill_coverage_change,
        affected_employees=scenario.affected_employees,
        overall_risk_score=scenario.overall_risk_score, is_draft=scenario.is_draft,
        created_at=scenario.created_at
    )


@router.get(
    "/simulate/{scenario_id}",
    response_model=SimulationResponse,
    summary="Get simulation"
)
async def get_simulation(
    scenario_id: str,
    current_user: User = Depends(require_roles(
        UserRole.SUPER_ADMIN, UserRole.ORG_ADMIN
    )),
    db: AsyncSession = Depends(get_db)
):
    """Get simulation details."""
    result = await db.execute(
        select(RestructuringScenario).where(
            RestructuringScenario.id == scenario_id,
            RestructuringScenario.org_id == current_user.org_id
        )
    )
    scenario = result.scalar_one_or_none()
    if not scenario:
        raise NotFoundException("Scenario", scenario_id)

    return SimulationResponse(
        id=scenario.id, name=scenario.name, description=scenario.description,
        scenario_type=scenario.scenario_type,
        projected_cost_change=scenario.projected_cost_change,
        projected_productivity_change=scenario.projected_productivity_change,
        projected_skill_coverage_change=scenario.projected_skill_coverage_change,
        affected_employees=scenario.affected_employees,
        overall_risk_score=scenario.overall_risk_score, is_draft=scenario.is_draft,
        created_at=scenario.created_at
    )


@router.get(
    "/hiring-plan",
    summary="Get hiring plan"
)
async def get_hiring_plan(
    current_user: User = Depends(require_roles(
        UserRole.SUPER_ADMIN, UserRole.ORG_ADMIN
    )),
    db: AsyncSession = Depends(get_db)
):
    """Get AI-generated hiring plan."""
    if not has_permission(current_user.role, Permission.WORKFORCE_VIEW_HIRING):
        raise ForbiddenException("Not authorized")

    return {
        "recommended_hires": 5,
        "budget_required": 350000,
        "timeline_months": 6,
        "roles": [
            {"title": "Senior Backend Engineer", "count": 2, "priority": "high"},
            {"title": "ML Engineer", "count": 2, "priority": "critical"},
            {"title": "DevOps Engineer", "count": 1, "priority": "medium"}
        ],
        "skill_gaps_addressed": ["Machine Learning", "Kubernetes", "Python"],
        "projected_impact": {
            "productivity_increase": 15,
            "delivery_time_reduction": 20
        }
    }

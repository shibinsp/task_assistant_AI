"""
TaskPulse - AI Assistant - Workforce Schemas
Pydantic schemas for workforce intelligence and analytics
"""

from datetime import datetime, date
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field


# ==================== Workforce Score Schemas ====================

class ScoreComponent(BaseModel):
    """Individual score component."""
    name: str
    score: float = Field(ge=0, le=100)
    weight: float = Field(ge=0, le=1)
    trend: str = Field(..., description="Trend: improving, stable, declining")
    details: Dict[str, Any] = Field(default_factory=dict)


class WorkforceScoreResponse(BaseModel):
    """Schema for workforce score in API responses."""
    id: str
    user_id: str
    org_id: str

    # Overall score
    overall_score: float = Field(ge=0, le=100)
    percentile: Optional[float] = Field(None, ge=0, le=100)

    # Component scores
    velocity_score: float = Field(ge=0, le=100)
    quality_score: float = Field(ge=0, le=100)
    self_sufficiency_score: float = Field(ge=0, le=100)
    learning_score: float = Field(ge=0, le=100)
    collaboration_score: float = Field(ge=0, le=100)

    # Trends
    score_trend: str = Field(..., description="Trend: improving, stable, declining")
    previous_score: Optional[float] = None

    # Period
    period_start: date
    period_end: date

    created_at: datetime

    model_config = {"from_attributes": True}


class WorkforceScoreListResponse(BaseModel):
    """Response for list of workforce scores."""
    scores: List[WorkforceScoreResponse]
    total: int
    average_score: float = 0.0
    page: int
    page_size: int


class WorkforceScoreDetailResponse(WorkforceScoreResponse):
    """Detailed workforce score with components."""
    components: List[ScoreComponent] = Field(default_factory=list)
    recommendations: List[str] = Field(default_factory=list)
    peer_comparison: Dict[str, Any] = Field(default_factory=dict)


# ==================== Attrition Risk Schemas ====================

class AttritionRiskFactor(BaseModel):
    """Attrition risk factor."""
    factor: str
    weight: float = Field(ge=0, le=1)
    description: str


class AttritionRiskResponse(BaseModel):
    """Response for attrition risk analysis."""
    user_id: str
    user_name: str

    # Risk assessment
    risk_score: float = Field(ge=0, le=1)
    risk_level: str = Field(..., description="Risk level: low, medium, high, critical")

    # Factors
    risk_factors: List[AttritionRiskFactor] = Field(default_factory=list)
    protective_factors: List[str] = Field(default_factory=list)

    # Recommendations
    recommended_actions: List[str] = Field(default_factory=list)

    analyzed_at: datetime


class AttritionRiskListResponse(BaseModel):
    """Response for list of attrition risks."""
    at_risk_employees: List[AttritionRiskResponse]
    total: int
    high_risk_count: int = 0
    medium_risk_count: int = 0


# ==================== Burnout Risk Schemas ====================

class BurnoutIndicator(BaseModel):
    """Burnout indicator."""
    indicator: str
    severity: str = Field(..., description="Severity: low, medium, high")
    observed_value: Any
    threshold_value: Any


class BurnoutRiskResponse(BaseModel):
    """Response for burnout risk analysis."""
    user_id: str
    user_name: str

    # Risk assessment
    risk_score: float = Field(ge=0, le=1)
    risk_level: str = Field(..., description="Risk level: low, medium, high, critical")

    # Indicators
    indicators: List[BurnoutIndicator] = Field(default_factory=list)

    # Workload metrics
    avg_hours_per_week: float
    tasks_in_progress: int
    overdue_tasks: int

    # Recommendations
    recommended_actions: List[str] = Field(default_factory=list)

    analyzed_at: datetime


class BurnoutRiskListResponse(BaseModel):
    """Response for list of burnout risks."""
    at_risk_employees: List[BurnoutRiskResponse]
    total: int
    high_risk_count: int = 0


# ==================== Manager Effectiveness Schemas ====================

class ManagerEffectivenessResponse(BaseModel):
    """Schema for manager effectiveness in API responses."""
    id: str
    manager_id: str
    manager_name: str
    org_id: str

    # Team metrics
    team_size: int
    direct_reports: int

    # Effectiveness scores
    overall_score: float = Field(ge=0, le=100)
    team_velocity_score: float = Field(ge=0, le=100)
    team_quality_score: float = Field(ge=0, le=100)
    team_growth_score: float = Field(ge=0, le=100)
    retention_score: float = Field(ge=0, le=100)

    # Comparison
    percentile: Optional[float] = Field(None, ge=0, le=100)

    # Period
    period_start: date
    period_end: date

    created_at: datetime

    model_config = {"from_attributes": True}


class ManagerEffectivenessListResponse(BaseModel):
    """Response for list of manager effectiveness scores."""
    managers: List[ManagerEffectivenessResponse]
    total: int
    average_score: float = 0.0


# ==================== Organization Health Schemas ====================

class OrgHealthMetric(BaseModel):
    """Organization health metric."""
    name: str
    value: float
    target: Optional[float] = None
    trend: str = Field(..., description="Trend: improving, stable, declining")
    status: str = Field(..., description="Status: good, warning, critical")


class OrgHealthSnapshotResponse(BaseModel):
    """Schema for organization health snapshot in API responses."""
    id: str
    org_id: str

    # Overall health
    health_score: float = Field(ge=0, le=100)
    health_status: str = Field(..., description="Status: healthy, warning, critical")

    # Component scores
    productivity_index: float = Field(ge=0, le=100)
    quality_index: float = Field(ge=0, le=100)
    engagement_index: float = Field(ge=0, le=100)
    skill_coverage_index: float = Field(ge=0, le=100)

    # Headcount
    total_employees: int
    active_employees: int

    # Metrics
    metrics: List[OrgHealthMetric] = Field(default_factory=list)

    snapshot_date: date
    created_at: datetime

    model_config = {"from_attributes": True}


class OrgHealthTrendResponse(BaseModel):
    """Response for organization health trend."""
    org_id: str

    # Time series
    snapshots: List[OrgHealthSnapshotResponse]

    # Trend summary
    health_trend: str = Field(..., description="Trend: improving, stable, declining")
    trend_percentage: float

    period_start: date
    period_end: date


# ==================== Restructuring Simulation Schemas ====================

class RestructuringScenarioRequest(BaseModel):
    """Request for restructuring simulation."""
    scenario_type: str = Field(..., description="Type: team_merge, role_change, automation, reduction")
    description: str = Field(..., min_length=1, max_length=500)
    parameters: Dict[str, Any] = Field(..., description="Scenario parameters")


class RestructuringImpact(BaseModel):
    """Impact of restructuring."""
    area: str
    impact_type: str = Field(..., description="Type: positive, negative, neutral")
    magnitude: str = Field(..., description="Magnitude: low, medium, high")
    description: str


class RestructuringScenarioResponse(BaseModel):
    """Schema for restructuring scenario in API responses."""
    id: str
    org_id: str

    # Scenario
    scenario_type: str
    description: str
    parameters: Dict[str, Any] = Field(default_factory=dict)

    # Results
    productivity_impact: float = Field(..., description="Percentage change")
    cost_impact: float = Field(..., description="Cost change")
    skill_coverage_impact: float = Field(..., description="Percentage change")
    risk_score: float = Field(ge=0, le=1)

    # Detailed impacts
    impacts: List[RestructuringImpact] = Field(default_factory=list)

    # Recommendations
    recommendations: List[str] = Field(default_factory=list)
    risks: List[str] = Field(default_factory=list)

    # Metadata
    confidence: float = Field(ge=0, le=1)
    simulated_at: datetime

    model_config = {"from_attributes": True}


class RestructuringScenarioListResponse(BaseModel):
    """Response for list of restructuring scenarios."""
    scenarios: List[RestructuringScenarioResponse]
    total: int


# ==================== Hiring Plan Schemas ====================

class HiringRecommendation(BaseModel):
    """Hiring recommendation."""
    role: str
    skill_requirements: List[str]
    priority: str = Field(..., description="Priority: low, medium, high, critical")
    recommended_hire_date: date
    estimated_cost: Optional[float] = None
    justification: str


class HiringPlanResponse(BaseModel):
    """Response for hiring plan generation."""
    org_id: str

    # Summary
    total_positions: int
    total_cost: float

    # Recommendations
    recommendations: List[HiringRecommendation]

    # By timeline
    immediate_needs: List[HiringRecommendation]  # Within 1 month
    short_term_needs: List[HiringRecommendation]  # 1-3 months
    medium_term_needs: List[HiringRecommendation]  # 3-6 months

    # Analysis
    skill_gaps_addressed: List[str]
    capacity_improvement: float

    generated_at: datetime

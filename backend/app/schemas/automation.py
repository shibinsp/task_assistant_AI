"""
TaskPulse - AI Assistant - Automation Schemas
Pydantic schemas for automation patterns and AI agents
"""

from datetime import datetime
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field

from app.models.automation import PatternStatus, AgentStatus


# ==================== Automation Pattern Schemas ====================

class AutomationPatternResponse(BaseModel):
    """Schema for automation pattern in API responses."""
    id: str
    org_id: str
    name: str
    description: Optional[str] = None

    # Pattern details
    pattern_signature: str
    task_count: int
    consistency_score: float = Field(ge=0, le=1)
    automation_readiness: float = Field(ge=0, le=1)

    # Status
    status: PatternStatus

    # Metrics
    estimated_hours_saved: float = 0.0
    estimated_cost_saved: float = 0.0

    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class PatternListResponse(BaseModel):
    """Response for list of automation patterns."""
    patterns: List[AutomationPatternResponse]
    total: int
    total_potential_savings_hours: float = 0.0
    total_potential_savings_cost: float = 0.0


class PatternAcceptRequest(BaseModel):
    """Request to accept an automation pattern."""
    pattern_id: str = Field(..., description="Pattern ID to accept")
    agent_name: Optional[str] = Field(None, description="Name for the created agent")
    schedule: Optional[str] = Field(None, description="Cron schedule for agent execution")


class PatternRejectRequest(BaseModel):
    """Request to reject an automation pattern."""
    pattern_id: str = Field(..., description="Pattern ID to reject")
    reason: Optional[str] = Field(None, description="Reason for rejection")


# ==================== AI Agent Schemas ====================

class AIAgentCreate(BaseModel):
    """Schema for creating an AI agent."""
    name: str = Field(..., min_length=1, max_length=100, description="Agent name")
    description: Optional[str] = Field(None, max_length=500, description="Agent description")
    pattern_id: Optional[str] = Field(None, description="Source pattern ID")
    trigger_conditions: Dict[str, Any] = Field(default_factory=dict, description="Trigger conditions")
    actions: List[Dict[str, Any]] = Field(default_factory=list, description="Actions to perform")
    schedule: Optional[str] = Field(None, description="Cron schedule")


class AIAgentUpdate(BaseModel):
    """Schema for updating an AI agent."""
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    description: Optional[str] = Field(None, max_length=500)
    trigger_conditions: Optional[Dict[str, Any]] = None
    actions: Optional[List[Dict[str, Any]]] = None
    schedule: Optional[str] = None
    is_enabled: Optional[bool] = None


class AIAgentResponse(BaseModel):
    """Schema for AI agent in API responses."""
    id: str
    org_id: str
    name: str
    description: Optional[str] = None

    # Configuration
    pattern_id: Optional[str] = None
    trigger_conditions: Dict[str, Any] = Field(default_factory=dict)
    actions: List[Dict[str, Any]] = Field(default_factory=list)
    schedule: Optional[str] = None

    # Status
    status: AgentStatus
    is_enabled: bool

    # Shadow mode
    shadow_mode: bool = False
    shadow_runs: int = 0
    shadow_match_rate: Optional[float] = None

    # Metrics
    total_runs: int = 0
    successful_runs: int = 0
    failed_runs: int = 0
    hours_saved: float = 0.0

    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class AIAgentListResponse(BaseModel):
    """Response for list of AI agents."""
    agents: List[AIAgentResponse]
    total: int
    active_count: int = 0
    shadow_count: int = 0


class AIAgentStatusUpdate(BaseModel):
    """Schema for updating agent status."""
    status: AgentStatus = Field(..., description="New status")


# ==================== Agent Run Schemas ====================

class AgentRunResponse(BaseModel):
    """Schema for agent run in API responses."""
    id: str
    agent_id: str

    # Execution
    trigger_type: str  # scheduled, manual, event
    trigger_data: Dict[str, Any] = Field(default_factory=dict)

    # Results
    success: bool
    output_data: Dict[str, Any] = Field(default_factory=dict)
    error_message: Optional[str] = None

    # Performance
    duration_ms: Optional[int] = None
    tasks_processed: int = 0
    actions_taken: int = 0

    # Shadow mode comparison
    shadow_mode: bool = False
    manual_match: Optional[bool] = None
    mismatch_reason: Optional[str] = None

    started_at: datetime
    completed_at: Optional[datetime] = None

    model_config = {"from_attributes": True}


class AgentRunListResponse(BaseModel):
    """Response for list of agent runs."""
    runs: List[AgentRunResponse]
    total: int
    page: int
    page_size: int


# ==================== Shadow Mode Schemas ====================

class ShadowReportMismatch(BaseModel):
    """Mismatch in shadow mode comparison."""
    field: str
    expected: Any
    actual: Any
    severity: str = Field(..., description="Severity: low, medium, high")


class ShadowReportResponse(BaseModel):
    """Response for shadow mode validation report."""
    agent_id: str
    agent_name: str

    # Summary
    total_runs: int
    matching_runs: int
    mismatching_runs: int
    match_rate: float = Field(ge=0, le=1)

    # Mismatch details
    mismatches: List[ShadowReportMismatch] = Field(default_factory=list)

    # Recommendation
    ready_for_production: bool
    recommendation: str

    # Period
    period_start: datetime
    period_end: datetime


class PromoteShadowRequest(BaseModel):
    """Request to promote agent from shadow to live."""
    agent_id: str = Field(..., description="Agent ID to promote")
    confirm: bool = Field(default=False, description="Confirm promotion")


# ==================== ROI Dashboard Schemas ====================

class ROIMetrics(BaseModel):
    """ROI metrics for automation."""
    total_hours_saved: float = 0.0
    total_cost_saved: float = 0.0
    tasks_automated: int = 0
    automation_rate: float = Field(default=0.0, ge=0, le=1)


class ROIDashboardResponse(BaseModel):
    """Response for ROI dashboard."""
    # Overall metrics
    metrics: ROIMetrics

    # By period
    this_week: ROIMetrics
    this_month: ROIMetrics
    all_time: ROIMetrics

    # By agent
    by_agent: List[Dict[str, Any]] = Field(default_factory=list)

    # Trends
    weekly_savings_trend: List[Dict[str, Any]] = Field(default_factory=list)

    # Projections
    projected_monthly_savings: float = 0.0
    projected_annual_savings: float = 0.0


# ==================== Pattern Detection Schemas ====================

class DetectPatternsRequest(BaseModel):
    """Request to trigger pattern detection."""
    min_occurrences: int = Field(default=3, ge=2, description="Minimum occurrences")
    min_consistency: float = Field(default=0.7, ge=0, le=1, description="Minimum consistency score")
    days_to_analyze: int = Field(default=30, ge=7, le=365, description="Days to analyze")


class DetectPatternsResponse(BaseModel):
    """Response from pattern detection."""
    patterns_detected: int
    new_patterns: int
    updated_patterns: int
    analysis_period_days: int
    completed_at: datetime

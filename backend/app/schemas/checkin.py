"""
TaskPulse - AI Assistant - Check-In Schemas
Pydantic schemas for check-in management
"""

from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime

from app.models.checkin import (
    CheckInTrigger, CheckInStatus, ProgressIndicator
)


# ==================== Check-In Response Schemas ====================

class CheckInResponse(BaseModel):
    """Check-in response schema."""
    id: str
    task_id: str
    user_id: Optional[str]
    org_id: str
    cycle_number: int
    trigger: CheckInTrigger
    status: CheckInStatus
    scheduled_at: datetime
    responded_at: Optional[datetime]
    expires_at: Optional[datetime]
    progress_indicator: Optional[ProgressIndicator]
    progress_notes: Optional[str]
    completed_since_last: Optional[str]
    blockers_reported: Optional[str]
    help_needed: bool
    estimated_completion_change: Optional[float]
    ai_suggestion: Optional[str]
    ai_confidence: Optional[float]
    sentiment_score: Optional[float]
    friction_detected: bool
    escalated: bool
    escalated_to: Optional[str]
    escalated_at: Optional[datetime]
    escalation_reason: Optional[str]
    is_overdue: bool
    response_time_minutes: Optional[int]
    task_title: Optional[str] = None
    user_name: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class CheckInDetailResponse(CheckInResponse):
    """Detailed check-in with reminders."""
    reminders_sent: int = 0


class CheckInListResponse(BaseModel):
    """Paginated check-in list."""
    checkins: List[CheckInResponse]
    total: int
    page: int
    page_size: int


# ==================== Check-In Response (User Action) ====================

class CheckInSubmit(BaseModel):
    """Schema for responding to a check-in."""
    progress_indicator: ProgressIndicator
    progress_notes: Optional[str] = Field(None, max_length=2000)
    completed_since_last: Optional[str] = Field(None, max_length=1000)
    blockers_reported: Optional[str] = Field(None, max_length=1000)
    help_needed: bool = False
    estimated_completion_change: Optional[float] = Field(
        None,
        description="Hours to add/subtract from estimate (positive = more time needed)"
    )


class CheckInSkip(BaseModel):
    """Schema for skipping a check-in."""
    reason: Optional[str] = Field(None, max_length=500)


# ==================== Check-In Creation (Manual) ====================

class CheckInCreate(BaseModel):
    """Schema for manually creating a check-in."""
    task_id: str
    user_id: str
    trigger: CheckInTrigger = CheckInTrigger.MANUAL
    scheduled_at: Optional[datetime] = None  # Defaults to now
    expires_at: Optional[datetime] = None


# ==================== Check-In Configuration ====================

class CheckInConfigBase(BaseModel):
    """Base check-in configuration."""
    interval_hours: float = Field(default=3.0, ge=1.0, le=8.0)
    enabled: bool = True
    silent_mode_threshold: float = Field(default=0.8, ge=0.0, le=1.0)
    max_daily_checkins: int = Field(default=4, ge=1, le=10)
    work_start_hour: int = Field(default=9, ge=0, le=23)
    work_end_hour: int = Field(default=18, ge=0, le=23)
    respect_timezone: bool = True
    excluded_days: str = "0,6"  # Sunday, Saturday
    auto_escalate_after_missed: int = Field(default=2, ge=1, le=5)
    escalate_to_manager: bool = True
    ai_suggestions_enabled: bool = True
    ai_sentiment_analysis: bool = True


class CheckInConfigCreate(CheckInConfigBase):
    """Schema for creating check-in config."""
    team_id: Optional[str] = None
    user_id: Optional[str] = None
    task_id: Optional[str] = None


class CheckInConfigUpdate(BaseModel):
    """Schema for updating check-in config."""
    interval_hours: Optional[float] = Field(None, ge=1.0, le=8.0)
    enabled: Optional[bool] = None
    silent_mode_threshold: Optional[float] = Field(None, ge=0.0, le=1.0)
    max_daily_checkins: Optional[int] = Field(None, ge=1, le=10)
    work_start_hour: Optional[int] = Field(None, ge=0, le=23)
    work_end_hour: Optional[int] = Field(None, ge=0, le=23)
    respect_timezone: Optional[bool] = None
    excluded_days: Optional[str] = None
    auto_escalate_after_missed: Optional[int] = Field(None, ge=1, le=5)
    escalate_to_manager: Optional[bool] = None
    ai_suggestions_enabled: Optional[bool] = None
    ai_sentiment_analysis: Optional[bool] = None


class CheckInConfigResponse(CheckInConfigBase):
    """Check-in configuration response."""
    id: str
    org_id: str
    team_id: Optional[str]
    user_id: Optional[str]
    task_id: Optional[str]
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# ==================== Escalation ====================

class EscalationRequest(BaseModel):
    """Schema for manually escalating a check-in."""
    escalate_to: str
    reason: str = Field(..., min_length=1, max_length=1000)


class EscalationResponse(BaseModel):
    """Escalation result."""
    checkin_id: str
    escalated_to: str
    escalated_at: datetime
    reason: str
    notification_sent: bool = True


# ==================== Statistics & Analytics ====================

class CheckInStatistics(BaseModel):
    """Check-in statistics for a period."""
    total_checkins: int
    pending: int
    responded: int
    skipped: int
    expired: int
    escalated: int
    response_rate: float
    average_response_time_minutes: Optional[float]
    friction_rate: float  # Percentage with friction detected
    help_requested_rate: float


class UserCheckInSummary(BaseModel):
    """User's check-in summary."""
    user_id: str
    user_name: Optional[str]
    total_checkins: int
    response_rate: float
    average_response_time_minutes: Optional[float]
    current_streak: int  # Consecutive responses
    common_blockers: List[str]


class TeamCheckInSummary(BaseModel):
    """Team check-in summary."""
    team_id: str
    total_members: int
    active_checkins: int
    response_rate: float
    members_needing_help: int
    friction_detected_count: int


# ==================== Feed/Dashboard ====================

class CheckInFeedItem(BaseModel):
    """Item in the check-in feed for managers."""
    checkin_id: str
    task_id: str
    task_title: str
    user_id: str
    user_name: str
    status: CheckInStatus
    progress_indicator: Optional[ProgressIndicator]
    help_needed: bool
    friction_detected: bool
    ai_suggestion: Optional[str]
    escalated: bool
    scheduled_at: datetime
    responded_at: Optional[datetime]


class CheckInFeedResponse(BaseModel):
    """Manager's check-in feed."""
    items: List[CheckInFeedItem]
    total: int
    needs_attention: int  # Count requiring manager action
    page: int
    page_size: int

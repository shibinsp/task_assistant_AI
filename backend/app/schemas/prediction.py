"""
TaskPulse - AI Assistant - Prediction Schemas
Pydantic schemas for ML predictions and velocity tracking
"""

from datetime import datetime, date
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field

from app.models.prediction import PredictionType


# ==================== Prediction Request Schemas ====================

class TaskPredictionRequest(BaseModel):
    """Request for task completion prediction."""
    task_id: str = Field(..., description="Task ID to predict")
    include_subtasks: bool = Field(default=True, description="Include subtask predictions")


class TeamVelocityRequest(BaseModel):
    """Request for team velocity analysis."""
    team_id: Optional[str] = Field(None, description="Team ID (optional)")
    days: int = Field(default=30, ge=7, le=365, description="Number of days to analyze")


class HiringPredictionRequest(BaseModel):
    """Request for hiring needs prediction."""
    target_date: date = Field(..., description="Target date for prediction")
    growth_rate: float = Field(default=0.0, ge=-1.0, le=5.0, description="Expected growth rate")


# ==================== Prediction Response Schemas ====================

class PredictionEstimate(BaseModel):
    """Prediction estimate with confidence intervals."""
    p25: float = Field(..., description="25th percentile estimate")
    p50: float = Field(..., description="50th percentile (median) estimate")
    p90: float = Field(..., description="90th percentile estimate")
    unit: str = Field(default="days", description="Unit of measurement")


class TaskPredictionResponse(BaseModel):
    """Response for task completion prediction."""
    task_id: str
    task_title: str
    current_status: str

    # Predictions
    completion_estimate: PredictionEstimate
    risk_level: str = Field(..., description="Risk level: low, medium, high, critical")
    risk_factors: List[str] = Field(default_factory=list, description="Identified risk factors")

    # Confidence
    confidence: float = Field(..., ge=0, le=1, description="Prediction confidence")

    # Recommendations
    recommendations: List[str] = Field(default_factory=list, description="Suggested actions")

    # Metadata
    predicted_at: datetime
    model_version: str = "1.0"


class PredictionResponse(BaseModel):
    """Schema for prediction in API responses."""
    id: str
    org_id: str
    prediction_type: PredictionType
    target_id: str
    target_type: str

    # Estimates
    p25_estimate: float
    p50_estimate: float
    p90_estimate: float

    # Risk assessment
    risk_score: float = Field(ge=0, le=1)
    risk_factors: List[str] = Field(default_factory=list)

    # Accuracy tracking
    confidence: float = Field(ge=0, le=1)
    actual_value: Optional[float] = None
    accuracy_score: Optional[float] = None

    created_at: datetime
    expires_at: Optional[datetime] = None

    model_config = {"from_attributes": True}


class PredictionListResponse(BaseModel):
    """Response for list of predictions."""
    predictions: List[PredictionResponse]
    total: int
    page: int
    page_size: int


# ==================== Velocity Schemas ====================

class VelocityDataPoint(BaseModel):
    """Single velocity data point."""
    date: date
    completed_tasks: int
    story_points: float
    velocity: float


class VelocitySnapshotResponse(BaseModel):
    """Schema for velocity snapshot in API responses."""
    id: str
    org_id: str
    team_id: Optional[str] = None
    user_id: Optional[str] = None

    # Metrics
    period_start: date
    period_end: date
    tasks_completed: int
    story_points_completed: float
    avg_completion_time_hours: float

    # Velocity
    velocity: float
    velocity_trend: str = Field(..., description="Trend: increasing, stable, decreasing")

    created_at: datetime

    model_config = {"from_attributes": True}


class VelocityTrendResponse(BaseModel):
    """Response for velocity trend analysis."""
    team_id: Optional[str] = None
    user_id: Optional[str] = None

    # Time series data
    data_points: List[VelocityDataPoint]

    # Summary
    current_velocity: float
    average_velocity: float
    trend: str = Field(..., description="Trend: increasing, stable, decreasing")
    trend_percentage: float = Field(..., description="Percentage change")

    # Forecast
    forecast_next_week: float
    forecast_next_month: float

    # Period
    period_start: date
    period_end: date


class VelocityForecastResponse(BaseModel):
    """Response for velocity forecasting."""
    team_id: Optional[str] = None

    # Forecast data
    forecast_dates: List[date]
    forecast_values: List[float]
    confidence_lower: List[float]
    confidence_upper: List[float]

    # Summary
    expected_velocity: float
    best_case_velocity: float
    worst_case_velocity: float


# ==================== Hiring Prediction Schemas ====================

class SkillDemand(BaseModel):
    """Skill demand prediction."""
    skill_name: str
    current_capacity: int
    required_capacity: int
    gap: int
    priority: str = Field(..., description="Priority: low, medium, high, critical")


class HiringPredictionResponse(BaseModel):
    """Response for hiring needs prediction."""
    target_date: date

    # Overall needs
    total_headcount_needed: int
    current_headcount: int
    hiring_gap: int

    # By skill
    skill_demands: List[SkillDemand]

    # Timeline
    recommended_start_date: date
    recommended_hire_dates: List[date]

    # Cost estimate
    estimated_cost: Optional[float] = None

    # Confidence
    confidence: float = Field(ge=0, le=1)

    predicted_at: datetime


# ==================== Accuracy Tracking Schemas ====================

class PredictionAccuracyResponse(BaseModel):
    """Response for prediction accuracy metrics."""
    prediction_type: str

    # Metrics
    total_predictions: int
    evaluated_predictions: int

    # Accuracy scores
    mean_absolute_error: Optional[float] = None
    mean_percentage_error: Optional[float] = None
    accuracy_rate: Optional[float] = None

    # By confidence level
    high_confidence_accuracy: Optional[float] = None
    medium_confidence_accuracy: Optional[float] = None
    low_confidence_accuracy: Optional[float] = None

    # Time period
    period_start: date
    period_end: date


class RecordActualRequest(BaseModel):
    """Request to record actual value for prediction."""
    prediction_id: str = Field(..., description="Prediction ID")
    actual_value: float = Field(..., description="Actual observed value")
    completed_at: Optional[datetime] = Field(None, description="When the actual was observed")

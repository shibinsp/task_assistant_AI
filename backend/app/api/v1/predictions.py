"""
TaskPulse - AI Assistant - Predictions API
ML-powered forecasting endpoints
"""

from typing import Optional
from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from datetime import datetime, timedelta
import random

from app.database import get_db
from app.models.user import User, UserRole
from app.models.prediction import Prediction, VelocitySnapshot, PredictionType
from app.models.task import Task, TaskStatus
from app.api.v1.dependencies import get_current_active_user, require_roles
from app.core.permissions import Permission, has_permission
from app.core.exceptions import NotFoundException, ForbiddenException
from app.utils.helpers import generate_uuid
from pydantic import BaseModel, Field
from typing import List

router = APIRouter()


# Schemas
class PredictionResponse(BaseModel):
    id: str
    prediction_type: PredictionType
    task_id: Optional[str]
    predicted_date_p25: Optional[datetime]
    predicted_date_p50: Optional[datetime]
    predicted_date_p90: Optional[datetime]
    confidence: Optional[float]
    risk_score: Optional[float]
    risk_factors: List[str]
    created_at: datetime

    class Config:
        from_attributes = True


class VelocityResponse(BaseModel):
    team_id: str
    current_velocity: float
    velocity_trend: str
    predicted_next_sprint: float
    capacity_utilization: float
    snapshots: List[dict]


class HiringPrediction(BaseModel):
    skill_name: str
    current_coverage: float
    required_coverage: float
    gap: float
    recommended_hires: int
    urgency: str


# Endpoints
@router.get(
    "/tasks/{task_id}",
    response_model=PredictionResponse,
    summary="Get task prediction"
)
async def get_task_prediction(
    task_id: str,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """Get delivery prediction for a task."""
    if not has_permission(current_user.role, Permission.PREDICTIONS_READ):
        raise ForbiddenException("Not authorized")

    # Check task exists
    task = await db.execute(
        select(Task).where(Task.id == task_id, Task.org_id == current_user.org_id)
    )
    task = task.scalar_one_or_none()
    if not task:
        raise NotFoundException("Task", task_id)

    # Check for existing prediction
    pred = await db.execute(
        select(Prediction).where(
            Prediction.task_id == task_id,
            Prediction.prediction_type == PredictionType.TASK_COMPLETION
        ).order_by(Prediction.created_at.desc())
    )
    prediction = pred.scalar_one_or_none()

    if not prediction:
        # Generate new prediction (mock)
        now = datetime.utcnow()
        base_days = task.estimated_hours / 8 if task.estimated_hours else 5

        prediction = Prediction(
            id=generate_uuid(),
            org_id=current_user.org_id,
            prediction_type=PredictionType.TASK_COMPLETION,
            task_id=task_id,
            predicted_date_p25=now + timedelta(days=base_days * 0.8),
            predicted_date_p50=now + timedelta(days=base_days),
            predicted_date_p90=now + timedelta(days=base_days * 1.5),
            confidence=random.uniform(0.7, 0.95),
            risk_score=random.uniform(0.1, 0.6)
        )
        prediction.risk_factors = ["Dependencies may cause delays", "Resource availability uncertain"]
        db.add(prediction)
        await db.flush()
        await db.refresh(prediction)

    return PredictionResponse(
        id=prediction.id,
        prediction_type=prediction.prediction_type,
        task_id=prediction.task_id,
        predicted_date_p25=prediction.predicted_date_p25,
        predicted_date_p50=prediction.predicted_date_p50,
        predicted_date_p90=prediction.predicted_date_p90,
        confidence=prediction.confidence,
        risk_score=prediction.risk_score,
        risk_factors=prediction.risk_factors,
        created_at=prediction.created_at
    )


@router.get(
    "/team/{team_id}/velocity",
    response_model=VelocityResponse,
    summary="Get team velocity forecast"
)
async def get_team_velocity(
    team_id: str,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """Get velocity forecast for a team."""
    if not has_permission(current_user.role, Permission.PREDICTIONS_READ_TEAM):
        raise ForbiddenException("Not authorized")

    # Mock velocity data
    snapshots = []
    now = datetime.utcnow()
    for i in range(5):
        week_start = now - timedelta(weeks=5-i)
        snapshots.append({
            "period": week_start.isoformat(),
            "velocity": random.uniform(15, 25),
            "capacity_utilization": random.uniform(0.7, 0.9)
        })

    current = snapshots[-1]["velocity"] if snapshots else 20
    trend = "improving" if snapshots[-1]["velocity"] > snapshots[0]["velocity"] else "stable"

    return VelocityResponse(
        team_id=team_id,
        current_velocity=current,
        velocity_trend=trend,
        predicted_next_sprint=current * 1.05,
        capacity_utilization=0.82,
        snapshots=snapshots
    )


@router.get(
    "/hiring",
    response_model=List[HiringPrediction],
    summary="Get hiring predictions"
)
async def get_hiring_predictions(
    current_user: User = Depends(require_roles(
        UserRole.SUPER_ADMIN, UserRole.ORG_ADMIN, UserRole.MANAGER
    )),
    db: AsyncSession = Depends(get_db)
):
    """Get AI-powered hiring recommendations."""
    # Mock hiring predictions
    return [
        HiringPrediction(
            skill_name="Python",
            current_coverage=0.75,
            required_coverage=0.90,
            gap=0.15,
            recommended_hires=2,
            urgency="medium"
        ),
        HiringPrediction(
            skill_name="Machine Learning",
            current_coverage=0.40,
            required_coverage=0.70,
            gap=0.30,
            recommended_hires=3,
            urgency="high"
        ),
        HiringPrediction(
            skill_name="DevOps",
            current_coverage=0.60,
            required_coverage=0.80,
            gap=0.20,
            recommended_hires=2,
            urgency="medium"
        )
    ]


@router.get(
    "/accuracy",
    summary="Get prediction accuracy metrics"
)
async def get_prediction_accuracy(
    days: int = Query(90, ge=30, le=365),
    current_user: User = Depends(require_roles(
        UserRole.SUPER_ADMIN, UserRole.ORG_ADMIN
    )),
    db: AsyncSession = Depends(get_db)
):
    """Get prediction accuracy tracking."""
    return {
        "period_days": days,
        "total_predictions": 150,
        "completed_tasks": 120,
        "accuracy_p50": 0.78,
        "accuracy_p90": 0.92,
        "mean_absolute_error_days": 2.3,
        "model_version": "v1.0",
        "last_retrained": datetime.utcnow().isoformat()
    }

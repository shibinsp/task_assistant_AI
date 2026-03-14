"""
TaskPulse - AI Assistant - Prediction Models
ML-powered forecasting and risk assessment
"""

from sqlalchemy import Column, String, Text, Boolean, ForeignKey, Integer, Float, DateTime
from sqlalchemy.dialects.postgresql import UUID as PG_UUID, JSONB
from sqlalchemy.orm import relationship, backref
from sqlalchemy.sql import func
import enum
import uuid
from datetime import datetime

from app.database import Base, Enum


class PredictionType(str, enum.Enum):
    """Types of predictions."""
    TASK_COMPLETION = "task_completion"
    PROJECT_DELIVERY = "project_delivery"
    TEAM_VELOCITY = "team_velocity"
    ATTRITION_RISK = "attrition_risk"
    HIRING_NEEDS = "hiring_needs"


class Prediction(Base):
    """Prediction record for tasks/projects."""
    __tablename__ = "predictions"

    org_id = Column(PG_UUID(as_uuid=True), ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False, index=True)
    prediction_type = Column(Enum(PredictionType), nullable=False)

    # Target
    task_id = Column(PG_UUID(as_uuid=True), ForeignKey("tasks.id"), nullable=True)
    project_id = Column(PG_UUID(as_uuid=True), nullable=True)
    user_id = Column(PG_UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    team_id = Column(PG_UUID(as_uuid=True), nullable=True)

    # Prediction values
    predicted_date_p25 = Column(DateTime(timezone=True), nullable=True)  # 25th percentile
    predicted_date_p50 = Column(DateTime(timezone=True), nullable=True)  # Median
    predicted_date_p90 = Column(DateTime(timezone=True), nullable=True)  # 90th percentile
    confidence = Column(Float, nullable=True)
    risk_score = Column(Float, nullable=True)  # 0-1

    # Factors
    risk_factors = Column(JSONB, default=[])
    model_version = Column(String(50), default="v1")
    features = Column(JSONB, default={})

    # Accuracy tracking
    actual_date = Column(DateTime(timezone=True), nullable=True)
    accuracy_score = Column(Float, nullable=True)

    organization = relationship("Organization", backref="predictions")
    task = relationship("Task", backref=backref("predictions", passive_deletes=True))
    user = relationship("User", backref="predictions")


class VelocitySnapshot(Base):
    """Team velocity snapshots for trending."""
    __tablename__ = "velocity_snapshots"

    org_id = Column(PG_UUID(as_uuid=True), ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False)
    team_id = Column(PG_UUID(as_uuid=True), nullable=False, index=True)

    period_start = Column(DateTime(timezone=True), nullable=False)
    period_end = Column(DateTime(timezone=True), nullable=False)

    tasks_completed = Column(Integer, default=0)
    story_points_completed = Column(Float, default=0)
    velocity = Column(Float, nullable=True)
    capacity_utilization = Column(Float, nullable=True)

    organization = relationship("Organization", backref="velocity_snapshots")

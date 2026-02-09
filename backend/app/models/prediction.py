"""
TaskPulse - AI Assistant - Prediction Models
ML-powered forecasting and risk assessment
"""

from sqlalchemy import Column, String, Enum, Text, Boolean, ForeignKey, Integer, Float, DateTime
from sqlalchemy.orm import relationship
import enum
from datetime import datetime

from app.database import Base


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

    org_id = Column(String(36), ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False, index=True)
    prediction_type = Column(Enum(PredictionType), nullable=False)

    # Target
    task_id = Column(String(36), ForeignKey("tasks.id"), nullable=True)
    project_id = Column(String(36), nullable=True)
    user_id = Column(String(36), ForeignKey("users.id"), nullable=True)
    team_id = Column(String(36), nullable=True)

    # Prediction values
    predicted_date_p25 = Column(DateTime, nullable=True)  # 25th percentile
    predicted_date_p50 = Column(DateTime, nullable=True)  # Median
    predicted_date_p90 = Column(DateTime, nullable=True)  # 90th percentile
    confidence = Column(Float, nullable=True)
    risk_score = Column(Float, nullable=True)  # 0-1

    # Factors
    risk_factors_json = Column(Text, default="[]")
    model_version = Column(String(50), default="v1")
    features_json = Column(Text, default="{}")

    # Accuracy tracking
    actual_date = Column(DateTime, nullable=True)
    accuracy_score = Column(Float, nullable=True)

    organization = relationship("Organization", backref="predictions")
    task = relationship("Task", backref="predictions")
    user = relationship("User", backref="predictions")

    @property
    def risk_factors(self):
        import json
        return json.loads(self.risk_factors_json or "[]")

    @risk_factors.setter
    def risk_factors(self, value):
        import json
        self.risk_factors_json = json.dumps(value)


class VelocitySnapshot(Base):
    """Team velocity snapshots for trending."""
    __tablename__ = "velocity_snapshots"

    org_id = Column(String(36), ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False)
    team_id = Column(String(36), nullable=False, index=True)

    period_start = Column(DateTime, nullable=False)
    period_end = Column(DateTime, nullable=False)

    tasks_completed = Column(Integer, default=0)
    story_points_completed = Column(Float, default=0)
    velocity = Column(Float, nullable=True)
    capacity_utilization = Column(Float, nullable=True)

    organization = relationship("Organization", backref="velocity_snapshots")

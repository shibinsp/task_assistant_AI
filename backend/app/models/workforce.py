"""
TaskPulse - AI Assistant - Workforce Intelligence Models
Executive-level decision intelligence
"""

from sqlalchemy import Column, String, Enum, Text, Boolean, ForeignKey, Integer, Float, DateTime
from sqlalchemy.orm import relationship
import enum
from datetime import datetime

from app.database import Base


class WorkforceScore(Base):
    """Employee workforce score snapshot."""
    __tablename__ = "workforce_scores"

    user_id = Column(String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    org_id = Column(String(36), ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False, index=True)

    snapshot_date = Column(DateTime, default=datetime.utcnow)

    # Component scores (0-100)
    velocity_score = Column(Float, nullable=True)
    quality_score = Column(Float, nullable=True)
    self_sufficiency_score = Column(Float, nullable=True)
    learning_score = Column(Float, nullable=True)
    collaboration_score = Column(Float, nullable=True)

    # Composite
    overall_score = Column(Float, nullable=True)
    percentile_rank = Column(Float, nullable=True)

    # Risk indicators
    attrition_risk_score = Column(Float, nullable=True)
    burnout_risk_score = Column(Float, nullable=True)

    # Trend
    score_trend = Column(String(20), default="stable")  # improving, stable, declining

    user = relationship("User", backref="workforce_scores")
    organization = relationship("Organization", backref="workforce_scores")


class ManagerEffectiveness(Base):
    """Manager effectiveness metrics."""
    __tablename__ = "manager_effectiveness"

    manager_id = Column(String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    org_id = Column(String(36), ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False, index=True)

    snapshot_date = Column(DateTime, default=datetime.utcnow)

    # Team metrics
    team_size = Column(Integer, default=0)
    team_velocity_avg = Column(Float, nullable=True)
    team_quality_avg = Column(Float, nullable=True)

    # Manager-specific
    escalation_response_time_hours = Column(Float, nullable=True)
    escalation_resolution_rate = Column(Float, nullable=True)
    team_attrition_rate = Column(Float, nullable=True)
    team_satisfaction_score = Column(Float, nullable=True)

    # AI comparison
    redundancy_score = Column(Float, nullable=True)  # % of tasks AI could do
    assignment_quality_score = Column(Float, nullable=True)
    workload_distribution_score = Column(Float, nullable=True)

    # Ranking
    effectiveness_score = Column(Float, nullable=True)
    org_percentile = Column(Float, nullable=True)

    manager = relationship("User", backref="effectiveness_scores")
    organization = relationship("Organization", backref="manager_effectiveness")


class OrgHealthSnapshot(Base):
    """Organization health daily snapshot."""
    __tablename__ = "org_health_snapshots"

    org_id = Column(String(36), ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False, index=True)
    snapshot_date = Column(DateTime, default=datetime.utcnow)

    # Health components (0-100)
    productivity_index = Column(Float, nullable=True)
    skill_coverage_index = Column(Float, nullable=True)
    management_quality_index = Column(Float, nullable=True)
    automation_maturity_index = Column(Float, nullable=True)
    delivery_predictability_index = Column(Float, nullable=True)

    # Composite
    overall_health_score = Column(Float, nullable=True)

    # Key metrics
    total_employees = Column(Integer, default=0)
    active_tasks = Column(Integer, default=0)
    blocked_tasks = Column(Integer, default=0)
    overdue_tasks = Column(Integer, default=0)

    # Risk counts
    high_attrition_risk_count = Column(Integer, default=0)
    high_burnout_risk_count = Column(Integer, default=0)

    organization = relationship("Organization", backref="health_snapshots")


class RestructuringScenario(Base):
    """What-if scenario for restructuring."""
    __tablename__ = "restructuring_scenarios"

    org_id = Column(String(36), ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False, index=True)
    created_by = Column(String(36), ForeignKey("users.id"), nullable=False)

    name = Column(String(500), nullable=False)
    description = Column(Text, nullable=True)

    # Scenario config
    scenario_type = Column(String(100), nullable=False)  # team_merge, role_change, automation_replace, reduction
    config_json = Column(Text, default="{}")

    # Impact projections
    projected_cost_change = Column(Float, nullable=True)
    projected_productivity_change = Column(Float, nullable=True)
    projected_skill_coverage_change = Column(Float, nullable=True)
    affected_employees = Column(Integer, default=0)

    # Risk assessment
    risk_factors_json = Column(Text, default="[]")
    overall_risk_score = Column(Float, nullable=True)

    # Status
    is_draft = Column(Boolean, default=True)
    executed = Column(Boolean, default=False)
    executed_at = Column(DateTime, nullable=True)

    organization = relationship("Organization", backref="restructuring_scenarios")
    creator = relationship("User", backref="created_scenarios")

    @property
    def config(self):
        import json
        return json.loads(self.config_json or "{}")

    @config.setter
    def config(self, value):
        import json
        self.config_json = json.dumps(value)

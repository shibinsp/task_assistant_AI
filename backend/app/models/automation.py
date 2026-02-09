"""
TaskPulse - AI Assistant - Automation Models
Pattern detection and AI agent management
"""

from sqlalchemy import Column, String, Enum, Text, Boolean, ForeignKey, Integer, Float, DateTime
from sqlalchemy.orm import relationship
import enum
from datetime import datetime

from app.database import Base


class PatternStatus(str, enum.Enum):
    """Automation pattern status."""
    DETECTED = "detected"
    SUGGESTED = "suggested"
    ACCEPTED = "accepted"
    REJECTED = "rejected"
    IMPLEMENTED = "implemented"


class AgentStatus(str, enum.Enum):
    """AI agent status."""
    CREATED = "created"
    SHADOW = "shadow"
    SUPERVISED = "supervised"
    LIVE = "live"
    PAUSED = "paused"
    RETIRED = "retired"


class AutomationPattern(Base):
    """Detected automation opportunity."""
    __tablename__ = "automation_patterns"

    org_id = Column(String(36), ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False, index=True)

    # Pattern details
    name = Column(String(500), nullable=False)
    description = Column(Text, nullable=True)
    pattern_type = Column(String(100), nullable=True)
    status = Column(Enum(PatternStatus), default=PatternStatus.DETECTED)

    # Detection info
    frequency_per_week = Column(Float, nullable=True)
    consistency_score = Column(Float, nullable=True)  # 0-1
    users_affected = Column(Integer, default=0)

    # Savings estimate
    estimated_hours_saved_weekly = Column(Float, nullable=True)
    estimated_cost_savings_monthly = Column(Float, nullable=True)
    implementation_complexity = Column(Integer, default=5)  # 1-10

    # Automation details
    automation_recipe_json = Column(Text, default="{}")
    triggers_json = Column(Text, default="[]")
    actions_json = Column(Text, default="[]")

    # User feedback
    accepted_by = Column(String(36), ForeignKey("users.id"), nullable=True)
    accepted_at = Column(DateTime, nullable=True)
    rejection_reason = Column(Text, nullable=True)

    organization = relationship("Organization", backref="automation_patterns")
    accepted_user = relationship("User", backref="accepted_patterns")

    @property
    def automation_recipe(self):
        import json
        return json.loads(self.automation_recipe_json or "{}")

    @automation_recipe.setter
    def automation_recipe(self, value):
        import json
        self.automation_recipe_json = json.dumps(value)


class AIAgent(Base):
    """AI automation agent."""
    __tablename__ = "ai_agents"

    org_id = Column(String(36), ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False, index=True)
    pattern_id = Column(String(36), ForeignKey("automation_patterns.id"), nullable=True)

    # Agent info
    name = Column(String(200), nullable=False)
    description = Column(Text, nullable=True)
    status = Column(Enum(AgentStatus), default=AgentStatus.CREATED)

    # Configuration
    config_json = Column(Text, default="{}")
    permissions_json = Column(Text, default="[]")

    # Shadow mode tracking
    shadow_started_at = Column(DateTime, nullable=True)
    shadow_match_rate = Column(Float, nullable=True)
    shadow_runs = Column(Integer, default=0)

    # Performance
    total_runs = Column(Integer, default=0)
    successful_runs = Column(Integer, default=0)
    hours_saved_total = Column(Float, default=0)
    last_run_at = Column(DateTime, nullable=True)

    # Ownership
    created_by = Column(String(36), ForeignKey("users.id"), nullable=False)
    approved_by = Column(String(36), ForeignKey("users.id"), nullable=True)
    approved_at = Column(DateTime, nullable=True)

    organization = relationship("Organization", backref="ai_agents")
    pattern = relationship("AutomationPattern", backref="agents")
    creator = relationship("User", foreign_keys=[created_by], backref="created_agents")
    approver = relationship("User", foreign_keys=[approved_by], backref="approved_agents")


class AgentRun(Base):
    """Individual agent execution record."""
    __tablename__ = "agent_runs"

    agent_id = Column(String(36), ForeignKey("ai_agents.id", ondelete="CASCADE"), nullable=False, index=True)
    org_id = Column(String(36), ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False)

    # Execution
    started_at = Column(DateTime, default=datetime.utcnow)
    completed_at = Column(DateTime, nullable=True)
    status = Column(String(50), default="running")  # running, success, failed

    # Results
    input_data_json = Column(Text, default="{}")
    output_data_json = Column(Text, default="{}")
    error_message = Column(Text, nullable=True)

    # Shadow mode comparison
    is_shadow = Column(Boolean, default=False)
    human_action_json = Column(Text, nullable=True)
    matched_human = Column(Boolean, nullable=True)

    agent = relationship("AIAgent", backref="runs")
    organization = relationship("Organization", backref="agent_runs")

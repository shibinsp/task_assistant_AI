"""
TaskPulse - AI Assistant - Skill Model
Employee skill tracking and analysis
"""

import uuid
import enum
from datetime import datetime, timezone
from typing import Optional, List

from sqlalchemy import Column, String, Text, Boolean, ForeignKey, Integer, Float, DateTime
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.database import Base, CompatibleJSONB, CompatibleUUID, Enum


class SkillCategory(str, enum.Enum):
    """Skill categories."""
    TECHNICAL = "technical"
    PROCESS = "process"
    SOFT = "soft"
    DOMAIN = "domain"
    TOOL = "tool"
    LANGUAGE = "language"


class SkillTrend(str, enum.Enum):
    """Skill trend direction."""
    IMPROVING = "improving"
    STABLE = "stable"
    DECLINING = "declining"


class GapType(str, enum.Enum):
    """Type of skill gap."""
    CRITICAL = "critical"  # Must have for current role
    GROWTH = "growth"  # Needed for next level
    STRETCH = "stretch"  # Nice to have


class Skill(Base):
    """
    Master skill catalog.
    Organization-wide skill definitions.
    """

    __tablename__ = "skills"

    org_id = Column(
        CompatibleUUID,
        ForeignKey("organizations.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )

    # Skill info
    name = Column(String(200), nullable=False)
    description = Column(Text, nullable=True)
    category = Column(Enum(SkillCategory), default=SkillCategory.TECHNICAL)

    # Metadata (native JSONB)
    aliases = Column(CompatibleJSONB, default=[])  # Alternative names
    related_skills = Column(CompatibleJSONB, default=[])  # Related skill IDs
    prerequisites = Column(CompatibleJSONB, default=[])  # Prerequisite skill IDs

    # Benchmarks
    org_average_level = Column(Float, nullable=True)
    industry_average_level = Column(Float, nullable=True)

    # Status
    is_active = Column(Boolean, default=True)

    # Relationships
    organization = relationship("Organization", backref="skills")

    def __repr__(self) -> str:
        return f"<Skill(id={self.id}, name={self.name})>"


class UserSkill(Base):
    """
    User's skill profile.
    Tracks skill level and progression.
    """

    __tablename__ = "user_skills"

    user_id = Column(
        CompatibleUUID,
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    skill_id = Column(
        CompatibleUUID,
        ForeignKey("skills.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    org_id = Column(
        CompatibleUUID,
        ForeignKey("organizations.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )

    # Current assessment
    level = Column(Float, default=1.0)  # 1-10 scale
    confidence = Column(Float, default=0.5)  # 0-1, how confident in assessment
    trend = Column(Enum(SkillTrend), default=SkillTrend.STABLE)

    # Evidence
    last_demonstrated = Column(DateTime(timezone=True), nullable=True)
    demonstration_count = Column(Integer, default=0)
    source = Column(String(50), default="inferred")  # inferred, self_reported, manager_assessed, certification

    # History (native JSONB)
    level_history = Column(CompatibleJSONB, default=[])  # [{date, level}, ...]
    notes = Column(Text, nullable=True)

    # Certification
    is_certified = Column(Boolean, default=False)
    certification_date = Column(DateTime(timezone=True), nullable=True)
    certification_expiry = Column(DateTime(timezone=True), nullable=True)

    # Relationships
    user = relationship("User", backref="user_skills")
    skill = relationship("Skill", backref="user_skills")
    organization = relationship("Organization", backref="user_skills")

    def __repr__(self) -> str:
        return f"<UserSkill(user={self.user_id}, skill={self.skill_id}, level={self.level})>"

    def add_level_snapshot(self, new_level: float) -> None:
        """Add a level snapshot to history."""
        history = list(self.level_history or [])
        history.append({
            "date": datetime.now(timezone.utc).isoformat(),
            "level": new_level
        })
        # Keep last 50 entries
        self.level_history = history[-50:]
        self.level = new_level


class SkillGap(Base):
    """
    Identified skill gaps for users.
    """

    __tablename__ = "skill_gaps"

    user_id = Column(
        CompatibleUUID,
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    skill_id = Column(
        CompatibleUUID,
        ForeignKey("skills.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    org_id = Column(
        CompatibleUUID,
        ForeignKey("organizations.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )

    # Gap details
    gap_type = Column(Enum(GapType), default=GapType.GROWTH)
    current_level = Column(Float, nullable=True)
    required_level = Column(Float, nullable=False)
    gap_size = Column(Float, nullable=False)  # required - current

    # Context
    for_role = Column(String(200), nullable=True)  # Role requiring this skill
    priority = Column(Integer, default=5)  # 1-10, higher = more important
    identified_at = Column(DateTime(timezone=True), server_default=func.now())

    # Resolution
    is_resolved = Column(Boolean, default=False)
    resolved_at = Column(DateTime(timezone=True), nullable=True)

    # Recommendations (native JSONB)
    learning_resources = Column(CompatibleJSONB, default=[])

    # Relationships
    user = relationship("User", backref="skill_gaps")
    skill = relationship("Skill", backref="skill_gaps")

    def __repr__(self) -> str:
        return f"<SkillGap(user={self.user_id}, skill={self.skill_id}, gap={self.gap_size})>"


class SkillMetrics(Base):
    """
    Aggregated skill metrics for analytics.
    Snapshot of user's skill performance.
    """

    __tablename__ = "skill_metrics"

    user_id = Column(
        CompatibleUUID,
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    org_id = Column(
        CompatibleUUID,
        ForeignKey("organizations.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )

    # Period
    period_start = Column(DateTime(timezone=True), nullable=False)
    period_end = Column(DateTime(timezone=True), nullable=False)

    # Velocity metrics
    task_completion_velocity = Column(Float, nullable=True)  # Tasks per week
    quality_score = Column(Float, nullable=True)  # 0-1
    self_sufficiency_index = Column(Float, nullable=True)  # 0-1 (less help needed)
    learning_velocity = Column(Float, nullable=True)  # Skill improvement rate

    # Collaboration
    collaboration_score = Column(Float, nullable=True)  # 0-1
    help_given_count = Column(Integer, default=0)
    help_received_count = Column(Integer, default=0)

    # Blocker analysis
    blockers_encountered = Column(Integer, default=0)
    blockers_self_resolved = Column(Integer, default=0)
    avg_blocker_resolution_hours = Column(Float, nullable=True)

    # Peer comparison (percentile)
    velocity_percentile = Column(Float, nullable=True)  # 0-100
    quality_percentile = Column(Float, nullable=True)
    learning_percentile = Column(Float, nullable=True)

    # Relationships
    user = relationship("User", backref="skill_metrics")
    organization = relationship("Organization", backref="skill_metrics")

    def __repr__(self) -> str:
        return f"<SkillMetrics(user={self.user_id}, period={self.period_start})>"


class LearningPath(Base):
    """
    AI-generated learning paths for skill development.
    """

    __tablename__ = "learning_paths"

    user_id = Column(
        CompatibleUUID,
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    org_id = Column(
        CompatibleUUID,
        ForeignKey("organizations.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )

    # Path details
    title = Column(String(500), nullable=False)
    description = Column(Text, nullable=True)
    target_role = Column(String(200), nullable=True)

    # Skills to develop (native JSONB)
    skills_data = Column(CompatibleJSONB, default=[])  # [{skill_id, target_level}, ...]
    milestones = Column(CompatibleJSONB, default=[])  # Progress milestones

    # Progress
    progress_percentage = Column(Float, default=0.0)
    started_at = Column(DateTime(timezone=True), nullable=True)
    target_completion = Column(DateTime(timezone=True), nullable=True)
    completed_at = Column(DateTime(timezone=True), nullable=True)

    # Status
    is_active = Column(Boolean, default=True)
    is_ai_generated = Column(Boolean, default=True)

    # Relationships
    user = relationship("User", backref="learning_paths")
    organization = relationship("Organization", backref="learning_paths")

    def __repr__(self) -> str:
        return f"<LearningPath(user={self.user_id}, title={self.title[:30]})>"

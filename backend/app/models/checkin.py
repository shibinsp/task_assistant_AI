"""
TaskPulse - AI Assistant - Check-In Model
Smart check-in system for proactive task monitoring
"""

from sqlalchemy import Column, String, Enum, Text, Boolean, ForeignKey, Integer, Float, DateTime
from sqlalchemy.orm import relationship
import enum
from datetime import datetime
from typing import Optional

from app.database import Base


class CheckInTrigger(str, enum.Enum):
    """What triggered the check-in."""
    SCHEDULED = "scheduled"  # Regular interval check-in
    PROGRESS_STALL = "progress_stall"  # No progress detected
    DEADLINE_APPROACHING = "deadline_approaching"  # Task deadline is near
    MANUAL = "manual"  # User or manager requested
    BLOCKER_DETECTED = "blocker_detected"  # System detected potential blocker
    STATUS_CHANGE = "status_change"  # Task status changed to blocked


class CheckInStatus(str, enum.Enum):
    """Check-in response status."""
    PENDING = "pending"  # Awaiting response
    RESPONDED = "responded"  # User has responded
    SKIPPED = "skipped"  # User skipped (within grace period)
    EXPIRED = "expired"  # No response within time window
    ESCALATED = "escalated"  # Escalated to manager


class ProgressIndicator(str, enum.Enum):
    """User's self-reported progress."""
    ON_TRACK = "on_track"
    SLIGHTLY_BEHIND = "slightly_behind"
    SIGNIFICANTLY_BEHIND = "significantly_behind"
    BLOCKED = "blocked"
    AHEAD = "ahead"
    COMPLETED = "completed"


class CheckIn(Base):
    """
    Check-in record for proactive task monitoring.
    The core of the "no stuck for more than 3 hours" philosophy.
    """

    __tablename__ = "checkins"

    # Relationships
    task_id = Column(
        String(36),
        ForeignKey("tasks.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    user_id = Column(
        String(36),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
        index=True
    )
    org_id = Column(
        String(36),
        ForeignKey("organizations.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )

    # Check-in metadata
    cycle_number = Column(Integer, default=1)  # Which check-in cycle (1st, 2nd, etc.)
    trigger = Column(Enum(CheckInTrigger), default=CheckInTrigger.SCHEDULED)
    status = Column(Enum(CheckInStatus), default=CheckInStatus.PENDING, index=True)

    # Timing
    scheduled_at = Column(DateTime, nullable=False)
    responded_at = Column(DateTime, nullable=True)
    expires_at = Column(DateTime, nullable=True)

    # User response
    progress_indicator = Column(Enum(ProgressIndicator), nullable=True)
    progress_notes = Column(Text, nullable=True)
    completed_since_last = Column(Text, nullable=True)  # What was accomplished
    blockers_reported = Column(Text, nullable=True)  # User-reported blockers
    help_needed = Column(Boolean, default=False)
    estimated_completion_change = Column(Float, nullable=True)  # Hours adjusted

    # AI analysis
    ai_suggestion = Column(Text, nullable=True)  # AI-generated help
    ai_confidence = Column(Float, nullable=True)  # AI confidence in suggestion
    sentiment_score = Column(Float, nullable=True)  # Detected sentiment (-1 to 1)
    friction_detected = Column(Boolean, default=False)

    # Escalation
    escalated = Column(Boolean, default=False)
    escalated_to = Column(String(36), ForeignKey("users.id"), nullable=True)
    escalated_at = Column(DateTime, nullable=True)
    escalation_reason = Column(Text, nullable=True)

    # Relationships
    task = relationship("Task", backref="checkins")
    user = relationship("User", foreign_keys=[user_id], backref="checkins")
    organization = relationship("Organization", backref="checkins")
    escalated_user = relationship("User", foreign_keys=[escalated_to])

    def __repr__(self) -> str:
        return f"<CheckIn(id={self.id}, task={self.task_id}, status={self.status})>"

    @property
    def is_overdue(self) -> bool:
        """Check if response is overdue."""
        if self.status != CheckInStatus.PENDING:
            return False
        if not self.expires_at:
            return False
        return datetime.utcnow() > self.expires_at

    @property
    def response_time_minutes(self) -> Optional[int]:
        """Time taken to respond in minutes."""
        if not self.responded_at:
            return None
        delta = self.responded_at - self.scheduled_at
        return int(delta.total_seconds() / 60)


class CheckInConfig(Base):
    """
    Check-in configuration per team/user/task level.
    Allows customization of check-in behavior.
    """

    __tablename__ = "checkin_configs"

    org_id = Column(
        String(36),
        ForeignKey("organizations.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )

    # Scope - one of these should be set (null = org-wide default)
    team_id = Column(String(36), nullable=True, index=True)
    user_id = Column(String(36), ForeignKey("users.id"), nullable=True, index=True)
    task_id = Column(String(36), ForeignKey("tasks.id"), nullable=True, index=True)

    # Check-in settings
    interval_hours = Column(Float, default=3.0)  # Hours between check-ins
    enabled = Column(Boolean, default=True)
    silent_mode_threshold = Column(Float, default=0.8)  # Progress % to skip check-in
    max_daily_checkins = Column(Integer, default=4)

    # Working hours (to not disturb outside work time)
    work_start_hour = Column(Integer, default=9)  # 9 AM
    work_end_hour = Column(Integer, default=18)  # 6 PM
    respect_timezone = Column(Boolean, default=True)
    excluded_days = Column(String(50), default="0,6")  # 0=Sunday, 6=Saturday

    # Escalation settings
    auto_escalate_after_missed = Column(Integer, default=2)  # Escalate after N missed
    escalate_to_manager = Column(Boolean, default=True)

    # AI settings
    ai_suggestions_enabled = Column(Boolean, default=True)
    ai_sentiment_analysis = Column(Boolean, default=True)

    # Relationships
    organization = relationship("Organization", backref="checkin_configs")
    user = relationship("User", backref="checkin_config")
    task = relationship("Task", backref="checkin_config")

    def __repr__(self) -> str:
        scope = "org"
        if self.team_id:
            scope = f"team:{self.team_id}"
        elif self.user_id:
            scope = f"user:{self.user_id}"
        elif self.task_id:
            scope = f"task:{self.task_id}"
        return f"<CheckInConfig(id={self.id}, scope={scope}, interval={self.interval_hours}h)>"


class CheckInReminder(Base):
    """
    Reminder sent for pending check-ins.
    Tracks notification history.
    """

    __tablename__ = "checkin_reminders"

    checkin_id = Column(
        String(36),
        ForeignKey("checkins.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    user_id = Column(
        String(36),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True
    )

    reminder_number = Column(Integer, default=1)  # 1st, 2nd reminder
    channel = Column(String(50), default="in_app")  # in_app, email, slack, etc.
    sent_at = Column(DateTime, default=datetime.utcnow)
    acknowledged = Column(Boolean, default=False)
    acknowledged_at = Column(DateTime, nullable=True)

    # Relationships
    checkin = relationship("CheckIn", backref="reminders")
    user = relationship("User", backref="checkin_reminders")

    def __repr__(self) -> str:
        return f"<CheckInReminder(checkin={self.checkin_id}, number={self.reminder_number})>"

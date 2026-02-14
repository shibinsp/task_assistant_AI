"""
TaskPulse - AI Assistant - Notification & Integration Models
Communication and external system connections
"""

from sqlalchemy import Column, String, Enum, Text, Boolean, ForeignKey, Integer, Float, DateTime
from sqlalchemy.orm import relationship, backref
import enum
from datetime import datetime

from app.database import Base


class NotificationType(str, enum.Enum):
    """Types of notifications."""
    CHECKIN_REMINDER = "checkin_reminder"
    TASK_ASSIGNED = "task_assigned"
    TASK_COMPLETED = "task_completed"
    TASK_BLOCKED = "task_blocked"
    ESCALATION = "escalation"
    DEADLINE_APPROACHING = "deadline_approaching"
    AI_SUGGESTION = "ai_suggestion"
    MENTION = "mention"
    SYSTEM = "system"


class NotificationChannel(str, enum.Enum):
    """Notification delivery channels."""
    IN_APP = "in_app"
    EMAIL = "email"
    SLACK = "slack"
    TEAMS = "teams"
    WEBHOOK = "webhook"


class NotificationPriority(str, enum.Enum):
    """Notification priority levels."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    URGENT = "urgent"


class IntegrationType(str, enum.Enum):
    """Types of integrations."""
    JIRA = "jira"
    GITHUB = "github"
    GITLAB = "gitlab"
    SLACK = "slack"
    TEAMS = "teams"
    CONFLUENCE = "confluence"
    NOTION = "notion"
    CUSTOM_WEBHOOK = "custom_webhook"


class IntegrationStatus(str, enum.Enum):
    """Integration connection status."""
    PENDING = "pending"
    ACTIVE = "active"
    ERROR = "error"
    DISCONNECTED = "disconnected"


class Notification(Base):
    """User notification."""
    __tablename__ = "notifications"

    user_id = Column(String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    org_id = Column(String(36), ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False, index=True)

    notification_type = Column(Enum(NotificationType), nullable=False)
    title = Column(String(500), nullable=False)
    message = Column(Text, nullable=True)

    # Related entities
    task_id = Column(String(36), ForeignKey("tasks.id"), nullable=True)
    checkin_id = Column(String(36), ForeignKey("checkins.id"), nullable=True)

    # Status
    is_read = Column(Boolean, default=False)
    read_at = Column(DateTime, nullable=True)

    # Delivery
    channel = Column(Enum(NotificationChannel), default=NotificationChannel.IN_APP)
    delivered = Column(Boolean, default=False)
    delivered_at = Column(DateTime, nullable=True)

    # Action
    action_url = Column(String(1000), nullable=True)
    action_data_json = Column(Text, default="{}")

    user = relationship("User", backref="notifications")
    organization = relationship("Organization", backref="notifications")
    task = relationship("Task", backref=backref("notifications", passive_deletes=True))
    checkin = relationship("CheckIn", backref="notifications")


class NotificationPreference(Base):
    """User notification preferences."""
    __tablename__ = "notification_preferences"

    user_id = Column(String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    org_id = Column(String(36), ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False)

    notification_type = Column(Enum(NotificationType), nullable=False)
    channel = Column(Enum(NotificationChannel), nullable=False)

    enabled = Column(Boolean, default=True)
    quiet_hours_start = Column(Integer, nullable=True)  # Hour 0-23
    quiet_hours_end = Column(Integer, nullable=True)
    batch_frequency_minutes = Column(Integer, default=0)  # 0 = immediate

    user = relationship("User", backref="notification_preferences")
    organization = relationship("Organization", backref="notification_preferences")


class Integration(Base):
    """External integration configuration."""
    __tablename__ = "integrations"

    org_id = Column(String(36), ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False, index=True)

    integration_type = Column(Enum(IntegrationType), nullable=False)
    name = Column(String(200), nullable=False)
    description = Column(Text, nullable=True)

    # Connection
    is_active = Column(Boolean, default=False)
    config_json = Column(Text, default="{}")  # Encrypted in production
    credentials_json = Column(Text, default="{}")  # Encrypted

    # Sync
    sync_enabled = Column(Boolean, default=True)
    last_sync_at = Column(DateTime, nullable=True)
    last_sync_status = Column(String(50), nullable=True)
    sync_error = Column(Text, nullable=True)

    # OAuth
    oauth_access_token = Column(Text, nullable=True)  # Encrypted
    oauth_refresh_token = Column(Text, nullable=True)  # Encrypted
    oauth_expires_at = Column(DateTime, nullable=True)

    connected_by = Column(String(36), ForeignKey("users.id"), nullable=True)
    connected_at = Column(DateTime, nullable=True)

    organization = relationship("Organization", backref="integrations")
    connector = relationship("User", backref="connected_integrations")

    @property
    def config(self):
        import json
        return json.loads(self.config_json or "{}")

    @config.setter
    def config(self, value):
        import json
        self.config_json = json.dumps(value)


class Webhook(Base):
    """Outbound webhook configuration."""
    __tablename__ = "webhooks"

    org_id = Column(String(36), ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False, index=True)

    name = Column(String(200), nullable=False)
    url = Column(String(2000), nullable=False)
    secret = Column(String(255), nullable=True)  # For signature verification

    # Events
    events_json = Column(Text, default="[]")  # List of event types to trigger

    # Status
    is_active = Column(Boolean, default=True)

    # Headers
    headers_json = Column(Text, default="{}")

    # Stats
    total_deliveries = Column(Integer, default=0)
    successful_deliveries = Column(Integer, default=0)
    last_delivery_at = Column(DateTime, nullable=True)
    last_delivery_status = Column(Integer, nullable=True)

    created_by = Column(String(36), ForeignKey("users.id"), nullable=False)

    organization = relationship("Organization", backref="webhooks")
    creator = relationship("User", backref="created_webhooks")

    @property
    def events(self):
        import json
        return json.loads(self.events_json or "[]")

    @events.setter
    def events(self, value):
        import json
        self.events_json = json.dumps(value)


class WebhookDelivery(Base):
    """Webhook delivery log."""
    __tablename__ = "webhook_deliveries"

    webhook_id = Column(String(36), ForeignKey("webhooks.id", ondelete="CASCADE"), nullable=False, index=True)
    org_id = Column(String(36), ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False)

    event_type = Column(String(100), nullable=False)
    payload_json = Column(Text, default="{}")

    # Delivery
    attempted_at = Column(DateTime, default=datetime.utcnow)
    response_status = Column(Integer, nullable=True)
    response_body = Column(Text, nullable=True)
    response_time_ms = Column(Integer, nullable=True)

    # Retry
    retry_count = Column(Integer, default=0)
    next_retry_at = Column(DateTime, nullable=True)
    is_successful = Column(Boolean, default=False)

    webhook = relationship("Webhook", backref="deliveries")
    organization = relationship("Organization", backref="webhook_deliveries")

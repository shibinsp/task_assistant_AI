"""
TaskPulse - AI Assistant - Audit & Admin Models
Security, compliance, and admin features
"""

from sqlalchemy import Column, String, Enum, Text, Boolean, ForeignKey, Integer, Float, DateTime
from sqlalchemy.orm import relationship
import enum
from datetime import datetime

from app.database import Base


class ActorType(str, enum.Enum):
    """Who performed the action."""
    USER = "user"
    ADMIN = "admin"
    SYSTEM = "system"
    AI = "ai"
    API = "api"
    INTEGRATION = "integration"


class AuditAction(str, enum.Enum):
    """Types of auditable actions."""
    # Auth
    LOGIN = "login"
    LOGOUT = "logout"
    PASSWORD_CHANGE = "password_change"
    MFA_ENABLED = "mfa_enabled"

    # CRUD
    CREATE = "create"
    READ = "read"
    UPDATE = "update"
    DELETE = "delete"

    # Admin
    ROLE_CHANGE = "role_change"
    PERMISSION_CHANGE = "permission_change"
    CONFIG_CHANGE = "config_change"

    # Data
    EXPORT = "export"
    IMPORT = "import"

    # GDPR
    DATA_REQUEST = "data_request"
    DATA_DELETION = "data_deletion"


class AuditLog(Base):
    """Immutable audit log entry."""
    __tablename__ = "audit_logs"

    org_id = Column(String(36), ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False, index=True)

    # Actor
    actor_type = Column(Enum(ActorType), nullable=False)
    actor_id = Column(String(36), nullable=True)  # User/system ID
    actor_name = Column(String(200), nullable=True)

    # Action
    action = Column(Enum(AuditAction), nullable=False)
    resource_type = Column(String(100), nullable=False)  # user, task, org, etc.
    resource_id = Column(String(36), nullable=True)

    # Details
    description = Column(Text, nullable=True)
    old_value_json = Column(Text, nullable=True)
    new_value_json = Column(Text, nullable=True)
    metadata_json = Column(Text, default="{}")

    # Context
    ip_address = Column(String(45), nullable=True)
    user_agent = Column(String(500), nullable=True)
    request_id = Column(String(36), nullable=True)

    # Timestamp (not using updated_at for immutability)
    timestamp = Column(DateTime, default=datetime.utcnow, index=True)

    organization = relationship("Organization", backref="audit_logs")

    @property
    def extra_data(self):
        import json
        return json.loads(self.metadata_json or "{}")


class GDPRRequest(Base):
    """GDPR data request tracking."""
    __tablename__ = "gdpr_requests"

    org_id = Column(String(36), ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False, index=True)
    user_id = Column(String(36), ForeignKey("users.id"), nullable=False, index=True)

    request_type = Column(String(50), nullable=False)  # export, erasure, access, rectification
    status = Column(String(50), default="pending")  # pending, processing, completed, failed

    # Processing
    requested_at = Column(DateTime, default=datetime.utcnow)
    processed_at = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)
    processed_by = Column(String(36), ForeignKey("users.id"), nullable=True)

    # Result
    result_url = Column(String(2000), nullable=True)  # For export downloads
    result_expiry = Column(DateTime, nullable=True)
    error_message = Column(Text, nullable=True)

    # Verification
    verification_token = Column(String(255), nullable=True)
    verified_at = Column(DateTime, nullable=True)

    organization = relationship("Organization", backref="gdpr_requests")
    user = relationship("User", foreign_keys=[user_id], backref="gdpr_requests")
    processor = relationship("User", foreign_keys=[processed_by])


class APIKey(Base):
    """API key for programmatic access."""
    __tablename__ = "api_keys"

    org_id = Column(String(36), ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False, index=True)
    user_id = Column(String(36), ForeignKey("users.id"), nullable=False)

    name = Column(String(200), nullable=False)
    key_hash = Column(String(255), nullable=False)  # Only store hash
    key_prefix = Column(String(10), nullable=False)  # For identification

    # Permissions
    scopes_json = Column(Text, default="[]")  # Specific permissions
    is_full_access = Column(Boolean, default=False)

    # Status
    is_active = Column(Boolean, default=True)
    expires_at = Column(DateTime, nullable=True)

    # Usage
    last_used_at = Column(DateTime, nullable=True)
    last_used_ip = Column(String(45), nullable=True)
    usage_count = Column(Integer, default=0)

    # Limits
    rate_limit = Column(Integer, default=1000)  # Requests per hour
    current_usage = Column(Integer, default=0)
    usage_reset_at = Column(DateTime, nullable=True)

    created_by = Column(String(36), ForeignKey("users.id"), nullable=False)

    organization = relationship("Organization", backref="api_keys")
    owner = relationship("User", foreign_keys=[user_id], backref="api_keys")
    creator = relationship("User", foreign_keys=[created_by])

    @property
    def scopes(self):
        import json
        return json.loads(self.scopes_json or "[]")

    @scopes.setter
    def scopes(self, value):
        import json
        self.scopes_json = json.dumps(value)


class SystemHealth(Base):
    """System health monitoring snapshots."""
    __tablename__ = "system_health"

    snapshot_time = Column(DateTime, default=datetime.utcnow, index=True)

    # Database
    db_connections_active = Column(Integer, nullable=True)
    db_query_avg_ms = Column(Float, nullable=True)

    # API
    api_requests_per_minute = Column(Integer, nullable=True)
    api_error_rate = Column(Float, nullable=True)
    api_latency_p50_ms = Column(Float, nullable=True)
    api_latency_p99_ms = Column(Float, nullable=True)

    # AI
    ai_requests_per_hour = Column(Integer, nullable=True)
    ai_avg_latency_ms = Column(Float, nullable=True)
    ai_cache_hit_rate = Column(Float, nullable=True)

    # Background jobs
    jobs_pending = Column(Integer, nullable=True)
    jobs_failed = Column(Integer, nullable=True)

    # Storage
    storage_used_mb = Column(Float, nullable=True)

    # Alerts
    active_alerts_json = Column(Text, default="[]")

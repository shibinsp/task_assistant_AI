"""
TaskPulse - AI Assistant - User Model
User management with role-based access control
"""

from sqlalchemy import (
    Column, String, Text, Boolean, ForeignKey, DateTime,
    Integer, UniqueConstraint, func
)
from sqlalchemy.dialects.postgresql import UUID as PG_UUID, JSONB
from sqlalchemy.orm import relationship
import enum
from datetime import datetime

from app.database import Base, Enum


class UserRole(str, enum.Enum):
    """User roles for RBAC."""
    SUPER_ADMIN = "super_admin"
    ORG_ADMIN = "org_admin"
    MANAGER = "manager"
    TEAM_LEAD = "team_lead"
    EMPLOYEE = "employee"
    VIEWER = "viewer"


class SkillLevel(str, enum.Enum):
    """Employee skill/seniority level."""
    JUNIOR = "junior"
    MID = "mid"
    SENIOR = "senior"
    LEAD = "lead"


class User(Base):
    """
    User model with authentication and profile data.
    Users belong to an organization and have specific roles.
    """

    __tablename__ = "users"

    # Organization relationship
    org_id = Column(
        PG_UUID(as_uuid=True),
        ForeignKey("organizations.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )

    # Authentication
    email = Column(String(255), nullable=False, index=True)
    password_hash = Column(String(255), nullable=True)  # Null for SSO-only users
    is_sso_user = Column(Boolean, default=False)
    supabase_auth_id = Column(PG_UUID(as_uuid=True), unique=True, index=True, nullable=True)

    # Profile
    first_name = Column(String(100), nullable=False)
    last_name = Column(String(100), nullable=False)
    avatar_url = Column(String(500), nullable=True)
    phone = Column(String(50), nullable=True)
    timezone = Column(String(50), default="UTC", nullable=False)

    # Role and permissions
    role = Column(
        Enum(UserRole),
        default=UserRole.EMPLOYEE,
        nullable=False
    )
    skill_level = Column(
        Enum(SkillLevel),
        default=SkillLevel.MID,
        nullable=False
    )

    # Team/reporting structure
    team_id = Column(PG_UUID(as_uuid=True), nullable=True, index=True)
    manager_id = Column(
        PG_UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True
    )

    # GDPR consent tracking
    consent_data = Column(JSONB, default={})

    # Status
    is_active = Column(Boolean, default=True, nullable=False)
    is_email_verified = Column(Boolean, default=False)
    last_login = Column(DateTime(timezone=True), nullable=True)
    failed_login_attempts = Column(Integer, default=0)
    lockout_until = Column(DateTime(timezone=True), nullable=True)  # Account lockout after failed attempts

    # Relationships
    organization = relationship("Organization", back_populates="users")
    direct_reports = relationship(
        "User",
        backref="manager_ref",
        remote_side="User.id",
        foreign_keys=[manager_id]
    )

    # Index for unique email per organization
    __table_args__ = (
        UniqueConstraint('org_id', 'email', name='uq_user_org_email'),
    )

    def __repr__(self) -> str:
        return f"<User(id={self.id}, email={self.email}, role={self.role})>"

    @property
    def full_name(self) -> str:
        """Get user's full name."""
        return f"{self.first_name} {self.last_name}"

    @property
    def consent(self) -> dict:
        return self.consent_data or {}

    @consent.setter
    def consent(self, value: dict) -> None:
        self.consent_data = value

    @property
    def has_ai_monitoring_consent(self) -> bool:
        """Check if user has consented to AI monitoring."""
        return self.consent.get("ai_monitoring", False)

    @property
    def has_skill_tracking_consent(self) -> bool:
        """Check if user has consented to skill tracking."""
        return self.consent.get("skill_tracking", False)

    def update_consent(self, consent_type: str, value: bool) -> None:
        """Update a specific consent value."""
        current_consent = self.consent
        current_consent[consent_type] = value
        current_consent[f"{consent_type}_updated_at"] = datetime.utcnow().isoformat()
        self.consent = current_consent

    @property
    def is_admin(self) -> bool:
        """Check if user has admin role."""
        return self.role in (UserRole.SUPER_ADMIN, UserRole.ORG_ADMIN)

    @property
    def is_manager_or_above(self) -> bool:
        """Check if user is manager or higher."""
        return self.role in (
            UserRole.SUPER_ADMIN,
            UserRole.ORG_ADMIN,
            UserRole.MANAGER,
            UserRole.TEAM_LEAD
        )

    @property
    def can_assign_tasks(self) -> bool:
        """Check if user can assign tasks to others."""
        return self.role in (
            UserRole.SUPER_ADMIN,
            UserRole.ORG_ADMIN,
            UserRole.MANAGER,
            UserRole.TEAM_LEAD
        )

    def get_role_hierarchy_level(self) -> int:
        """Get numeric hierarchy level for role comparison."""
        levels = {
            UserRole.SUPER_ADMIN: 100,
            UserRole.ORG_ADMIN: 90,
            UserRole.MANAGER: 70,
            UserRole.TEAM_LEAD: 60,
            UserRole.EMPLOYEE: 40,
            UserRole.VIEWER: 10
        }
        return levels.get(self.role, 0)

    def can_manage_user(self, other_user: "User") -> bool:
        """Check if this user can manage another user."""
        # Super admin can manage everyone
        if self.role == UserRole.SUPER_ADMIN:
            return True

        # Must be in same organization
        if self.org_id != other_user.org_id:
            return False

        # Org admin can manage all in their org except super admins
        if self.role == UserRole.ORG_ADMIN:
            return other_user.role != UserRole.SUPER_ADMIN

        # Managers can only manage their direct reports
        if self.role in (UserRole.MANAGER, UserRole.TEAM_LEAD):
            return other_user.manager_id == self.id

        return False

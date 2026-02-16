"""
TaskPulse - AI Assistant - User Schemas
Pydantic schemas for user and authentication API validation
"""

from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field, EmailStr, field_validator

from app.models.user import UserRole, SkillLevel


# ==================== Base Schemas ====================

class UserBase(BaseModel):
    """Base user schema with common fields."""
    email: EmailStr = Field(..., description="User email address")
    first_name: str = Field(..., min_length=1, max_length=100, description="First name")
    last_name: str = Field(..., min_length=1, max_length=100, description="Last name")


# ==================== Authentication Schemas ====================

class UserRegister(UserBase):
    """Schema for user registration."""
    password: str = Field(..., min_length=8, max_length=128, description="Password")
    org_name: Optional[str] = Field(None, min_length=2, max_length=255, description="Organization name for new org")
    org_id: Optional[str] = Field(None, description="Organization ID to join existing org")
    invite_code: Optional[str] = Field(None, description="Invitation code")
    role: Optional[UserRole] = Field(None, description="Desired role (cannot be admin)")

    @field_validator("role")
    @classmethod
    def validate_role(cls, v: Optional[UserRole]) -> Optional[UserRole]:
        """Prevent signup with admin roles."""
        if v and v in (UserRole.SUPER_ADMIN, UserRole.ORG_ADMIN):
            raise ValueError("Cannot register as an admin role")
        return v

    @field_validator("password")
    @classmethod
    def validate_password(cls, v: str) -> str:
        """Validate password strength."""
        import re
        if len(v) < 8:
            raise ValueError("Password must be at least 8 characters")
        if not re.search(r'[A-Z]', v):
            raise ValueError("Password must contain at least one uppercase letter")
        if not re.search(r'[a-z]', v):
            raise ValueError("Password must contain at least one lowercase letter")
        if not re.search(r'\d', v):
            raise ValueError("Password must contain at least one digit")
        return v


class UserLogin(BaseModel):
    """Schema for user login."""
    email: EmailStr = Field(..., description="User email address")
    password: str = Field(..., description="User password")


class TokenResponse(BaseModel):
    """Schema for authentication token response."""
    access_token: str = Field(..., description="JWT access token")
    refresh_token: str = Field(..., description="JWT refresh token")
    token_type: str = Field(default="bearer", description="Token type")
    expires_in: int = Field(..., description="Access token expiration in seconds")


class TokenRefresh(BaseModel):
    """Schema for token refresh request."""
    refresh_token: str = Field(..., description="Refresh token")


class PasswordReset(BaseModel):
    """Schema for password reset request."""
    email: EmailStr = Field(..., description="User email address")


class PasswordResetConfirm(BaseModel):
    """Schema for password reset confirmation."""
    token: str = Field(..., description="Password reset token")
    new_password: str = Field(..., min_length=8, max_length=128, description="New password")

    @field_validator("new_password")
    @classmethod
    def validate_password(cls, v: str) -> str:
        """Validate password strength."""
        import re
        if len(v) < 8:
            raise ValueError("Password must be at least 8 characters")
        if not re.search(r'[A-Z]', v):
            raise ValueError("Password must contain at least one uppercase letter")
        if not re.search(r'[a-z]', v):
            raise ValueError("Password must contain at least one lowercase letter")
        if not re.search(r'\d', v):
            raise ValueError("Password must contain at least one digit")
        return v


class PasswordChange(BaseModel):
    """Schema for password change."""
    current_password: str = Field(..., description="Current password")
    new_password: str = Field(..., min_length=8, max_length=128, description="New password")

    @field_validator("new_password")
    @classmethod
    def validate_password(cls, v: str) -> str:
        """Validate password strength."""
        import re
        if len(v) < 8:
            raise ValueError("Password must be at least 8 characters")
        if not re.search(r'[A-Z]', v):
            raise ValueError("Password must contain at least one uppercase letter")
        if not re.search(r'[a-z]', v):
            raise ValueError("Password must contain at least one lowercase letter")
        if not re.search(r'\d', v):
            raise ValueError("Password must contain at least one digit")
        return v


# ==================== Create Schemas ====================

class UserCreate(UserBase):
    """Schema for creating a new user (admin)."""
    password: Optional[str] = Field(None, min_length=8, max_length=128)
    role: UserRole = Field(default=UserRole.EMPLOYEE)
    skill_level: SkillLevel = Field(default=SkillLevel.MID)
    team_id: Optional[str] = None
    manager_id: Optional[str] = None
    timezone: str = Field(default="UTC")
    is_sso_user: bool = Field(default=False)


# ==================== Update Schemas ====================

class UserUpdate(BaseModel):
    """Schema for updating a user."""
    first_name: Optional[str] = Field(None, min_length=1, max_length=100)
    last_name: Optional[str] = Field(None, min_length=1, max_length=100)
    phone: Optional[str] = Field(None, max_length=50)
    timezone: Optional[str] = None
    avatar_url: Optional[str] = Field(None, max_length=500)


class UserAdminUpdate(UserUpdate):
    """Schema for admin updating a user."""
    role: Optional[UserRole] = None
    skill_level: Optional[SkillLevel] = None
    team_id: Optional[str] = None
    manager_id: Optional[str] = None
    is_active: Optional[bool] = None


# ==================== Consent Schemas ====================

class ConsentUpdate(BaseModel):
    """Schema for updating user consent."""
    ai_monitoring: Optional[bool] = Field(None, description="Consent for AI monitoring")
    skill_tracking: Optional[bool] = Field(None, description="Consent for skill tracking")
    analytics: Optional[bool] = Field(None, description="Consent for analytics")
    marketing: Optional[bool] = Field(None, description="Consent for marketing communications")


class ConsentResponse(BaseModel):
    """Schema for consent status response."""
    ai_monitoring: bool = False
    ai_monitoring_updated_at: Optional[str] = None
    skill_tracking: bool = False
    skill_tracking_updated_at: Optional[str] = None
    analytics: bool = False
    analytics_updated_at: Optional[str] = None
    marketing: bool = False
    marketing_updated_at: Optional[str] = None


# ==================== Response Schemas ====================

class UserResponse(UserBase):
    """Schema for user in API responses."""
    id: str
    org_id: str
    role: UserRole
    skill_level: SkillLevel
    timezone: str
    is_active: bool
    is_email_verified: bool
    avatar_url: Optional[str] = None
    created_at: datetime

    model_config = {"from_attributes": True}

    @property
    def full_name(self) -> str:
        return f"{self.first_name} {self.last_name}"


class UserDetailResponse(UserResponse):
    """Detailed user response with additional info."""
    phone: Optional[str] = None
    team_id: Optional[str] = None
    manager_id: Optional[str] = None
    last_login: Optional[datetime] = None
    consent: ConsentResponse = Field(default_factory=ConsentResponse)
    updated_at: datetime

    model_config = {"from_attributes": True}


class UserListResponse(BaseModel):
    """Response for list of users."""
    users: list[UserResponse]
    total: int
    page: int
    page_size: int


class CurrentUserResponse(UserDetailResponse):
    """Response for current authenticated user."""
    organization_name: str
    organization_plan: str
    permissions: list[str] = Field(default_factory=list)


# ==================== Session Schemas ====================

class SessionResponse(BaseModel):
    """Schema for session in API responses."""
    id: str
    device_info: Optional[str] = None
    ip_address: Optional[str] = None
    last_activity: datetime
    created_at: datetime
    is_current: bool = False

    model_config = {"from_attributes": True}


class SessionListResponse(BaseModel):
    """Response for list of sessions."""
    sessions: list[SessionResponse]
    total: int

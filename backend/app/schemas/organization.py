"""
TaskPulse - AI Assistant - Organization Schemas
Pydantic schemas for organization API validation
"""

from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field, field_validator

from app.models.organization import PlanTier


# ==================== Base Schemas ====================

class OrganizationBase(BaseModel):
    """Base organization schema with common fields."""
    name: str = Field(..., min_length=2, max_length=255, description="Organization name")
    description: Optional[str] = Field(None, max_length=1000, description="Organization description")


# ==================== Create Schemas ====================

class OrganizationCreate(OrganizationBase):
    """Schema for creating a new organization."""
    slug: Optional[str] = Field(None, min_length=3, max_length=100, description="URL-friendly identifier")
    plan: PlanTier = Field(default=PlanTier.STARTER, description="Subscription plan tier")
    settings: Optional[dict] = Field(default_factory=dict, description="Organization settings")

    @field_validator("slug")
    @classmethod
    def validate_slug(cls, v: Optional[str]) -> Optional[str]:
        if v is None:
            return v
        # Ensure slug is lowercase and contains only valid characters
        import re
        if not re.match(r'^[a-z0-9]+(-[a-z0-9]+)*$', v):
            raise ValueError("Slug must be lowercase alphanumeric with hyphens only")
        return v


# ==================== Update Schemas ====================

class OrganizationUpdate(BaseModel):
    """Schema for updating an organization."""
    name: Optional[str] = Field(None, min_length=2, max_length=255)
    description: Optional[str] = Field(None, max_length=1000)
    settings: Optional[dict] = None
    is_active: Optional[bool] = None


class OrganizationPlanUpdate(BaseModel):
    """Schema for updating organization plan (admin only)."""
    plan: PlanTier


# ==================== Response Schemas ====================

class OrganizationResponse(OrganizationBase):
    """Schema for organization in API responses."""
    id: str
    slug: str
    plan: PlanTier
    is_active: bool
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class OrganizationDetailResponse(OrganizationResponse):
    """Detailed organization response with additional info."""
    settings: dict = Field(default_factory=dict)
    features: dict = Field(default_factory=dict)
    max_users: int
    user_count: Optional[int] = None

    model_config = {"from_attributes": True}


class OrganizationListResponse(BaseModel):
    """Response for list of organizations."""
    organizations: list[OrganizationResponse]
    total: int
    page: int
    page_size: int


# ==================== Settings Schemas ====================

class CheckInSettings(BaseModel):
    """Check-in engine settings."""
    interval_hours: int = Field(default=3, ge=1, le=8)
    enabled: bool = Field(default=True)
    silent_mode_threshold: float = Field(default=0.8, ge=0, le=1)


class NotificationSettings(BaseModel):
    """Notification settings."""
    email_enabled: bool = True
    slack_enabled: bool = False
    teams_enabled: bool = False
    in_app_enabled: bool = True


class OrganizationSettings(BaseModel):
    """Complete organization settings schema."""
    checkin: CheckInSettings = Field(default_factory=CheckInSettings)
    notifications: NotificationSettings = Field(default_factory=NotificationSettings)
    timezone: str = Field(default="UTC")
    working_hours_start: str = Field(default="09:00")
    working_hours_end: str = Field(default="17:00")
    working_days: list[int] = Field(default=[1, 2, 3, 4, 5])  # Monday=1 to Friday=5

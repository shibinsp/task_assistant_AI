"""
TaskPulse - AI Assistant - Notification Schemas
Pydantic schemas for notifications, preferences, and webhooks
"""

from datetime import datetime
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field

from app.models.notification import NotificationType, NotificationChannel, IntegrationType


# ==================== Notification Schemas ====================

class NotificationCreate(BaseModel):
    """Schema for creating a notification."""
    type: NotificationType = Field(..., description="Notification type")
    title: str = Field(..., min_length=1, max_length=200, description="Notification title")
    message: str = Field(..., description="Notification message")
    data: Dict[str, Any] = Field(default_factory=dict, description="Additional data")
    link: Optional[str] = Field(None, max_length=500, description="Link URL")
    priority: str = Field(default="normal", description="Priority: low, normal, high, urgent")


class NotificationUpdate(BaseModel):
    """Schema for updating a notification."""
    is_read: Optional[bool] = None


class NotificationResponse(BaseModel):
    """Schema for notification in API responses."""
    id: str
    user_id: str
    type: NotificationType
    title: str
    message: str
    data: Dict[str, Any] = Field(default_factory=dict)
    link: Optional[str] = None
    priority: str
    is_read: bool
    read_at: Optional[datetime] = None
    created_at: datetime

    model_config = {"from_attributes": True}


class NotificationListResponse(BaseModel):
    """Response for list of notifications."""
    notifications: List[NotificationResponse]
    total: int
    unread_count: int
    page: int
    page_size: int


class NotificationCountResponse(BaseModel):
    """Response for notification counts."""
    total: int
    unread: int
    by_type: Dict[str, int] = Field(default_factory=dict)


# ==================== Notification Preference Schemas ====================

class NotificationPreferenceUpdate(BaseModel):
    """Schema for updating notification preferences."""
    channel: Optional[NotificationChannel] = None
    enabled: Optional[bool] = None
    quiet_hours_start: Optional[str] = Field(None, description="Quiet hours start (HH:MM)")
    quiet_hours_end: Optional[str] = Field(None, description="Quiet hours end (HH:MM)")
    digest_frequency: Optional[str] = Field(None, description="Digest frequency: none, daily, weekly")

    # Per-type settings
    task_assigned: Optional[bool] = None
    task_mentioned: Optional[bool] = None
    task_completed: Optional[bool] = None
    checkin_reminder: Optional[bool] = None
    checkin_escalation: Optional[bool] = None
    team_updates: Optional[bool] = None


class NotificationPreferenceResponse(BaseModel):
    """Schema for notification preferences in API responses."""
    id: str
    user_id: str
    channel: NotificationChannel
    enabled: bool
    quiet_hours_start: Optional[str] = None
    quiet_hours_end: Optional[str] = None
    digest_frequency: str = "none"

    # Per-type settings
    task_assigned: bool = True
    task_mentioned: bool = True
    task_completed: bool = True
    checkin_reminder: bool = True
    checkin_escalation: bool = True
    team_updates: bool = True

    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class NotificationPreferenceListResponse(BaseModel):
    """Response for list of notification preferences."""
    preferences: List[NotificationPreferenceResponse]


# ==================== Integration Schemas ====================

class IntegrationCreate(BaseModel):
    """Schema for creating an integration."""
    type: IntegrationType = Field(..., description="Integration type")
    name: str = Field(..., min_length=1, max_length=100, description="Integration name")
    config: Dict[str, Any] = Field(default_factory=dict, description="Integration configuration")


class IntegrationUpdate(BaseModel):
    """Schema for updating an integration."""
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    config: Optional[Dict[str, Any]] = None
    is_enabled: Optional[bool] = None


class IntegrationResponse(BaseModel):
    """Schema for integration in API responses."""
    id: str
    org_id: str
    type: IntegrationType
    name: str
    status: str
    is_enabled: bool
    last_sync_at: Optional[datetime] = None
    sync_error: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class IntegrationListResponse(BaseModel):
    """Response for list of integrations."""
    integrations: List[IntegrationResponse]
    total: int


class IntegrationSyncRequest(BaseModel):
    """Request for triggering integration sync."""
    full_sync: bool = Field(default=False, description="Perform full sync instead of incremental")


class IntegrationSyncResponse(BaseModel):
    """Response for integration sync."""
    success: bool
    items_synced: int = 0
    errors: List[str] = Field(default_factory=list)
    sync_started_at: datetime
    sync_completed_at: Optional[datetime] = None


# ==================== Webhook Schemas ====================

class WebhookCreate(BaseModel):
    """Schema for creating a webhook."""
    name: str = Field(..., min_length=1, max_length=100, description="Webhook name")
    url: str = Field(..., description="Webhook URL")
    events: List[str] = Field(..., min_length=1, description="Events to subscribe to")
    headers: Dict[str, str] = Field(default_factory=dict, description="Custom headers")
    secret: Optional[str] = Field(None, description="Webhook secret for signature")
    is_enabled: bool = Field(default=True)


class WebhookUpdate(BaseModel):
    """Schema for updating a webhook."""
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    url: Optional[str] = None
    events: Optional[List[str]] = None
    headers: Optional[Dict[str, str]] = None
    secret: Optional[str] = None
    is_enabled: Optional[bool] = None


class WebhookResponse(BaseModel):
    """Schema for webhook in API responses."""
    id: str
    org_id: str
    name: str
    url: str
    events: List[str]
    is_enabled: bool
    last_triggered_at: Optional[datetime] = None
    failure_count: int = 0
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class WebhookListResponse(BaseModel):
    """Response for list of webhooks."""
    webhooks: List[WebhookResponse]
    total: int


class WebhookTestRequest(BaseModel):
    """Request for testing a webhook."""
    event_type: str = Field(default="test", description="Event type for test payload")


class WebhookTestResponse(BaseModel):
    """Response for webhook test."""
    success: bool
    status_code: Optional[int] = None
    response_time_ms: Optional[int] = None
    error: Optional[str] = None


# ==================== Webhook Delivery Schemas ====================

class WebhookDeliveryResponse(BaseModel):
    """Schema for webhook delivery in API responses."""
    id: str
    webhook_id: str
    event_type: str
    status_code: Optional[int] = None
    success: bool
    response_time_ms: Optional[int] = None
    error_message: Optional[str] = None
    retry_count: int = 0
    created_at: datetime

    model_config = {"from_attributes": True}


class WebhookDeliveryListResponse(BaseModel):
    """Response for list of webhook deliveries."""
    deliveries: List[WebhookDeliveryResponse]
    total: int
    page: int
    page_size: int

"""
TaskPulse - AI Assistant - Notifications API
Notification management endpoints
"""

from typing import Optional, List
from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import datetime

from app.database import get_db
from app.models.user import User
from app.models.notification import NotificationType, NotificationChannel
from app.services.notification_service import NotificationService
from app.api.v1.dependencies import get_current_active_user, get_pagination, PaginationParams
from app.core.exceptions import NotFoundException
from pydantic import BaseModel, Field

router = APIRouter()


# Schemas
class NotificationResponse(BaseModel):
    id: str
    notification_type: NotificationType
    title: str
    message: str
    is_read: bool
    read_at: Optional[datetime]
    action_url: Optional[str]
    created_at: datetime

    class Config:
        from_attributes = True


class NotificationListResponse(BaseModel):
    notifications: List[NotificationResponse]
    total: int
    unread_count: int
    page: int
    page_size: int


class NotificationPreferencesResponse(BaseModel):
    id: str
    channels: List[NotificationChannel]
    email_enabled: bool
    push_enabled: bool
    quiet_hours_start: Optional[str]
    quiet_hours_end: Optional[str]
    notification_types: dict

    class Config:
        from_attributes = True


class NotificationPreferencesUpdate(BaseModel):
    channels: Optional[List[NotificationChannel]] = None
    email_enabled: Optional[bool] = None
    push_enabled: Optional[bool] = None
    quiet_hours_start: Optional[str] = Field(None, pattern=r"^\d{2}:\d{2}$")
    quiet_hours_end: Optional[str] = Field(None, pattern=r"^\d{2}:\d{2}$")
    notification_types: Optional[dict] = None


def get_notification_service(db: AsyncSession = Depends(get_db)) -> NotificationService:
    return NotificationService(db)


# Endpoints
@router.get(
    "",
    response_model=NotificationListResponse,
    summary="Get notifications"
)
async def get_notifications(
    pagination: PaginationParams = Depends(get_pagination),
    unread_only: bool = Query(False),
    notification_type: Optional[NotificationType] = Query(None),
    current_user: User = Depends(get_current_active_user),
    service: NotificationService = Depends(get_notification_service)
):
    """Get notifications for the current user."""
    notifications, total = await service.get_notifications(
        user_id=current_user.id,
        org_id=current_user.org_id,
        unread_only=unread_only,
        notification_type=notification_type,
        limit=pagination.limit,
        offset=pagination.skip
    )

    unread_count = await service.get_unread_count(current_user.id, current_user.org_id)

    return NotificationListResponse(
        notifications=[
            NotificationResponse(
                id=n.id,
                notification_type=n.notification_type,
                title=n.title,
                message=n.message,
                is_read=n.is_read,
                read_at=n.read_at,
                action_url=n.action_url,
                created_at=n.created_at
            ) for n in notifications
        ],
        total=total,
        unread_count=unread_count,
        page=pagination.page,
        page_size=pagination.page_size
    )


@router.get(
    "/unread-count",
    summary="Get unread notification count"
)
async def get_unread_count(
    current_user: User = Depends(get_current_active_user),
    service: NotificationService = Depends(get_notification_service)
):
    """Get count of unread notifications."""
    count = await service.get_unread_count(current_user.id, current_user.org_id)
    return {"unread_count": count}


@router.patch(
    "/{notification_id}/read",
    response_model=NotificationResponse,
    summary="Mark notification as read"
)
async def mark_notification_read(
    notification_id: str,
    current_user: User = Depends(get_current_active_user),
    service: NotificationService = Depends(get_notification_service)
):
    """Mark a notification as read."""
    notification = await service.mark_as_read(notification_id, current_user.id)

    if not notification:
        raise NotFoundException("Notification", notification_id)

    return NotificationResponse(
        id=notification.id,
        notification_type=notification.notification_type,
        title=notification.title,
        message=notification.message,
        is_read=notification.is_read,
        read_at=notification.read_at,
        action_url=notification.action_url,
        created_at=notification.created_at
    )


@router.post(
    "/read-all",
    summary="Mark all notifications as read"
)
async def mark_all_read(
    current_user: User = Depends(get_current_active_user),
    service: NotificationService = Depends(get_notification_service)
):
    """Mark all notifications as read."""
    count = await service.mark_all_as_read(current_user.id, current_user.org_id)
    return {"marked_read": count}


@router.delete(
    "/{notification_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete notification"
)
async def delete_notification(
    notification_id: str,
    current_user: User = Depends(get_current_active_user),
    service: NotificationService = Depends(get_notification_service)
):
    """Delete a notification."""
    success = await service.delete_notification(notification_id, current_user.id)

    if not success:
        raise NotFoundException("Notification", notification_id)


@router.get(
    "/preferences",
    response_model=NotificationPreferencesResponse,
    summary="Get notification preferences"
)
async def get_preferences(
    current_user: User = Depends(get_current_active_user),
    service: NotificationService = Depends(get_notification_service)
):
    """Get notification preferences for the current user."""
    prefs = await service.get_user_preferences(current_user.id)

    if not prefs:
        # Return defaults
        return NotificationPreferencesResponse(
            id="default",
            channels=[NotificationChannel.IN_APP],
            email_enabled=True,
            push_enabled=False,
            quiet_hours_start=None,
            quiet_hours_end=None,
            notification_types={}
        )

    return NotificationPreferencesResponse(
        id=prefs.id,
        channels=prefs.channels or [NotificationChannel.IN_APP],
        email_enabled=prefs.email_enabled,
        push_enabled=prefs.push_enabled,
        quiet_hours_start=prefs.quiet_hours_start,
        quiet_hours_end=prefs.quiet_hours_end,
        notification_types=prefs.notification_types or {}
    )


@router.patch(
    "/preferences",
    response_model=NotificationPreferencesResponse,
    summary="Update notification preferences"
)
async def update_preferences(
    updates: NotificationPreferencesUpdate,
    current_user: User = Depends(get_current_active_user),
    service: NotificationService = Depends(get_notification_service)
):
    """Update notification preferences."""
    prefs = await service.update_preferences(
        user_id=current_user.id,
        org_id=current_user.org_id,
        channels=updates.channels,
        email_enabled=updates.email_enabled,
        push_enabled=updates.push_enabled,
        quiet_hours_start=updates.quiet_hours_start,
        quiet_hours_end=updates.quiet_hours_end,
        notification_types=updates.notification_types
    )

    return NotificationPreferencesResponse(
        id=prefs.id,
        channels=prefs.channels or [NotificationChannel.IN_APP],
        email_enabled=prefs.email_enabled,
        push_enabled=prefs.push_enabled,
        quiet_hours_start=prefs.quiet_hours_start,
        quiet_hours_end=prefs.quiet_hours_end,
        notification_types=prefs.notification_types or {}
    )

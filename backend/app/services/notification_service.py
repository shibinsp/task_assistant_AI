"""
TaskPulse - AI Assistant - Notification Service
Handles in-app, email, and push notifications
"""

from typing import Optional, List, Dict, Any
from datetime import datetime, timedelta
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, update, and_

from app.models.notification import (
    Notification, NotificationPreference, NotificationType,
    NotificationPriority, NotificationChannel
)
from app.models.user import User
from app.utils.helpers import generate_uuid


class NotificationService:
    """Service for managing notifications."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def create_notification(
        self,
        user_id: str,
        org_id: str,
        notification_type: NotificationType,
        title: str,
        message: str,
        priority: NotificationPriority = NotificationPriority.MEDIUM,
        action_url: Optional[str] = None,
        action_label: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
        related_entity_type: Optional[str] = None,
        related_entity_id: Optional[str] = None
    ) -> Notification:
        """Create a new notification."""
        notification = Notification(
            id=generate_uuid(),
            org_id=org_id,
            user_id=user_id,
            notification_type=notification_type,
            priority=priority,
            title=title,
            message=message,
            action_url=action_url,
            action_label=action_label,
            related_entity_type=related_entity_type,
            related_entity_id=related_entity_id
        )
        if metadata:
            notification.metadata = metadata

        self.db.add(notification)
        await self.db.flush()
        await self.db.refresh(notification)

        # Check user preferences and send via appropriate channels
        await self._send_via_channels(notification)

        return notification

    async def _send_via_channels(self, notification: Notification) -> None:
        """Send notification via configured channels based on user preferences."""
        prefs = await self.get_user_preferences(notification.user_id)

        if not prefs:
            # Default: in-app only
            return

        # Check if this notification type is enabled
        type_prefs = prefs.notification_types or {}
        if notification.notification_type.value in type_prefs:
            if not type_prefs[notification.notification_type.value].get("enabled", True):
                return

        channels = prefs.channels or [NotificationChannel.IN_APP]

        for channel in channels:
            if channel == NotificationChannel.EMAIL:
                await self._send_email(notification)
            elif channel == NotificationChannel.PUSH:
                await self._send_push(notification)
            # IN_APP is handled by the notification being in the database

    async def _send_email(self, notification: Notification) -> None:
        """Send email notification (stub for SMTP integration)."""
        # TODO: Implement actual email sending with SMTP
        # For now, just log it
        print(f"[EMAIL] To: {notification.user_id}, Subject: {notification.title}")

    async def _send_push(self, notification: Notification) -> None:
        """Send push notification (stub for push service integration)."""
        # TODO: Implement actual push notification
        print(f"[PUSH] To: {notification.user_id}, Message: {notification.title}")

    async def get_notifications(
        self,
        user_id: str,
        org_id: str,
        unread_only: bool = False,
        notification_type: Optional[NotificationType] = None,
        limit: int = 50,
        offset: int = 0
    ) -> tuple[List[Notification], int]:
        """Get notifications for a user."""
        query = select(Notification).where(
            Notification.user_id == user_id,
            Notification.org_id == org_id
        )

        if unread_only:
            query = query.where(Notification.is_read == False)

        if notification_type:
            query = query.where(Notification.notification_type == notification_type)

        # Get total count
        count_query = select(func.count()).select_from(query.subquery())
        total = (await self.db.execute(count_query)).scalar() or 0

        # Get notifications
        result = await self.db.execute(
            query.order_by(Notification.created_at.desc())
            .offset(offset).limit(limit)
        )
        notifications = list(result.scalars().all())

        return notifications, total

    async def mark_as_read(
        self,
        notification_id: str,
        user_id: str
    ) -> Optional[Notification]:
        """Mark a notification as read."""
        result = await self.db.execute(
            select(Notification).where(
                Notification.id == notification_id,
                Notification.user_id == user_id
            )
        )
        notification = result.scalar_one_or_none()

        if notification:
            notification.is_read = True
            notification.read_at = datetime.utcnow()
            await self.db.flush()

        return notification

    async def mark_all_as_read(self, user_id: str, org_id: str) -> int:
        """Mark all notifications as read for a user."""
        result = await self.db.execute(
            update(Notification)
            .where(
                Notification.user_id == user_id,
                Notification.org_id == org_id,
                Notification.is_read == False
            )
            .values(is_read=True, read_at=datetime.utcnow())
        )
        await self.db.flush()
        return result.rowcount

    async def delete_notification(
        self,
        notification_id: str,
        user_id: str
    ) -> bool:
        """Delete a notification."""
        result = await self.db.execute(
            select(Notification).where(
                Notification.id == notification_id,
                Notification.user_id == user_id
            )
        )
        notification = result.scalar_one_or_none()

        if notification:
            await self.db.delete(notification)
            await self.db.flush()
            return True

        return False

    async def get_unread_count(self, user_id: str, org_id: str) -> int:
        """Get count of unread notifications."""
        result = await self.db.execute(
            select(func.count()).where(
                Notification.user_id == user_id,
                Notification.org_id == org_id,
                Notification.is_read == False
            )
        )
        return result.scalar() or 0

    async def get_user_preferences(
        self,
        user_id: str
    ) -> Optional[NotificationPreference]:
        """Get notification preferences for a user."""
        result = await self.db.execute(
            select(NotificationPreference).where(
                NotificationPreference.user_id == user_id
            )
        )
        return result.scalar_one_or_none()

    async def update_preferences(
        self,
        user_id: str,
        org_id: str,
        channels: Optional[List[NotificationChannel]] = None,
        email_enabled: Optional[bool] = None,
        push_enabled: Optional[bool] = None,
        quiet_hours_start: Optional[str] = None,
        quiet_hours_end: Optional[str] = None,
        notification_types: Optional[Dict[str, Any]] = None
    ) -> NotificationPreference:
        """Update notification preferences."""
        result = await self.db.execute(
            select(NotificationPreference).where(
                NotificationPreference.user_id == user_id
            )
        )
        prefs = result.scalar_one_or_none()

        if not prefs:
            prefs = NotificationPreference(
                id=generate_uuid(),
                org_id=org_id,
                user_id=user_id
            )
            self.db.add(prefs)

        if channels is not None:
            prefs.channels = channels
        if email_enabled is not None:
            prefs.email_enabled = email_enabled
        if push_enabled is not None:
            prefs.push_enabled = push_enabled
        if quiet_hours_start is not None:
            prefs.quiet_hours_start = quiet_hours_start
        if quiet_hours_end is not None:
            prefs.quiet_hours_end = quiet_hours_end
        if notification_types is not None:
            prefs.notification_types = notification_types

        await self.db.flush()
        await self.db.refresh(prefs)

        return prefs

    # Convenience methods for common notifications
    async def notify_task_assigned(
        self,
        user_id: str,
        org_id: str,
        task_id: str,
        task_title: str,
        assigned_by: str
    ) -> Notification:
        """Send notification when a task is assigned."""
        return await self.create_notification(
            user_id=user_id,
            org_id=org_id,
            notification_type=NotificationType.TASK_ASSIGNED,
            title="New Task Assigned",
            message=f"You have been assigned to: {task_title}",
            priority=NotificationPriority.HIGH,
            action_url=f"/tasks/{task_id}",
            action_label="View Task",
            related_entity_type="task",
            related_entity_id=task_id,
            metadata={"assigned_by": assigned_by}
        )

    async def notify_checkin_due(
        self,
        user_id: str,
        org_id: str,
        task_id: str,
        task_title: str
    ) -> Notification:
        """Send notification for check-in reminder."""
        return await self.create_notification(
            user_id=user_id,
            org_id=org_id,
            notification_type=NotificationType.CHECKIN_DUE,
            title="Check-in Reminder",
            message=f"How's progress on: {task_title}?",
            priority=NotificationPriority.MEDIUM,
            action_url=f"/tasks/{task_id}/checkin",
            action_label="Check In",
            related_entity_type="task",
            related_entity_id=task_id
        )

    async def notify_task_blocked(
        self,
        manager_id: str,
        org_id: str,
        task_id: str,
        task_title: str,
        blocked_by: str,
        blocker_type: str
    ) -> Notification:
        """Send notification when a task is blocked."""
        return await self.create_notification(
            user_id=manager_id,
            org_id=org_id,
            notification_type=NotificationType.TASK_BLOCKED,
            title="Task Blocked",
            message=f"{blocked_by} is blocked on: {task_title}",
            priority=NotificationPriority.HIGH,
            action_url=f"/tasks/{task_id}",
            action_label="View Details",
            related_entity_type="task",
            related_entity_id=task_id,
            metadata={"blocker_type": blocker_type}
        )

    async def notify_deadline_approaching(
        self,
        user_id: str,
        org_id: str,
        task_id: str,
        task_title: str,
        deadline: datetime,
        hours_remaining: int
    ) -> Notification:
        """Send notification when deadline is approaching."""
        return await self.create_notification(
            user_id=user_id,
            org_id=org_id,
            notification_type=NotificationType.DEADLINE_APPROACHING,
            title="Deadline Approaching",
            message=f"{task_title} is due in {hours_remaining} hours",
            priority=NotificationPriority.HIGH if hours_remaining < 24 else NotificationPriority.MEDIUM,
            action_url=f"/tasks/{task_id}",
            action_label="View Task",
            related_entity_type="task",
            related_entity_id=task_id,
            metadata={"deadline": deadline.isoformat(), "hours_remaining": hours_remaining}
        )

    async def notify_ai_suggestion(
        self,
        user_id: str,
        org_id: str,
        task_id: str,
        suggestion_preview: str
    ) -> Notification:
        """Send notification for AI suggestion."""
        return await self.create_notification(
            user_id=user_id,
            org_id=org_id,
            notification_type=NotificationType.AI_SUGGESTION,
            title="AI Suggestion Available",
            message=suggestion_preview[:100] + "..." if len(suggestion_preview) > 100 else suggestion_preview,
            priority=NotificationPriority.LOW,
            action_url=f"/tasks/{task_id}/ai-help",
            action_label="View Suggestion",
            related_entity_type="task",
            related_entity_id=task_id
        )

    async def cleanup_old_notifications(
        self,
        org_id: str,
        days_to_keep: int = 30
    ) -> int:
        """Clean up old read notifications."""
        cutoff = datetime.utcnow() - timedelta(days=days_to_keep)

        result = await self.db.execute(
            select(Notification).where(
                Notification.org_id == org_id,
                Notification.is_read == True,
                Notification.created_at < cutoff
            )
        )
        old_notifications = result.scalars().all()

        count = len(old_notifications)
        for notification in old_notifications:
            await self.db.delete(notification)

        await self.db.flush()
        return count

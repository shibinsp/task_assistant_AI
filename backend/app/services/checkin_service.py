"""
TaskPulse - AI Assistant - Check-In Service
Business logic for the Smart Check-In Engine
"""

from typing import Optional, List, Tuple
from datetime import datetime, timedelta
from sqlalchemy import select, func, and_, or_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.checkin import (
    CheckIn, CheckInConfig, CheckInReminder,
    CheckInTrigger, CheckInStatus, ProgressIndicator
)
from app.models.task import Task, TaskStatus
from app.models.user import User
from app.schemas.checkin import (
    CheckInSubmit, CheckInSkip, CheckInCreate,
    CheckInConfigCreate, CheckInConfigUpdate, EscalationRequest
)
from app.utils.helpers import generate_uuid
from app.core.exceptions import NotFoundException, ValidationException, ForbiddenException
from app.services.ai_service import get_ai_service
from app.services.notification_service import NotificationService
from app.models.notification import NotificationType, NotificationPriority
from app.config import settings


class CheckInService:
    """Service class for check-in operations."""

    def __init__(self, db: AsyncSession):
        self.db = db

    # ==================== Check-In CRUD ====================

    async def create_checkin(
        self,
        org_id: str,
        task_id: str,
        user_id: str,
        trigger: CheckInTrigger = CheckInTrigger.SCHEDULED,
        scheduled_at: Optional[datetime] = None,
        expires_hours: float = 2.0
    ) -> CheckIn:
        """Create a new check-in."""
        # Verify task exists and is active
        task = await self.db.execute(
            select(Task).where(
                and_(Task.id == task_id, Task.org_id == org_id)
            )
        )
        task = task.scalar_one_or_none()
        if not task:
            raise NotFoundException("Task", task_id)

        if task.status in (TaskStatus.DONE, TaskStatus.ARCHIVED):
            raise ValidationException("Cannot create check-in for completed task")

        # Get cycle number
        cycle_count = await self.db.execute(
            select(func.count()).select_from(CheckIn).where(
                and_(CheckIn.task_id == task_id, CheckIn.user_id == user_id)
            )
        )
        cycle_number = (cycle_count.scalar() or 0) + 1

        scheduled = scheduled_at or datetime.utcnow()
        expires = scheduled + timedelta(hours=expires_hours)

        checkin = CheckIn(
            id=generate_uuid(),
            org_id=org_id,
            task_id=task_id,
            user_id=user_id,
            cycle_number=cycle_number,
            trigger=trigger,
            status=CheckInStatus.PENDING,
            scheduled_at=scheduled,
            expires_at=expires
        )

        self.db.add(checkin)
        await self.db.flush()
        await self.db.refresh(checkin)

        return checkin

    async def get_checkin_by_id(
        self,
        checkin_id: str,
        org_id: str
    ) -> Optional[CheckIn]:
        """Get a check-in by ID."""
        result = await self.db.execute(
            select(CheckIn).where(
                and_(CheckIn.id == checkin_id, CheckIn.org_id == org_id)
            ).options(selectinload(CheckIn.task))
        )
        return result.scalar_one_or_none()

    async def get_checkins(
        self,
        org_id: str,
        user_id: Optional[str] = None,
        task_id: Optional[str] = None,
        team_id: Optional[str] = None,
        status: Optional[CheckInStatus] = None,
        pending_only: bool = False,
        skip: int = 0,
        limit: int = 50
    ) -> Tuple[List[CheckIn], int]:
        """Get check-ins with filters."""
        query = select(CheckIn).where(CheckIn.org_id == org_id)

        if user_id:
            query = query.where(CheckIn.user_id == user_id)
        if task_id:
            query = query.where(CheckIn.task_id == task_id)
        if status:
            query = query.where(CheckIn.status == status)
        if pending_only:
            query = query.where(CheckIn.status == CheckInStatus.PENDING)

        # Team filter requires join
        if team_id:
            query = query.join(Task).where(Task.team_id == team_id)

        # Count
        count_query = select(func.count()).select_from(query.subquery())
        total = (await self.db.execute(count_query)).scalar() or 0

        # Paginate
        query = query.offset(skip).limit(limit)
        query = query.order_by(CheckIn.scheduled_at.desc())
        query = query.options(selectinload(CheckIn.task))

        result = await self.db.execute(query)
        return list(result.scalars().all()), total

    async def get_pending_checkins_for_user(
        self,
        user_id: str,
        org_id: str
    ) -> List[CheckIn]:
        """Get all pending check-ins for a user."""
        result = await self.db.execute(
            select(CheckIn).where(
                and_(
                    CheckIn.user_id == user_id,
                    CheckIn.org_id == org_id,
                    CheckIn.status == CheckInStatus.PENDING
                )
            ).options(selectinload(CheckIn.task))
            .order_by(CheckIn.scheduled_at)
        )
        return list(result.scalars().all())

    # ==================== Check-In Response ====================

    async def respond_to_checkin(
        self,
        checkin_id: str,
        org_id: str,
        user_id: str,
        response: CheckInSubmit
    ) -> CheckIn:
        """Submit a response to a check-in."""
        checkin = await self.get_checkin_by_id(checkin_id, org_id)
        if not checkin:
            raise NotFoundException("CheckIn", checkin_id)

        if checkin.user_id != user_id:
            raise ForbiddenException("Not authorized to respond to this check-in")

        if checkin.status != CheckInStatus.PENDING:
            raise ValidationException(f"Check-in is already {checkin.status.value}")

        # Update check-in with response
        checkin.status = CheckInStatus.RESPONDED
        checkin.responded_at = datetime.utcnow()
        checkin.progress_indicator = response.progress_indicator
        checkin.progress_notes = response.progress_notes
        checkin.completed_since_last = response.completed_since_last
        checkin.blockers_reported = response.blockers_reported
        checkin.help_needed = response.help_needed
        checkin.estimated_completion_change = response.estimated_completion_change

        # AI analysis
        ai_service = get_ai_service()

        # Sentiment analysis on notes
        if response.progress_notes:
            sentiment = await ai_service.analyze_sentiment(response.progress_notes)
            checkin.sentiment_score = sentiment.get("confidence", 0)
            if sentiment.get("sentiment") in ["frustrated", "negative"]:
                checkin.friction_detected = True

        # If help needed or blocked, get AI suggestion
        if response.help_needed or response.progress_indicator == ProgressIndicator.BLOCKED:
            checkin.friction_detected = True

            task = checkin.task
            if task and response.blockers_reported:
                suggestion = await ai_service.get_unblock_suggestion(
                    task_title=task.title,
                    task_description=task.description or "",
                    blocker_type=task.blocker_type.value if task.blocker_type else "unknown",
                    blocker_description=response.blockers_reported
                )
                checkin.ai_suggestion = suggestion.get("suggestion")
                checkin.ai_confidence = suggestion.get("confidence")

        await self.db.flush()
        await self.db.refresh(checkin)

        return checkin

    async def skip_checkin(
        self,
        checkin_id: str,
        org_id: str,
        user_id: str,
        skip_data: CheckInSkip
    ) -> CheckIn:
        """Skip a check-in."""
        checkin = await self.get_checkin_by_id(checkin_id, org_id)
        if not checkin:
            raise NotFoundException("CheckIn", checkin_id)

        if checkin.user_id != user_id:
            raise ForbiddenException("Not authorized to skip this check-in")

        if checkin.status != CheckInStatus.PENDING:
            raise ValidationException(f"Check-in is already {checkin.status.value}")

        checkin.status = CheckInStatus.SKIPPED
        checkin.responded_at = datetime.utcnow()
        checkin.progress_notes = f"Skipped: {skip_data.reason}" if skip_data.reason else "Skipped"

        await self.db.flush()
        await self.db.refresh(checkin)

        return checkin

    # ==================== Escalation ====================

    async def escalate_checkin(
        self,
        checkin_id: str,
        org_id: str,
        escalation: EscalationRequest,
        escalated_by: str
    ) -> CheckIn:
        """Escalate a check-in to a manager."""
        checkin = await self.get_checkin_by_id(checkin_id, org_id)
        if not checkin:
            raise NotFoundException("CheckIn", checkin_id)

        if checkin.escalated:
            raise ValidationException("Check-in is already escalated")

        checkin.escalated = True
        checkin.escalated_to = escalation.escalate_to
        checkin.escalated_at = datetime.utcnow()
        checkin.escalation_reason = escalation.reason
        checkin.status = CheckInStatus.ESCALATED

        await self.db.flush()
        await self.db.refresh(checkin)

        # Send notification to escalated_to user
        notification_service = NotificationService(self.db)
        await notification_service.create_notification(
            user_id=escalation.escalate_to,
            org_id=org_id,
            notification_type=NotificationType.CHECKIN_ESCALATED,
            title="Check-in Escalated to You",
            message=f"A check-in has been escalated to you. Reason: {escalation.reason}",
            priority=NotificationPriority.HIGH,
            action_url=f"/checkins/{checkin_id}",
            action_label="View Check-in",
            related_entity_type="checkin",
            related_entity_id=checkin_id
        )

        return checkin

    async def auto_escalate_expired(
        self,
        org_id: str
    ) -> int:
        """Auto-escalate expired check-ins based on config."""
        # Get expired check-ins
        expired = await self.db.execute(
            select(CheckIn).where(
                and_(
                    CheckIn.org_id == org_id,
                    CheckIn.status == CheckInStatus.PENDING,
                    CheckIn.expires_at < datetime.utcnow(),
                    CheckIn.escalated == False
                )
            ).options(selectinload(CheckIn.task), selectinload(CheckIn.user))
        )
        expired_checkins = expired.scalars().all()

        escalated_count = 0
        for checkin in expired_checkins:
            # Mark as expired
            checkin.status = CheckInStatus.EXPIRED

            # Check if should auto-escalate
            config = await self.get_config_for_task(checkin.task_id, org_id)
            missed_count = await self._count_missed_checkins(
                checkin.user_id, checkin.task_id
            )

            if missed_count >= config.auto_escalate_after_missed:
                # Get manager to escalate to
                if checkin.user and checkin.user.manager_id:
                    checkin.escalated = True
                    checkin.escalated_to = checkin.user.manager_id
                    checkin.escalated_at = datetime.utcnow()
                    checkin.escalation_reason = f"Auto-escalated after {missed_count} missed check-ins"
                    checkin.status = CheckInStatus.ESCALATED
                    escalated_count += 1

        await self.db.flush()
        return escalated_count

    async def _count_missed_checkins(
        self,
        user_id: str,
        task_id: str
    ) -> int:
        """Count consecutive missed check-ins."""
        result = await self.db.execute(
            select(CheckIn).where(
                and_(
                    CheckIn.user_id == user_id,
                    CheckIn.task_id == task_id
                )
            ).order_by(CheckIn.scheduled_at.desc())
            .limit(10)
        )
        recent = result.scalars().all()

        missed = 0
        for checkin in recent:
            if checkin.status in (CheckInStatus.EXPIRED, CheckInStatus.PENDING):
                missed += 1
            elif checkin.status == CheckInStatus.RESPONDED:
                break

        return missed

    # ==================== Configuration ====================

    async def get_config(
        self,
        config_id: str,
        org_id: str
    ) -> Optional[CheckInConfig]:
        """Get a check-in config by ID."""
        result = await self.db.execute(
            select(CheckInConfig).where(
                and_(CheckInConfig.id == config_id, CheckInConfig.org_id == org_id)
            )
        )
        return result.scalar_one_or_none()

    async def get_config_for_task(
        self,
        task_id: str,
        org_id: str
    ) -> CheckInConfig:
        """Get effective config for a task (cascade: task -> user -> team -> org)."""
        # Try task-specific config
        result = await self.db.execute(
            select(CheckInConfig).where(
                and_(CheckInConfig.task_id == task_id, CheckInConfig.org_id == org_id)
            )
        )
        config = result.scalar_one_or_none()
        if config:
            return config

        # Get task for user and team info
        task_result = await self.db.execute(
            select(Task).where(Task.id == task_id)
        )
        task = task_result.scalar_one_or_none()

        if task:
            # Try user-specific config
            if task.assigned_to:
                result = await self.db.execute(
                    select(CheckInConfig).where(
                        and_(
                            CheckInConfig.user_id == task.assigned_to,
                            CheckInConfig.org_id == org_id
                        )
                    )
                )
                config = result.scalar_one_or_none()
                if config:
                    return config

            # Try team-specific config
            if task.team_id:
                result = await self.db.execute(
                    select(CheckInConfig).where(
                        and_(
                            CheckInConfig.team_id == task.team_id,
                            CheckInConfig.org_id == org_id
                        )
                    )
                )
                config = result.scalar_one_or_none()
                if config:
                    return config

        # Return org default or create default
        result = await self.db.execute(
            select(CheckInConfig).where(
                and_(
                    CheckInConfig.org_id == org_id,
                    CheckInConfig.team_id == None,
                    CheckInConfig.user_id == None,
                    CheckInConfig.task_id == None
                )
            )
        )
        config = result.scalar_one_or_none()

        if not config:
            # Create default org config
            config = CheckInConfig(
                id=generate_uuid(),
                org_id=org_id,
                interval_hours=settings.DEFAULT_CHECKIN_INTERVAL_HOURS
            )
            self.db.add(config)
            await self.db.flush()
            await self.db.refresh(config)

        return config

    async def create_config(
        self,
        org_id: str,
        config_data: CheckInConfigCreate
    ) -> CheckInConfig:
        """Create a check-in configuration."""
        config = CheckInConfig(
            id=generate_uuid(),
            org_id=org_id,
            **config_data.model_dump()
        )
        self.db.add(config)
        await self.db.flush()
        await self.db.refresh(config)
        return config

    async def update_config(
        self,
        config_id: str,
        org_id: str,
        config_data: CheckInConfigUpdate
    ) -> CheckInConfig:
        """Update a check-in configuration."""
        config = await self.get_config(config_id, org_id)
        if not config:
            raise NotFoundException("CheckInConfig", config_id)

        update_dict = config_data.model_dump(exclude_unset=True)
        for field, value in update_dict.items():
            setattr(config, field, value)

        await self.db.flush()
        await self.db.refresh(config)
        return config

    async def delete_config(
        self,
        config_id: str,
        org_id: str
    ) -> bool:
        """Delete a check-in configuration."""
        config = await self.get_config(config_id, org_id)
        if not config:
            raise NotFoundException("CheckInConfig", config_id)

        await self.db.delete(config)
        await self.db.flush()
        return True

    # ==================== Statistics ====================

    async def get_statistics(
        self,
        org_id: str,
        team_id: Optional[str] = None,
        user_id: Optional[str] = None,
        days: int = 30
    ) -> dict:
        """Get check-in statistics."""
        since = datetime.utcnow() - timedelta(days=days)
        base_query = select(CheckIn).where(
            and_(CheckIn.org_id == org_id, CheckIn.scheduled_at >= since)
        )

        if team_id:
            base_query = base_query.join(Task).where(Task.team_id == team_id)
        if user_id:
            base_query = base_query.where(CheckIn.user_id == user_id)

        # Get totals by status
        status_counts = {}
        for status in CheckInStatus:
            count = await self.db.execute(
                select(func.count()).select_from(
                    base_query.where(CheckIn.status == status).subquery()
                )
            )
            status_counts[status.value] = count.scalar() or 0

        total = sum(status_counts.values())
        responded = status_counts.get(CheckInStatus.RESPONDED.value, 0)

        # Average response time
        avg_result = await self.db.execute(
            select(func.avg(
                func.julianday(CheckIn.responded_at) - func.julianday(CheckIn.scheduled_at)
            )).select_from(
                base_query.where(CheckIn.responded_at != None).subquery()
            )
        )
        avg_days = avg_result.scalar()
        avg_minutes = avg_days * 24 * 60 if avg_days else None

        # Friction rate
        friction_count = await self.db.execute(
            select(func.count()).select_from(
                base_query.where(CheckIn.friction_detected == True).subquery()
            )
        )
        friction = friction_count.scalar() or 0

        # Help requested rate
        help_count = await self.db.execute(
            select(func.count()).select_from(
                base_query.where(CheckIn.help_needed == True).subquery()
            )
        )
        help_needed = help_count.scalar() or 0

        return {
            "total_checkins": total,
            "pending": status_counts.get(CheckInStatus.PENDING.value, 0),
            "responded": responded,
            "skipped": status_counts.get(CheckInStatus.SKIPPED.value, 0),
            "expired": status_counts.get(CheckInStatus.EXPIRED.value, 0),
            "escalated": status_counts.get(CheckInStatus.ESCALATED.value, 0),
            "response_rate": round(responded / total * 100, 1) if total > 0 else 0,
            "average_response_time_minutes": round(avg_minutes, 1) if avg_minutes else None,
            "friction_rate": round(friction / total * 100, 1) if total > 0 else 0,
            "help_requested_rate": round(help_needed / total * 100, 1) if total > 0 else 0
        }

    # ==================== Feed for Managers ====================

    async def get_manager_feed(
        self,
        org_id: str,
        manager_id: str,
        include_team: bool = True,
        needs_attention_only: bool = False,
        skip: int = 0,
        limit: int = 50
    ) -> Tuple[List[CheckIn], int, int]:
        """Get check-in feed for managers."""
        # Get direct reports
        reports_result = await self.db.execute(
            select(User.id).where(User.manager_id == manager_id)
        )
        report_ids = [r[0] for r in reports_result.all()]

        if not report_ids:
            return [], 0, 0

        query = select(CheckIn).where(
            and_(
                CheckIn.org_id == org_id,
                CheckIn.user_id.in_(report_ids)
            )
        )

        if needs_attention_only:
            query = query.where(
                or_(
                    CheckIn.help_needed == True,
                    CheckIn.friction_detected == True,
                    CheckIn.escalated == True,
                    CheckIn.status == CheckInStatus.EXPIRED
                )
            )

        # Count needs attention
        attention_query = select(func.count()).select_from(
            select(CheckIn).where(
                and_(
                    CheckIn.org_id == org_id,
                    CheckIn.user_id.in_(report_ids),
                    or_(
                        CheckIn.help_needed == True,
                        CheckIn.friction_detected == True,
                        CheckIn.escalated == True
                    )
                )
            ).subquery()
        )
        needs_attention = (await self.db.execute(attention_query)).scalar() or 0

        # Count total
        count_query = select(func.count()).select_from(query.subquery())
        total = (await self.db.execute(count_query)).scalar() or 0

        # Get results
        query = query.offset(skip).limit(limit)
        query = query.order_by(CheckIn.scheduled_at.desc())
        query = query.options(selectinload(CheckIn.task), selectinload(CheckIn.user))

        result = await self.db.execute(query)
        return list(result.scalars().all()), total, needs_attention

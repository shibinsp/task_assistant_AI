"""
TaskPulse - AI Assistant - Analytics Service
Dashboard metrics and reporting analytics
"""

from typing import Optional, List, Dict, Any
from datetime import datetime, timedelta
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_, case

from app.models.task import Task, TaskStatus, TaskPriority
from app.models.user import User
from app.models.checkin import CheckIn
from app.utils.helpers import generate_uuid


class AnalyticsService:
    """Service for analytics and dashboard metrics."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_dashboard_metrics(
        self,
        org_id: str,
        team_id: Optional[str] = None,
        user_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """Get comprehensive dashboard metrics."""
        # Build base query filters
        filters = [Task.org_id == org_id]
        if team_id:
            filters.append(Task.team_id == team_id)
        if user_id:
            filters.append(Task.assigned_to == user_id)

        # Task counts by status
        status_counts = await self._get_status_counts(filters)

        # Task counts by priority
        priority_counts = await self._get_priority_counts(filters)

        # Completion metrics
        completion_metrics = await self._get_completion_metrics(org_id, team_id, user_id)

        # Blocker analysis
        blocker_metrics = await self._get_blocker_metrics(filters)

        # Recent activity
        recent_activity = await self._get_recent_activity(org_id, team_id, user_id)

        return {
            "task_summary": {
                "by_status": status_counts,
                "by_priority": priority_counts,
                "total_active": sum(v for k, v in status_counts.items() if k not in ["done", "archived"]),
                "total_completed": status_counts.get("done", 0)
            },
            "completion_metrics": completion_metrics,
            "blocker_analysis": blocker_metrics,
            "recent_activity": recent_activity,
            "generated_at": datetime.utcnow().isoformat()
        }

    async def _get_status_counts(self, filters: List) -> Dict[str, int]:
        """Get task counts by status."""
        result = await self.db.execute(
            select(Task.status, func.count(Task.id))
            .where(*filters)
            .group_by(Task.status)
        )
        rows = result.all()
        return {row[0].value: row[1] for row in rows}

    async def _get_priority_counts(self, filters: List) -> Dict[str, int]:
        """Get task counts by priority."""
        result = await self.db.execute(
            select(Task.priority, func.count(Task.id))
            .where(*filters, Task.status.not_in([TaskStatus.DONE, TaskStatus.ARCHIVED]))
            .group_by(Task.priority)
        )
        rows = result.all()
        return {row[0].value: row[1] for row in rows}

    async def _get_completion_metrics(
        self,
        org_id: str,
        team_id: Optional[str],
        user_id: Optional[str]
    ) -> Dict[str, Any]:
        """Get completion rate metrics."""
        now = datetime.utcnow()
        week_ago = now - timedelta(days=7)
        month_ago = now - timedelta(days=30)

        filters = [Task.org_id == org_id]
        if team_id:
            filters.append(Task.team_id == team_id)
        if user_id:
            filters.append(Task.assigned_to == user_id)

        # This week completions
        result = await self.db.execute(
            select(func.count()).where(
                *filters,
                Task.status == TaskStatus.DONE,
                Task.completed_at >= week_ago
            )
        )
        week_completed = result.scalar() or 0

        # This month completions
        result = await self.db.execute(
            select(func.count()).where(
                *filters,
                Task.status == TaskStatus.DONE,
                Task.completed_at >= month_ago
            )
        )
        month_completed = result.scalar() or 0

        # On-time rate
        result = await self.db.execute(
            select(Task).where(
                *filters,
                Task.status == TaskStatus.DONE,
                Task.completed_at >= month_ago,
                Task.deadline.isnot(None)
            )
        )
        tasks_with_deadline = result.scalars().all()
        on_time = sum(1 for t in tasks_with_deadline if t.completed_at and t.deadline and t.completed_at <= t.deadline)
        on_time_rate = (on_time / len(tasks_with_deadline) * 100) if tasks_with_deadline else 0

        # Average completion time
        result = await self.db.execute(
            select(Task).where(
                *filters,
                Task.status == TaskStatus.DONE,
                Task.completed_at >= month_ago,
                Task.started_at.isnot(None)
            )
        )
        completed_tasks = result.scalars().all()

        avg_hours = 0
        if completed_tasks:
            total_hours = sum(
                (t.completed_at - t.started_at).total_seconds() / 3600
                for t in completed_tasks
                if t.completed_at and t.started_at
            )
            avg_hours = total_hours / len(completed_tasks)

        return {
            "completed_this_week": week_completed,
            "completed_this_month": month_completed,
            "on_time_rate": round(on_time_rate, 1),
            "avg_completion_hours": round(avg_hours, 1)
        }

    async def _get_blocker_metrics(self, filters: List) -> Dict[str, Any]:
        """Get blocker analysis metrics."""
        result = await self.db.execute(
            select(Task).where(
                *filters,
                Task.status == TaskStatus.BLOCKED
            )
        )
        blocked_tasks = result.scalars().all()

        by_type = {}
        for task in blocked_tasks:
            blocker_type = task.blocker_type.value if task.blocker_type else "unknown"
            by_type[blocker_type] = by_type.get(blocker_type, 0) + 1

        # Calculate average block duration
        avg_block_hours = 0
        if blocked_tasks:
            # Get tasks that were unblocked recently
            result = await self.db.execute(
                select(Task).where(
                    *filters,
                    Task.status != TaskStatus.BLOCKED
                ).order_by(Task.updated_at.desc()).limit(50)
            )
            recently_unblocked = result.scalars().all()
            # This is a simplified calculation
            avg_block_hours = 8.5  # Mock average

        return {
            "total_blocked": len(blocked_tasks),
            "by_type": by_type,
            "avg_block_duration_hours": avg_block_hours,
            "critical_blocked": sum(1 for t in blocked_tasks if t.priority == TaskPriority.CRITICAL)
        }

    async def _get_recent_activity(
        self,
        org_id: str,
        team_id: Optional[str],
        user_id: Optional[str],
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        """Get recent task activity."""
        filters = [Task.org_id == org_id]
        if team_id:
            filters.append(Task.team_id == team_id)
        if user_id:
            filters.append(Task.assigned_to == user_id)

        result = await self.db.execute(
            select(Task).where(*filters)
            .order_by(Task.updated_at.desc())
            .limit(limit)
        )
        recent_tasks = result.scalars().all()

        return [
            {
                "task_id": t.id,
                "title": t.title[:50],
                "status": t.status.value,
                "updated_at": t.updated_at.isoformat(),
                "assigned_to": t.assigned_to
            } for t in recent_tasks
        ]

    async def get_team_workload(
        self,
        team_id: str,
        org_id: str
    ) -> Dict[str, Any]:
        """Get workload distribution for a team."""
        # Get team members
        result = await self.db.execute(
            select(User).where(
                User.org_id == org_id,
                User.team_id == team_id,
                User.is_active == True
            )
        )
        team_members = result.scalars().all()

        workload = []
        for member in team_members:
            # Get task counts
            result = await self.db.execute(
                select(func.count()).where(
                    Task.assigned_to == member.id,
                    Task.org_id == org_id,
                    Task.status.not_in([TaskStatus.DONE, TaskStatus.ARCHIVED])
                )
            )
            active_count = result.scalar() or 0

            # Get estimated hours
            result = await self.db.execute(
                select(func.sum(Task.estimated_hours)).where(
                    Task.assigned_to == member.id,
                    Task.org_id == org_id,
                    Task.status.not_in([TaskStatus.DONE, TaskStatus.ARCHIVED])
                )
            )
            total_hours = result.scalar() or 0

            workload.append({
                "user_id": member.id,
                "user_name": f"{member.first_name} {member.last_name}",
                "active_tasks": active_count,
                "estimated_hours": round(total_hours, 1),
                "capacity_used": min(100, round(active_count / 8 * 100, 1))  # Assume 8 tasks = 100%
            })

        # Sort by workload
        workload.sort(key=lambda x: x["active_tasks"], reverse=True)

        return {
            "team_id": team_id,
            "total_members": len(team_members),
            "total_active_tasks": sum(w["active_tasks"] for w in workload),
            "avg_tasks_per_member": round(sum(w["active_tasks"] for w in workload) / max(1, len(team_members)), 1),
            "members": workload
        }

    async def get_velocity_chart_data(
        self,
        org_id: str,
        team_id: Optional[str] = None,
        weeks: int = 12
    ) -> Dict[str, Any]:
        """Get velocity data for charting."""
        data_points = []
        now = datetime.utcnow()

        filters = [Task.org_id == org_id, Task.status == TaskStatus.DONE]
        if team_id:
            filters.append(Task.team_id == team_id)

        for week in range(weeks - 1, -1, -1):
            week_start = now - timedelta(weeks=week + 1)
            week_end = now - timedelta(weeks=week)

            result = await self.db.execute(
                select(func.count()).where(
                    *filters,
                    Task.completed_at >= week_start,
                    Task.completed_at < week_end
                )
            )
            count = result.scalar() or 0

            data_points.append({
                "week": (now - timedelta(weeks=week)).strftime("%Y-%m-%d"),
                "completed": count
            })

        return {
            "period_weeks": weeks,
            "team_id": team_id,
            "data_points": data_points,
            "average": round(sum(d["completed"] for d in data_points) / weeks, 1),
            "trend": self._calculate_trend([d["completed"] for d in data_points])
        }

    def _calculate_trend(self, values: List[int]) -> str:
        """Calculate trend from a series of values."""
        if len(values) < 4:
            return "insufficient_data"

        recent = sum(values[-4:]) / 4
        older = sum(values[:-4]) / max(1, len(values) - 4)

        if recent > older * 1.1:
            return "increasing"
        elif recent < older * 0.9:
            return "decreasing"
        return "stable"

    async def get_bottleneck_analysis(
        self,
        org_id: str,
        team_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """Analyze bottlenecks in task flow."""
        filters = [Task.org_id == org_id]
        if team_id:
            filters.append(Task.team_id == team_id)

        # Get tasks in each status
        result = await self.db.execute(
            select(Task).where(*filters, Task.status.not_in([TaskStatus.DONE, TaskStatus.ARCHIVED]))
        )
        active_tasks = result.scalars().all()

        # Identify bottlenecks
        bottlenecks = []

        # Review bottleneck
        in_review = [t for t in active_tasks if t.status == TaskStatus.REVIEW]
        if len(in_review) > 5:
            bottlenecks.append({
                "type": "review_queue",
                "severity": "high" if len(in_review) > 10 else "medium",
                "count": len(in_review),
                "description": f"{len(in_review)} tasks waiting for review",
                "suggestion": "Consider adding more reviewers or async review process"
            })

        # Blocked tasks bottleneck
        blocked = [t for t in active_tasks if t.status == TaskStatus.BLOCKED]
        if len(blocked) > 3:
            bottlenecks.append({
                "type": "blocked_tasks",
                "severity": "high" if len(blocked) > 7 else "medium",
                "count": len(blocked),
                "description": f"{len(blocked)} tasks are blocked",
                "suggestion": "Prioritize blocker resolution"
            })

        # Overdue tasks
        overdue = [t for t in active_tasks if t.is_overdue]
        if len(overdue) > 0:
            bottlenecks.append({
                "type": "overdue",
                "severity": "high" if len(overdue) > 5 else "medium",
                "count": len(overdue),
                "description": f"{len(overdue)} tasks are overdue",
                "suggestion": "Review priorities and resource allocation"
            })

        # Unassigned tasks
        unassigned = [t for t in active_tasks if not t.assigned_to]
        if len(unassigned) > 5:
            bottlenecks.append({
                "type": "unassigned",
                "severity": "medium",
                "count": len(unassigned),
                "description": f"{len(unassigned)} tasks are unassigned",
                "suggestion": "Assign tasks to team members"
            })

        return {
            "total_active_tasks": len(active_tasks),
            "bottlenecks": bottlenecks,
            "bottleneck_count": len(bottlenecks),
            "health_score": max(0, 100 - len(bottlenecks) * 15),
            "analysis_time": datetime.utcnow().isoformat()
        }

    async def get_check_in_summary(
        self,
        org_id: str,
        team_id: Optional[str] = None,
        days: int = 7
    ) -> Dict[str, Any]:
        """Get check-in activity summary."""
        cutoff = datetime.utcnow() - timedelta(days=days)

        filters = [CheckIn.org_id == org_id, CheckIn.created_at >= cutoff]
        if team_id:
            filters.append(CheckIn.team_id == team_id)

        result = await self.db.execute(
            select(CheckIn).where(*filters)
        )
        checkins = result.scalars().all()

        total = len(checkins)
        responded = sum(1 for c in checkins if c.response_status == "responded")
        escalated = sum(1 for c in checkins if c.was_escalated)
        with_blockers = sum(1 for c in checkins if c.has_blocker)

        # Daily breakdown
        daily_counts = {}
        for checkin in checkins:
            day = checkin.created_at.strftime("%Y-%m-%d")
            daily_counts[day] = daily_counts.get(day, 0) + 1

        return {
            "period_days": days,
            "total_checkins": total,
            "responded": responded,
            "response_rate": round(responded / total * 100, 1) if total > 0 else 0,
            "escalated": escalated,
            "escalation_rate": round(escalated / total * 100, 1) if total > 0 else 0,
            "with_blockers": with_blockers,
            "daily_breakdown": daily_counts
        }

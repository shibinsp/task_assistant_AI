"""
Calendar Integration Agent

Sync with Google Calendar and Outlook for scheduling and reminders.
"""

import logging
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

from ..base import AgentCapability, EventType
from ..context import AgentContext
from .base_integration import (
    BaseIntegrationAgent,
    IntegrationStatus,
    SyncDirection,
    WebhookEvent,
)

logger = logging.getLogger(__name__)


class CalendarAgent(BaseIntegrationAgent):
    """
    Calendar integration agent for scheduling.

    Features:
    - Sync task deadlines to calendar
    - Block focus time for tasks
    - Schedule meetings for blocked tasks
    - Send calendar reminders
    - Check availability for assignments
    """

    integration_type = "calendar"
    name = "calendar_agent"
    description = "Calendar integration for scheduling and time management"
    version = "1.0.0"

    capabilities = [AgentCapability.CALENDAR_SYNC]

    sync_direction = SyncDirection.BIDIRECTIONAL
    sync_interval_minutes = 30

    # Calendar providers
    PROVIDERS = ["google", "outlook", "ical"]

    # Event colors by task priority
    PRIORITY_COLORS = {
        "critical": "11",  # Red
        "high": "5",       # Yellow
        "medium": "1",     # Blue
        "low": "8",        # Gray
    }

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        super().__init__(config)
        self.provider: str = "google"
        self.calendar_id: str = "primary"
        self.create_focus_blocks: bool = True
        self.focus_block_duration: int = 90  # minutes
        self.sync_deadlines: bool = True

        if config:
            self.provider = config.get("provider", "google")
            self.calendar_id = config.get("calendar_id", "primary")
            self.create_focus_blocks = config.get("create_focus_blocks", True)
            self.focus_block_duration = config.get("focus_block_duration", 90)
            self.sync_deadlines = config.get("sync_deadlines", True)

    async def sync_inbound(self, context: AgentContext) -> List[Dict[str, Any]]:
        """Sync calendar events to TaskPulse"""
        synced_items = []

        try:
            events = await self._fetch_calendar_events()

            for event in events:
                # Check if this looks like a task
                if self._is_task_event(event):
                    task_data = self._map_event_to_task(event)
                    synced_items.append({
                        **task_data,
                        "is_new": not self._task_exists(task_data["external_id"]),
                        "source": "calendar",
                    })

            logger.info(f"Synced {len(synced_items)} events from calendar")

        except Exception as e:
            logger.error(f"Calendar inbound sync error: {e}")
            raise

        return synced_items

    async def sync_outbound(self, context: AgentContext) -> Dict[str, Any]:
        """Sync TaskPulse tasks to calendar"""
        result = {"count": 0, "created": 0, "updated": 0, "errors": []}

        try:
            tasks = await self._get_tasks_to_sync(context)

            for task in tasks:
                try:
                    if task.get("calendar_event_id"):
                        await self._update_calendar_event(task)
                        result["updated"] += 1
                    else:
                        await self._create_calendar_event(task)
                        result["created"] += 1

                    result["count"] += 1

                except Exception as e:
                    result["errors"].append(f"Task {task.get('id')}: {str(e)}")

            logger.info(f"Synced {result['count']} tasks to calendar")

        except Exception as e:
            logger.error(f"Calendar outbound sync error: {e}")
            raise

        return result

    async def handle_webhook(self, event: WebhookEvent) -> Dict[str, Any]:
        """Handle calendar webhook events"""
        result = {"processed": False}

        try:
            event_type = event.payload.get("type")

            if event_type == "event.created":
                result = await self._handle_event_created(event.payload)

            elif event_type == "event.updated":
                result = await self._handle_event_updated(event.payload)

            elif event_type == "event.deleted":
                result = await self._handle_event_deleted(event.payload)

            elif event_type == "sync":
                # Full sync requested
                result = {"action": "trigger_sync"}

            result["processed"] = True

        except Exception as e:
            logger.error(f"Calendar webhook error: {e}")
            result["error"] = str(e)

        return result

    async def create_focus_block(
        self,
        user_calendar_id: str,
        task: Dict[str, Any],
        start_time: Optional[datetime] = None,
        duration_minutes: Optional[int] = None
    ) -> Dict[str, Any]:
        """Create a focus time block for a task"""
        if not start_time:
            start_time = await self._find_available_slot(user_calendar_id)

        duration = duration_minutes or self.focus_block_duration

        event = {
            "summary": f"Focus: {task.get('title')}",
            "description": f"Focus time for TaskPulse task.\n\n{task.get('description', '')}",
            "start": start_time.isoformat(),
            "end": (start_time + timedelta(minutes=duration)).isoformat(),
            "colorId": self.PRIORITY_COLORS.get(task.get("priority", "medium")),
            "reminders": {
                "useDefault": False,
                "overrides": [
                    {"method": "popup", "minutes": 5},
                ]
            },
            "extendedProperties": {
                "private": {
                    "taskpulse_task_id": task.get("id"),
                    "taskpulse_type": "focus_block",
                }
            }
        }

        logger.info(f"Would create focus block: {event['summary']} at {start_time}")

        return {"event_id": "focus_123", "start": start_time.isoformat()}

    async def create_deadline_event(
        self,
        user_calendar_id: str,
        task: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Create a deadline event for a task"""
        due_date = task.get("due_date")
        if not due_date:
            return {"error": "No due date"}

        if isinstance(due_date, str):
            due_date = datetime.fromisoformat(due_date)

        event = {
            "summary": f"Due: {task.get('title')}",
            "description": f"Deadline for TaskPulse task.",
            "start": {"date": due_date.strftime("%Y-%m-%d")},
            "end": {"date": due_date.strftime("%Y-%m-%d")},
            "colorId": self.PRIORITY_COLORS.get(task.get("priority", "medium")),
            "transparency": "transparent",  # Doesn't block time
            "reminders": {
                "useDefault": False,
                "overrides": [
                    {"method": "email", "minutes": 1440},  # 1 day before
                    {"method": "popup", "minutes": 60},
                ]
            },
        }

        logger.info(f"Would create deadline event: {event['summary']}")

        return {"event_id": "deadline_123"}

    async def schedule_meeting(
        self,
        organizer_calendar_id: str,
        attendee_emails: List[str],
        task: Dict[str, Any],
        duration_minutes: int = 30,
        title: Optional[str] = None
    ) -> Dict[str, Any]:
        """Schedule a meeting related to a task"""
        start_time = await self._find_common_availability(
            [organizer_calendar_id] + attendee_emails,
            duration_minutes
        )

        meeting_title = title or f"Discuss: {task.get('title')}"

        event = {
            "summary": meeting_title,
            "description": f"Meeting to discuss TaskPulse task.\n\nTask: {task.get('title')}\n{task.get('description', '')}",
            "start": start_time.isoformat(),
            "end": (start_time + timedelta(minutes=duration_minutes)).isoformat(),
            "attendees": [{"email": email} for email in attendee_emails],
            "conferenceData": {
                "createRequest": {
                    "requestId": f"taskpulse_{task.get('id')}",
                    "conferenceSolutionKey": {"type": "hangoutsMeet"}
                }
            },
        }

        logger.info(f"Would schedule meeting: {meeting_title}")

        return {
            "event_id": "meeting_123",
            "start": start_time.isoformat(),
            "meet_link": "https://meet.google.com/xxx-xxxx-xxx"
        }

    async def check_availability(
        self,
        user_calendar_ids: List[str],
        start_time: datetime,
        end_time: datetime
    ) -> Dict[str, Any]:
        """Check availability for users"""
        # In production, use Google Calendar freebusy API
        availability = {}

        for calendar_id in user_calendar_ids:
            availability[calendar_id] = {
                "busy_periods": [],
                "is_available": True,
            }

        return availability

    async def _fetch_calendar_events(self) -> List[Dict[str, Any]]:
        """Fetch events from calendar API"""
        # Mock response
        return [
            {
                "id": "event_1",
                "summary": "Focus: API Development",
                "description": "TaskPulse focus block",
                "start": {"dateTime": "2024-01-17T09:00:00Z"},
                "end": {"dateTime": "2024-01-17T10:30:00Z"},
                "extendedProperties": {
                    "private": {"taskpulse_task_id": "task_123"}
                }
            },
        ]

    def _is_task_event(self, event: Dict[str, Any]) -> bool:
        """Check if calendar event is related to a task"""
        props = event.get("extendedProperties", {}).get("private", {})
        return "taskpulse_task_id" in props

    def _map_event_to_task(self, event: Dict[str, Any]) -> Dict[str, Any]:
        """Map calendar event to task data"""
        summary = event.get("summary", "")

        # Extract task title (remove prefixes like "Focus:", "Due:")
        title = summary
        for prefix in ["Focus:", "Due:", "Meeting:"]:
            if summary.startswith(prefix):
                title = summary[len(prefix):].strip()
                break

        start = event.get("start", {})
        end = event.get("end", {})

        # Calculate duration
        if "dateTime" in start and "dateTime" in end:
            start_dt = datetime.fromisoformat(start["dateTime"].replace("Z", "+00:00"))
            end_dt = datetime.fromisoformat(end["dateTime"].replace("Z", "+00:00"))
            duration_hours = (end_dt - start_dt).total_seconds() / 3600
        else:
            duration_hours = None

        return {
            "external_id": f"calendar_{event['id']}",
            "title": title,
            "description": event.get("description", ""),
            "estimated_hours": duration_hours,
            "metadata": {
                "calendar_event_id": event["id"],
                "calendar_type": self._get_event_type(summary),
            },
        }

    def _get_event_type(self, summary: str) -> str:
        """Determine event type from summary"""
        if summary.startswith("Focus:"):
            return "focus_block"
        elif summary.startswith("Due:"):
            return "deadline"
        elif summary.startswith("Meeting:"):
            return "meeting"
        return "general"

    def _task_exists(self, external_id: str) -> bool:
        """Check if task already exists"""
        return False

    async def _get_tasks_to_sync(self, context: AgentContext) -> List[Dict[str, Any]]:
        """Get tasks that need calendar sync"""
        return []

    async def _create_calendar_event(self, task: Dict[str, Any]) -> str:
        """Create calendar event from task"""
        if task.get("due_date") and self.sync_deadlines:
            result = await self.create_deadline_event(self.calendar_id, task)
            return result.get("event_id", "")
        return ""

    async def _update_calendar_event(self, task: Dict[str, Any]) -> None:
        """Update existing calendar event"""
        event_id = task.get("calendar_event_id")
        logger.info(f"Would update calendar event {event_id}")

    async def _handle_event_created(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Handle event created webhook"""
        event = payload.get("event", {})
        if self._is_task_event(event):
            return {"action": "sync_from_calendar"}
        return {"action": None}

    async def _handle_event_updated(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Handle event updated webhook"""
        event = payload.get("event", {})
        if self._is_task_event(event):
            task_data = self._map_event_to_task(event)
            return {"action": "update_task", "task_data": task_data}
        return {"action": None}

    async def _handle_event_deleted(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Handle event deleted webhook"""
        event_id = payload.get("event_id")
        return {
            "action": "unlink_calendar",
            "event_id": event_id,
        }

    async def _find_available_slot(
        self,
        calendar_id: str,
        duration_minutes: int = 90,
        start_from: Optional[datetime] = None
    ) -> datetime:
        """Find next available time slot"""
        # In production, query calendar for free slots
        start = start_from or datetime.utcnow()

        # Round to next hour
        start = start.replace(minute=0, second=0, microsecond=0) + timedelta(hours=1)

        # Skip if outside working hours (9 AM - 6 PM)
        if start.hour < 9:
            start = start.replace(hour=9)
        elif start.hour >= 18:
            start = (start + timedelta(days=1)).replace(hour=9)

        return start

    async def _find_common_availability(
        self,
        calendar_ids: List[str],
        duration_minutes: int
    ) -> datetime:
        """Find common available time for multiple calendars"""
        # In production, use freebusy query
        return await self._find_available_slot(
            calendar_ids[0] if calendar_ids else "primary",
            duration_minutes
        )

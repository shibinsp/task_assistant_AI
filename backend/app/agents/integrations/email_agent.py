"""
Email Integration Agent

Send email notifications, digests, and handle incoming emails.
"""

import logging
from datetime import datetime
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


class EmailAgent(BaseIntegrationAgent):
    """
    Email integration agent for notifications and digests.

    Features:
    - Send email notifications
    - Daily/weekly digest emails
    - Escalation notifications
    - Parse incoming emails to create tasks
    """

    integration_type = "email"
    name = "email_agent"
    description = "Email integration for notifications and digests"
    version = "1.0.0"

    capabilities = [AgentCapability.EMAIL_NOTIFY]

    sync_direction = SyncDirection.BIDIRECTIONAL

    # Email templates
    TEMPLATES = {
        "task_assigned": "task_assigned",
        "task_completed": "task_completed",
        "task_blocked": "task_blocked",
        "checkin_reminder": "checkin_reminder",
        "daily_digest": "daily_digest",
        "weekly_digest": "weekly_digest",
        "escalation": "escalation",
    }

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        super().__init__(config)
        self.smtp_host: Optional[str] = None
        self.smtp_port: int = 587
        self.smtp_user: Optional[str] = None
        self.smtp_password: Optional[str] = None
        self.from_email: str = "taskpulse@company.com"
        self.from_name: str = "TaskPulse - AI Assistant"

        if config:
            self.smtp_host = config.get("smtp_host")
            self.smtp_port = config.get("smtp_port", 587)
            self.smtp_user = config.get("smtp_user")
            self.smtp_password = config.get("smtp_password")
            self.from_email = config.get("from_email", self.from_email)
            self.from_name = config.get("from_name", self.from_name)

    async def sync_inbound(self, context: AgentContext) -> List[Dict[str, Any]]:
        """Parse incoming emails to create tasks"""
        synced_items = []

        try:
            # In production, this would connect to IMAP/email API
            emails = await self._fetch_incoming_emails()

            for email in emails:
                task_data = self._parse_email_to_task(email)
                if task_data:
                    synced_items.append({
                        **task_data,
                        "is_new": True,
                        "source": "email",
                    })

        except Exception as e:
            logger.error(f"Email inbound sync error: {e}")
            raise

        return synced_items

    async def sync_outbound(self, context: AgentContext) -> Dict[str, Any]:
        """Send pending email notifications"""
        result = {"count": 0, "sent": 0, "failed": 0}

        try:
            notifications = await self._get_pending_notifications(context)

            for notification in notifications:
                try:
                    await self._send_email(notification)
                    result["sent"] += 1
                except Exception as e:
                    logger.error(f"Failed to send email: {e}")
                    result["failed"] += 1

                result["count"] += 1

        except Exception as e:
            logger.error(f"Email outbound sync error: {e}")
            raise

        return result

    async def handle_webhook(self, event: WebhookEvent) -> Dict[str, Any]:
        """Handle email webhooks (e.g., SendGrid, Mailgun)"""
        result = {"processed": False}

        try:
            event_type = event.payload.get("event")

            if event_type == "inbound":
                # Incoming email
                email_data = event.payload.get("email", {})
                task = self._parse_email_to_task(email_data)
                if task:
                    result = {"action": "create_task", "task_data": task}

            elif event_type == "delivered":
                result = {"action": "log_delivery", "status": "delivered"}

            elif event_type == "bounced":
                result = {"action": "log_bounce", "email": event.payload.get("email")}

            elif event_type == "opened":
                result = {"action": "log_open", "email": event.payload.get("email")}

            result["processed"] = True

        except Exception as e:
            logger.error(f"Email webhook error: {e}")
            result["error"] = str(e)

        return result

    async def send_notification(
        self,
        to_email: str,
        notification_type: str,
        data: Dict[str, Any],
        to_name: Optional[str] = None
    ) -> bool:
        """Send a notification email"""
        template = self.TEMPLATES.get(notification_type)
        if not template:
            logger.warning(f"Unknown notification type: {notification_type}")
            return False

        subject, html_body, text_body = self._render_template(template, data)

        return await self._send_email({
            "to_email": to_email,
            "to_name": to_name,
            "subject": subject,
            "html_body": html_body,
            "text_body": text_body,
        })

    async def send_daily_digest(
        self,
        user_email: str,
        user_name: str,
        tasks: List[Dict[str, Any]],
        stats: Dict[str, Any]
    ) -> bool:
        """Send daily digest email"""
        data = {
            "user_name": user_name,
            "date": datetime.utcnow().strftime("%B %d, %Y"),
            "tasks": tasks,
            "stats": stats,
        }

        return await self.send_notification(
            to_email=user_email,
            notification_type="daily_digest",
            data=data,
            to_name=user_name
        )

    async def send_escalation(
        self,
        manager_email: str,
        manager_name: str,
        employee_name: str,
        task: Dict[str, Any],
        reason: str
    ) -> bool:
        """Send escalation email to manager"""
        data = {
            "manager_name": manager_name,
            "employee_name": employee_name,
            "task": task,
            "reason": reason,
            "escalated_at": datetime.utcnow().isoformat(),
        }

        return await self.send_notification(
            to_email=manager_email,
            notification_type="escalation",
            data=data,
            to_name=manager_name
        )

    async def _fetch_incoming_emails(self) -> List[Dict[str, Any]]:
        """Fetch incoming emails from mailbox"""
        # In production, connect to IMAP or email API
        return []

    def _parse_email_to_task(self, email: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Parse email to extract task data"""
        subject = email.get("subject", "")
        body = email.get("body", "")
        sender = email.get("from", "")

        # Check if this looks like a task request
        task_indicators = ["todo:", "task:", "action:", "[task]", "[action]"]

        is_task = any(ind in subject.lower() for ind in task_indicators)

        if not is_task:
            return None

        # Extract task info
        title = subject
        for ind in task_indicators:
            title = title.lower().replace(ind, "").strip()
            title = title.capitalize()

        return {
            "external_id": email.get("message_id", ""),
            "title": title,
            "description": body[:1000],
            "status": "pending",
            "priority": "medium",
            "metadata": {
                "source": "email",
                "from_email": sender,
                "received_at": email.get("date"),
            },
        }

    async def _get_pending_notifications(
        self,
        context: AgentContext
    ) -> List[Dict[str, Any]]:
        """Get notifications waiting to be sent"""
        return []

    async def _send_email(self, email: Dict[str, Any]) -> bool:
        """Send email via SMTP or email service"""
        # In production, use aiosmtplib or email service API

        logger.info(
            f"Would send email to {email.get('to_email')}: {email.get('subject')}"
        )

        return True

    def _render_template(
        self,
        template_name: str,
        data: Dict[str, Any]
    ) -> tuple:
        """Render email template"""
        templates = {
            "task_assigned": self._template_task_assigned,
            "task_completed": self._template_task_completed,
            "task_blocked": self._template_task_blocked,
            "checkin_reminder": self._template_checkin_reminder,
            "daily_digest": self._template_daily_digest,
            "weekly_digest": self._template_weekly_digest,
            "escalation": self._template_escalation,
        }

        template_fn = templates.get(template_name)
        if template_fn:
            return template_fn(data)

        return ("TaskPulse Notification", "<p>Notification</p>", "Notification")

    def _template_task_assigned(self, data: Dict[str, Any]) -> tuple:
        task = data.get("task", {})
        subject = f"New Task Assigned: {task.get('title', 'Untitled')}"

        html = f"""
        <h2>You've been assigned a new task</h2>
        <h3>{task.get('title')}</h3>
        <p>{task.get('description', 'No description')}</p>
        <p><strong>Priority:</strong> {task.get('priority', 'Medium')}</p>
        <p><strong>Due:</strong> {task.get('due_date', 'No deadline')}</p>
        <p><a href="{data.get('task_url', '#')}">View Task</a></p>
        """

        text = f"""
        New Task: {task.get('title')}
        {task.get('description', '')}
        Priority: {task.get('priority')}
        Due: {task.get('due_date', 'No deadline')}
        """

        return subject, html, text

    def _template_task_completed(self, data: Dict[str, Any]) -> tuple:
        task = data.get("task", {})
        subject = f"Task Completed: {task.get('title', 'Untitled')}"

        html = f"""
        <h2>Task Completed!</h2>
        <h3>{task.get('title')}</h3>
        <p>Completed by: {data.get('completed_by', 'Unknown')}</p>
        """

        text = f"Task Completed: {task.get('title')}"

        return subject, html, text

    def _template_task_blocked(self, data: Dict[str, Any]) -> tuple:
        task = data.get("task", {})
        subject = f"Task Blocked: {task.get('title', 'Untitled')}"

        html = f"""
        <h2>Task Blocked</h2>
        <h3>{task.get('title')}</h3>
        <p><strong>Reason:</strong> {data.get('blocker_description', 'Unknown')}</p>
        <p><a href="{data.get('task_url', '#')}">View Task</a></p>
        """

        text = f"Task Blocked: {task.get('title')}\nReason: {data.get('blocker_description')}"

        return subject, html, text

    def _template_checkin_reminder(self, data: Dict[str, Any]) -> tuple:
        task = data.get("task", {})
        subject = f"Check-in Time: {task.get('title', 'Your Task')}"

        html = f"""
        <h2>Time for a check-in!</h2>
        <p>How's your progress on: <strong>{task.get('title')}</strong>?</p>
        <p><a href="{data.get('checkin_url', '#')}">Submit Check-in</a></p>
        """

        text = f"Check-in reminder for: {task.get('title')}"

        return subject, html, text

    def _template_daily_digest(self, data: Dict[str, Any]) -> tuple:
        subject = f"Your Daily Digest - {data.get('date')}"

        tasks_html = ""
        for task in data.get("tasks", [])[:10]:
            tasks_html += f"<li>{task.get('title')} - {task.get('status')}</li>"

        stats = data.get("stats", {})

        html = f"""
        <h2>Good morning, {data.get('user_name')}!</h2>
        <h3>Your Tasks for Today</h3>
        <ul>{tasks_html}</ul>
        <h3>Quick Stats</h3>
        <p>Completed yesterday: {stats.get('completed_yesterday', 0)}</p>
        <p>In progress: {stats.get('in_progress', 0)}</p>
        <p>Due today: {stats.get('due_today', 0)}</p>
        """

        text = f"Daily Digest for {data.get('user_name')}"

        return subject, html, text

    def _template_weekly_digest(self, data: Dict[str, Any]) -> tuple:
        subject = "Your Weekly Summary - TaskPulse"

        stats = data.get("stats", {})

        html = f"""
        <h2>Weekly Summary for {data.get('user_name')}</h2>
        <h3>This Week's Achievements</h3>
        <p>Tasks completed: {stats.get('completed', 0)}</p>
        <p>On-time delivery: {stats.get('on_time_percent', 0)}%</p>
        <p>Hours logged: {stats.get('hours_logged', 0)}</p>
        """

        text = f"Weekly summary: {stats.get('completed', 0)} tasks completed"

        return subject, html, text

    def _template_escalation(self, data: Dict[str, Any]) -> tuple:
        task = data.get("task", {})
        subject = f"Escalation: {task.get('title', 'Task')} - {data.get('employee_name')}"

        html = f"""
        <h2>Task Escalation</h2>
        <p>Hi {data.get('manager_name')},</p>
        <p>A task assigned to <strong>{data.get('employee_name')}</strong> requires your attention.</p>
        <h3>{task.get('title')}</h3>
        <p><strong>Reason:</strong> {data.get('reason')}</p>
        <p><strong>Escalated at:</strong> {data.get('escalated_at')}</p>
        <p><a href="{data.get('task_url', '#')}">View Task</a></p>
        """

        text = f"Escalation: {task.get('title')} needs attention"

        return subject, html, text

"""
Slack Integration Agent

Send notifications, handle slash commands, and interactive messages.
"""

import logging
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


class SlackAgent(BaseIntegrationAgent):
    """
    Slack integration agent for notifications and interactions.

    Features:
    - Send notifications to channels
    - Handle slash commands (/taskpulse, /checkin)
    - Interactive check-in messages
    - Thread-based task discussions
    - User mention notifications
    """

    integration_type = "slack"
    name = "slack_agent"
    description = "Slack integration for notifications and commands"
    version = "1.0.0"

    capabilities = [AgentCapability.SLACK_NOTIFY]

    api_base_url = "https://slack.com/api"
    api_version = "v1"

    sync_direction = SyncDirection.OUTBOUND

    # Default channels for different notification types
    DEFAULT_CHANNELS = {
        "task_assigned": "#tasks",
        "task_completed": "#tasks",
        "task_blocked": "#alerts",
        "checkin_due": None,  # DM to user
        "escalation": "#managers",
        "daily_digest": "#general",
    }

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        super().__init__(config)
        self.bot_token: Optional[str] = None
        self.signing_secret: Optional[str] = None
        self.default_channel: str = "#general"
        self.mention_format = "<@{user_id}>"

        if config:
            self.bot_token = config.get("bot_token")
            self.signing_secret = config.get("signing_secret")
            self.default_channel = config.get("default_channel", "#general")

    async def sync_inbound(self, context: AgentContext) -> List[Dict[str, Any]]:
        """Slack is primarily outbound - inbound handled via webhooks"""
        return []

    async def sync_outbound(self, context: AgentContext) -> Dict[str, Any]:
        """Send pending notifications to Slack"""
        result = {"count": 0, "sent": 0, "failed": 0}

        try:
            notifications = await self._get_pending_notifications(context)

            for notification in notifications:
                try:
                    await self._send_notification(notification)
                    result["sent"] += 1
                except Exception as e:
                    logger.error(f"Failed to send notification: {e}")
                    result["failed"] += 1

                result["count"] += 1

        except Exception as e:
            logger.error(f"Slack outbound sync error: {e}")
            raise

        return result

    async def handle_webhook(self, event: WebhookEvent) -> Dict[str, Any]:
        """Handle Slack webhook events"""
        result = {"processed": False}

        try:
            event_type = event.payload.get("type")

            if event_type == "url_verification":
                # Slack URL verification challenge
                result = {
                    "challenge": event.payload.get("challenge"),
                    "processed": True,
                }

            elif event_type == "event_callback":
                inner_event = event.payload.get("event", {})
                result = await self._handle_event_callback(inner_event)

            elif event_type == "slash_command":
                result = await self._handle_slash_command(event.payload)

            elif event_type == "interactive_message":
                result = await self._handle_interactive(event.payload)

            elif event_type == "block_actions":
                result = await self._handle_block_actions(event.payload)

            result["processed"] = True

        except Exception as e:
            logger.error(f"Slack webhook error: {e}")
            result["error"] = str(e)

        return result

    async def send_message(
        self,
        channel: str,
        text: str,
        blocks: Optional[List[Dict[str, Any]]] = None,
        thread_ts: Optional[str] = None,
        user_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """Send a message to Slack"""
        # POST chat.postMessage

        payload = {
            "channel": channel,
            "text": text,
        }

        if blocks:
            payload["blocks"] = blocks

        if thread_ts:
            payload["thread_ts"] = thread_ts

        # If user_id provided, send as DM
        if user_id and not channel.startswith("#"):
            payload["channel"] = user_id

        logger.info(f"Would send Slack message to {channel}: {text[:50]}...")

        return {"ok": True, "ts": "1234567890.123456"}

    async def send_checkin_request(
        self,
        user_slack_id: str,
        task: Dict[str, Any],
        checkin_id: str
    ) -> Dict[str, Any]:
        """Send interactive check-in request to user"""

        blocks = [
            {
                "type": "header",
                "text": {
                    "type": "plain_text",
                    "text": "How's your progress? ",
                }
            },
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": f"*Task:* {task.get('title')}\n*Due:* {task.get('due_date', 'No deadline')}",
                }
            },
            {
                "type": "divider"
            },
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": "How are things going?",
                },
                "accessory": {
                    "type": "static_select",
                    "placeholder": {
                        "type": "plain_text",
                        "text": "Select progress",
                    },
                    "options": [
                        {
                            "text": {"type": "plain_text", "text": "On track "},
                            "value": "on_track"
                        },
                        {
                            "text": {"type": "plain_text", "text": "Slight delay"},
                            "value": "slight_delay"
                        },
                        {
                            "text": {"type": "plain_text", "text": "Blocked "},
                            "value": "blocked"
                        },
                        {
                            "text": {"type": "plain_text", "text": "Need help"},
                            "value": "need_help"
                        },
                    ],
                    "action_id": f"checkin_progress_{checkin_id}",
                }
            },
            {
                "type": "input",
                "block_id": "checkin_notes",
                "element": {
                    "type": "plain_text_input",
                    "action_id": "notes_input",
                    "placeholder": {
                        "type": "plain_text",
                        "text": "Any updates or blockers? (optional)",
                    },
                    "multiline": True,
                },
                "label": {
                    "type": "plain_text",
                    "text": "Notes",
                },
                "optional": True,
            },
            {
                "type": "actions",
                "elements": [
                    {
                        "type": "button",
                        "text": {"type": "plain_text", "text": "Submit Check-in"},
                        "style": "primary",
                        "action_id": f"submit_checkin_{checkin_id}",
                    },
                    {
                        "type": "button",
                        "text": {"type": "plain_text", "text": "Snooze 1hr"},
                        "action_id": f"snooze_checkin_{checkin_id}",
                    },
                ]
            }
        ]

        return await self.send_message(
            channel=user_slack_id,
            text=f"Check-in time for: {task.get('title')}",
            blocks=blocks
        )

    async def send_task_notification(
        self,
        channel: str,
        task: Dict[str, Any],
        notification_type: str,
        assignee_slack_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """Send task notification"""

        colors = {
            "assigned": "#36a64f",  # Green
            "completed": "#2eb886",  # Teal
            "blocked": "#ff6b6b",   # Red
            "updated": "#3498db",   # Blue
        }

        color = colors.get(notification_type, "#808080")

        attachments = [
            {
                "color": color,
                "blocks": [
                    {
                        "type": "section",
                        "text": {
                            "type": "mrkdwn",
                            "text": self._format_task_notification(
                                task, notification_type, assignee_slack_id
                            ),
                        }
                    },
                    {
                        "type": "context",
                        "elements": [
                            {
                                "type": "mrkdwn",
                                "text": f"Priority: *{task.get('priority', 'medium')}* | Due: {task.get('due_date', 'No deadline')}",
                            }
                        ]
                    }
                ]
            }
        ]

        return await self.send_message(
            channel=channel,
            text=f"Task {notification_type}: {task.get('title')}",
            blocks=attachments[0]["blocks"]
        )

    def _format_task_notification(
        self,
        task: Dict[str, Any],
        notification_type: str,
        assignee_slack_id: Optional[str]
    ) -> str:
        """Format task notification message"""

        title = task.get("title", "Untitled Task")

        if notification_type == "assigned":
            if assignee_slack_id:
                return f" *New Task Assigned*\n<@{assignee_slack_id}> has been assigned: *{title}*"
            return f" *Task Assigned*: *{title}*"

        elif notification_type == "completed":
            return f" *Task Completed*: ~{title}~"

        elif notification_type == "blocked":
            blocker = task.get("blocker_description", "Unknown blocker")
            return f" *Task Blocked*: *{title}*\n> {blocker}"

        elif notification_type == "updated":
            return f" *Task Updated*: *{title}*"

        return f"*{title}*"

    async def _get_pending_notifications(
        self,
        context: AgentContext
    ) -> List[Dict[str, Any]]:
        """Get notifications waiting to be sent"""
        # In production, query notification queue
        return []

    async def _send_notification(self, notification: Dict[str, Any]) -> None:
        """Send a single notification"""
        notification_type = notification.get("type")
        channel = self.DEFAULT_CHANNELS.get(notification_type, self.default_channel)

        if channel is None:
            # DM to user
            channel = notification.get("user_slack_id")

        await self.send_message(
            channel=channel,
            text=notification.get("text", ""),
            blocks=notification.get("blocks")
        )

    async def _handle_event_callback(self, event: Dict[str, Any]) -> Dict[str, Any]:
        """Handle Slack event callbacks"""
        event_type = event.get("type")

        if event_type == "message":
            # Handle messages mentioning the bot
            if event.get("bot_id"):
                return {"skipped": True, "reason": "Bot message"}

            text = event.get("text", "")
            if "@taskpulse" in text.lower():
                return await self._handle_mention(event)

        elif event_type == "app_mention":
            return await self._handle_mention(event)

        return {"action": None}

    async def _handle_mention(self, event: Dict[str, Any]) -> Dict[str, Any]:
        """Handle bot mentions"""
        text = event.get("text", "")
        user = event.get("user")
        channel = event.get("channel")

        # Parse command from mention
        commands = {
            "status": self._cmd_status,
            "my tasks": self._cmd_my_tasks,
            "help": self._cmd_help,
        }

        for cmd, handler in commands.items():
            if cmd in text.lower():
                response = await handler(user)
                await self.send_message(
                    channel=channel,
                    text=response,
                    thread_ts=event.get("ts")
                )
                return {"action": "command", "command": cmd}

        # Default response
        await self.send_message(
            channel=channel,
            text="I can help with: `status`, `my tasks`, `help`",
            thread_ts=event.get("ts")
        )
        return {"action": "help"}

    async def _handle_slash_command(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Handle slash commands"""
        command = payload.get("command", "")
        text = payload.get("text", "")
        user_id = payload.get("user_id")

        if command == "/taskpulse":
            subcommand = text.split()[0] if text else "help"

            if subcommand == "status":
                return {
                    "response_type": "ephemeral",
                    "text": await self._cmd_status(user_id),
                }
            elif subcommand == "tasks":
                return {
                    "response_type": "ephemeral",
                    "text": await self._cmd_my_tasks(user_id),
                }
            else:
                return {
                    "response_type": "ephemeral",
                    "text": await self._cmd_help(user_id),
                }

        elif command == "/checkin":
            return {
                "response_type": "ephemeral",
                "text": "Starting check-in...",
                "trigger_checkin": True,
            }

        return {"response_type": "ephemeral", "text": "Unknown command"}

    async def _handle_interactive(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Handle interactive message responses"""
        callback_id = payload.get("callback_id", "")
        actions = payload.get("actions", [])

        if "checkin" in callback_id:
            return await self._handle_checkin_response(payload, actions)

        return {"action": None}

    async def _handle_block_actions(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Handle block action interactions"""
        actions = payload.get("actions", [])

        for action in actions:
            action_id = action.get("action_id", "")

            if action_id.startswith("submit_checkin_"):
                checkin_id = action_id.replace("submit_checkin_", "")
                return await self._submit_checkin(payload, checkin_id)

            elif action_id.startswith("snooze_checkin_"):
                checkin_id = action_id.replace("snooze_checkin_", "")
                return {"action": "snooze", "checkin_id": checkin_id, "duration": 3600}

            elif action_id.startswith("checkin_progress_"):
                # Progress selection - wait for submit
                return {"action": "progress_selected", "value": action.get("selected_option", {}).get("value")}

        return {"action": None}

    async def _submit_checkin(
        self,
        payload: Dict[str, Any],
        checkin_id: str
    ) -> Dict[str, Any]:
        """Process submitted check-in"""
        state = payload.get("state", {}).get("values", {})

        # Extract progress from state
        progress = None
        notes = None

        for block_id, block_data in state.items():
            for action_id, action_data in block_data.items():
                if "progress" in action_id:
                    progress = action_data.get("selected_option", {}).get("value")
                elif action_id == "notes_input":
                    notes = action_data.get("value")

        return {
            "action": "submit_checkin",
            "checkin_id": checkin_id,
            "progress": progress,
            "notes": notes,
            "user_id": payload.get("user", {}).get("id"),
        }

    async def _handle_checkin_response(
        self,
        payload: Dict[str, Any],
        actions: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Handle check-in response"""
        return {"action": "checkin_response", "payload": payload}

    async def _cmd_status(self, user_id: str) -> str:
        """Get user's task status"""
        # In production, query user's tasks
        return " *Your Status*\n• Active tasks: 3\n• Completed today: 2\n• Blocked: 0"

    async def _cmd_my_tasks(self, user_id: str) -> str:
        """Get user's task list"""
        return " *Your Tasks*\n1. Implement API endpoint (In Progress)\n2. Write tests (Pending)\n3. Update docs (Pending)"

    async def _cmd_help(self, user_id: str) -> str:
        """Get help text"""
        return """*TaskPulse Commands*
• `status` - View your current status
• `my tasks` - List your active tasks
• `/checkin` - Start a progress check-in
• `/taskpulse help` - Show this message"""

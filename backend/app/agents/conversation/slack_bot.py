"""
Slack Bot Agent

Slack-native conversational interface for TaskPulse - AI Assistant.
Handles Slack interactions, commands, and notifications.
"""

import logging
from typing import Any, Dict, List, Optional

from ..base import (
    AgentCapability,
    AgentEvent,
    AgentResult,
    BaseAgent,
    EventType,
)
from ..context import AgentContext, MessageRole

logger = logging.getLogger(__name__)


class SlackBotAgent(BaseAgent):
    """
    Slack bot conversational agent.

    Features:
    - Handle Slack messages and mentions
    - Process slash commands
    - Interactive message responses
    - Rich Slack block formatting
    """

    name = "slack_bot_agent"
    description = "Slack-native conversational interface"
    version = "1.0.0"

    capabilities = [
        AgentCapability.CHAT,
        AgentCapability.NATURAL_LANGUAGE,
    ]

    handled_events = [
        EventType.USER_MESSAGE,
        EventType.USER_COMMAND,
    ]

    priority = 10

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        super().__init__(config)
        self.bot_user_id: Optional[str] = config.get("bot_user_id") if config else None

    async def can_handle(self, event: AgentEvent) -> bool:
        """Handle Slack-sourced messages"""
        source = event.payload.get("source", "") if event.payload else ""
        return source == "slack"

    async def execute(self, context: AgentContext) -> AgentResult:
        """Process Slack message and generate response"""
        result = AgentResult(
            success=True,
            agent_name=self.name,
            event_id=context.event.id if context.event else "direct"
        )

        try:
            payload = context.event.payload if context.event else {}
            message_type = payload.get("type", "message")

            if message_type == "slash_command":
                response = await self._handle_slash_command(payload, context)
            elif message_type == "interactive":
                response = await self._handle_interactive(payload, context)
            else:
                response = await self._handle_message(payload, context)

            result.output = response
            result.message = response.get("text", "")

            # Add Slack-specific formatting
            if response.get("blocks"):
                result.output["slack_blocks"] = response["blocks"]

        except Exception as e:
            logger.error(f"Slack bot error: {e}")
            result.success = False
            result.error = str(e)
            result.message = "Sorry, I encountered an error. Please try again."

        return result

    async def _handle_message(
        self,
        payload: Dict[str, Any],
        context: AgentContext
    ) -> Dict[str, Any]:
        """Handle regular Slack messages"""
        text = payload.get("text", "").strip()

        # Remove bot mention if present
        if self.bot_user_id:
            text = text.replace(f"<@{self.bot_user_id}>", "").strip()

        # Parse command from message
        command = self._parse_command(text)

        handlers = {
            "status": self._cmd_status,
            "tasks": self._cmd_tasks,
            "help": self._cmd_help,
            "checkin": self._cmd_checkin,
        }

        handler = handlers.get(command, self._cmd_default)
        return await handler(text, context)

    async def _handle_slash_command(
        self,
        payload: Dict[str, Any],
        context: AgentContext
    ) -> Dict[str, Any]:
        """Handle Slack slash commands"""
        command = payload.get("command", "")
        text = payload.get("text", "")

        if command == "/taskpulse":
            subcommand = text.split()[0] if text else "help"

            if subcommand == "status":
                return await self._cmd_status(text, context)
            elif subcommand == "tasks":
                return await self._cmd_tasks(text, context)
            elif subcommand == "checkin":
                return await self._cmd_checkin(text, context)
            elif subcommand == "create":
                return await self._cmd_create(text, context)
            else:
                return await self._cmd_help(text, context)

        elif command == "/checkin":
            return await self._cmd_checkin(text, context)

        return await self._cmd_help(text, context)

    async def _handle_interactive(
        self,
        payload: Dict[str, Any],
        context: AgentContext
    ) -> Dict[str, Any]:
        """Handle interactive message responses"""
        action_id = payload.get("action_id", "")
        value = payload.get("value", "")

        if "task_" in action_id:
            return await self._handle_task_action(action_id, value, context)
        elif "checkin_" in action_id:
            return await self._handle_checkin_action(action_id, value, context)

        return {"text": "Action processed", "response_type": "ephemeral"}

    def _parse_command(self, text: str) -> str:
        """Parse command from message text"""
        text_lower = text.lower()

        commands = {
            "status": ["status", "how am i", "my progress"],
            "tasks": ["tasks", "my tasks", "show tasks", "what should i"],
            "help": ["help", "stuck", "blocked", "need help"],
            "checkin": ["checkin", "check in", "check-in"],
        }

        for cmd, triggers in commands.items():
            if any(t in text_lower for t in triggers):
                return cmd

        return "default"

    async def _cmd_status(
        self,
        text: str,
        context: AgentContext
    ) -> Dict[str, Any]:
        """Get user status"""
        stats = await self._get_stats(context)

        blocks = [
            {
                "type": "header",
                "text": {"type": "plain_text", "text": "Your Status"}
            },
            {
                "type": "section",
                "fields": [
                    {"type": "mrkdwn", "text": f"*Active Tasks:* {stats['active']}"},
                    {"type": "mrkdwn", "text": f"*Completed Today:* {stats['completed']}"},
                    {"type": "mrkdwn", "text": f"*Blocked:* {stats['blocked']}"},
                    {"type": "mrkdwn", "text": f"*On-time:* {stats['on_time']}%"},
                ]
            },
            {
                "type": "context",
                "elements": [
                    {"type": "mrkdwn", "text": "Keep up the great work!"}
                ]
            }
        ]

        return {
            "text": f"Active: {stats['active']} | Completed: {stats['completed']}",
            "blocks": blocks,
            "response_type": "ephemeral",
        }

    async def _cmd_tasks(
        self,
        text: str,
        context: AgentContext
    ) -> Dict[str, Any]:
        """List user tasks"""
        tasks = await self._get_tasks(context)

        if not tasks:
            return {
                "text": "You have no active tasks.",
                "response_type": "ephemeral",
            }

        blocks = [
            {
                "type": "header",
                "text": {"type": "plain_text", "text": "Your Tasks"}
            }
        ]

        for task in tasks[:5]:
            priority_emoji = {"critical": "", "high": "", "medium": "", "low": ""}.get(task['priority'], "")

            blocks.append({
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": f"{priority_emoji} *{task['title']}*\n_{task['status']}_ | Due: {task.get('due_date', 'No deadline')}"
                },
                "accessory": {
                    "type": "button",
                    "text": {"type": "plain_text", "text": "View"},
                    "action_id": f"task_view_{task['id']}"
                }
            })

        return {
            "text": f"You have {len(tasks)} active tasks",
            "blocks": blocks,
            "response_type": "ephemeral",
        }

    async def _cmd_checkin(
        self,
        text: str,
        context: AgentContext
    ) -> Dict[str, Any]:
        """Start a check-in"""
        tasks = await self._get_tasks(context)
        current_task = tasks[0] if tasks else None

        if not current_task:
            return {
                "text": "No active tasks found for check-in.",
                "response_type": "ephemeral",
            }

        blocks = [
            {
                "type": "header",
                "text": {"type": "plain_text", "text": "Check-in Time"}
            },
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": f"How's your progress on *{current_task['title']}*?"
                }
            },
            {
                "type": "actions",
                "elements": [
                    {
                        "type": "button",
                        "text": {"type": "plain_text", "text": "On Track"},
                        "style": "primary",
                        "action_id": "checkin_on_track",
                        "value": current_task['id']
                    },
                    {
                        "type": "button",
                        "text": {"type": "plain_text", "text": "Slight Delay"},
                        "action_id": "checkin_delayed",
                        "value": current_task['id']
                    },
                    {
                        "type": "button",
                        "text": {"type": "plain_text", "text": "Blocked"},
                        "style": "danger",
                        "action_id": "checkin_blocked",
                        "value": current_task['id']
                    },
                ]
            }
        ]

        return {
            "text": "Check-in for: " + current_task['title'],
            "blocks": blocks,
            "response_type": "ephemeral",
        }

    async def _cmd_create(
        self,
        text: str,
        context: AgentContext
    ) -> Dict[str, Any]:
        """Create a new task"""
        # Extract task title from text
        parts = text.split(maxsplit=1)
        title = parts[1] if len(parts) > 1 else ""

        if not title:
            return {
                "text": "Please provide a task title: `/taskpulse create [title]`",
                "response_type": "ephemeral",
            }

        return {
            "text": f"Created task: {title}",
            "blocks": [
                {
                    "type": "section",
                    "text": {
                        "type": "mrkdwn",
                        "text": f"Task created: *{title}*"
                    }
                },
                {
                    "type": "actions",
                    "elements": [
                        {
                            "type": "button",
                            "text": {"type": "plain_text", "text": "Set Priority"},
                            "action_id": "task_priority"
                        },
                        {
                            "type": "button",
                            "text": {"type": "plain_text", "text": "Set Due Date"},
                            "action_id": "task_due"
                        },
                    ]
                }
            ],
            "response_type": "in_channel",
        }

    async def _cmd_help(
        self,
        text: str,
        context: AgentContext
    ) -> Dict[str, Any]:
        """Show help"""
        blocks = [
            {
                "type": "header",
                "text": {"type": "plain_text", "text": "TaskPulse Commands"}
            },
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": """
*Commands:*
• `/taskpulse status` - View your status
• `/taskpulse tasks` - List your tasks
• `/taskpulse create [title]` - Create a task
• `/checkin` - Start a check-in

*Or just mention me:*
• "What should I work on?"
• "I'm stuck on..."
• "Show my tasks"
"""
                }
            }
        ]

        return {
            "text": "TaskPulse Help",
            "blocks": blocks,
            "response_type": "ephemeral",
        }

    async def _cmd_default(
        self,
        text: str,
        context: AgentContext
    ) -> Dict[str, Any]:
        """Default response"""
        return {
            "text": f"I heard: '{text}'. Try `/taskpulse help` for available commands.",
            "response_type": "ephemeral",
        }

    async def _handle_task_action(
        self,
        action_id: str,
        value: str,
        context: AgentContext
    ) -> Dict[str, Any]:
        """Handle task-related actions"""
        if "view" in action_id:
            return {"text": f"Viewing task {value}...", "response_type": "ephemeral"}
        elif "complete" in action_id:
            return {"text": f"Marked task {value} as complete!", "response_type": "ephemeral"}

        return {"text": "Action processed", "response_type": "ephemeral"}

    async def _handle_checkin_action(
        self,
        action_id: str,
        value: str,
        context: AgentContext
    ) -> Dict[str, Any]:
        """Handle check-in actions"""
        status_map = {
            "on_track": ("on_track", "Great! Keep up the momentum!"),
            "delayed": ("delayed", "Thanks for the update. Let me know if you need help."),
            "blocked": ("blocked", "I'll help you get unblocked. What's the issue?"),
        }

        for status, (code, message) in status_map.items():
            if status in action_id:
                return {
                    "text": message,
                    "response_type": "ephemeral",
                    "checkin_status": code,
                    "task_id": value,
                }

        return {"text": "Check-in recorded", "response_type": "ephemeral"}

    async def _get_stats(self, context: AgentContext) -> Dict[str, Any]:
        """Get user stats"""
        return {"active": 5, "completed": 2, "blocked": 0, "on_time": 87}

    async def _get_tasks(self, context: AgentContext) -> List[Dict[str, Any]]:
        """Get user tasks"""
        return [
            {"id": "1", "title": "API Implementation", "status": "in_progress", "priority": "high"},
            {"id": "2", "title": "Write Tests", "status": "pending", "priority": "medium"},
        ]

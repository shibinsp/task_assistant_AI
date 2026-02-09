"""
Microsoft Teams Bot Agent

Teams-native conversational interface for TaskPulse - AI Assistant.
Uses Adaptive Cards for rich interactions.
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


class TeamsBotAgent(BaseAgent):
    """
    Microsoft Teams bot conversational agent.

    Features:
    - Handle Teams messages and mentions
    - Adaptive Card responses
    - Task actions and forms
    - Teams channel integration
    """

    name = "teams_bot_agent"
    description = "Microsoft Teams conversational interface"
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
        self.bot_id: Optional[str] = config.get("bot_id") if config else None
        self.app_id: Optional[str] = config.get("app_id") if config else None

    async def can_handle(self, event: AgentEvent) -> bool:
        """Handle Teams-sourced messages"""
        source = event.payload.get("source", "") if event.payload else ""
        return source == "teams"

    async def execute(self, context: AgentContext) -> AgentResult:
        """Process Teams message and generate response"""
        result = AgentResult(
            success=True,
            agent_name=self.name,
            event_id=context.event.id if context.event else "direct"
        )

        try:
            payload = context.event.payload if context.event else {}
            activity_type = payload.get("type", "message")

            if activity_type == "invoke":
                response = await self._handle_invoke(payload, context)
            elif activity_type == "message":
                response = await self._handle_message(payload, context)
            else:
                response = {"text": "Unsupported activity type"}

            result.output = response
            result.message = response.get("text", "")

            # Add Teams-specific adaptive card
            if response.get("adaptive_card"):
                result.output["teams_card"] = response["adaptive_card"]

        except Exception as e:
            logger.error(f"Teams bot error: {e}")
            result.success = False
            result.error = str(e)
            result.message = "Sorry, I encountered an error."

        return result

    async def _handle_message(
        self,
        payload: Dict[str, Any],
        context: AgentContext
    ) -> Dict[str, Any]:
        """Handle Teams messages"""
        text = payload.get("text", "").strip()

        # Remove bot mention
        text = self._remove_mentions(text)

        # Parse intent
        intent = self._parse_intent(text)

        handlers = {
            "status": self._show_status,
            "tasks": self._show_tasks,
            "checkin": self._start_checkin,
            "help": self._show_help,
            "create": self._create_task,
        }

        handler = handlers.get(intent, self._default_response)
        return await handler(text, context)

    async def _handle_invoke(
        self,
        payload: Dict[str, Any],
        context: AgentContext
    ) -> Dict[str, Any]:
        """Handle Teams invoke activities (card actions)"""
        action_name = payload.get("name", "")
        action_data = payload.get("value", {})

        if action_name == "task_action":
            return await self._handle_task_action(action_data, context)
        elif action_name == "checkin_submit":
            return await self._handle_checkin_submit(action_data, context)

        return {"status": 200}

    def _remove_mentions(self, text: str) -> str:
        """Remove @mentions from text"""
        import re
        return re.sub(r"<at>.*?</at>", "", text).strip()

    def _parse_intent(self, text: str) -> str:
        """Parse user intent from message"""
        text_lower = text.lower()

        intents = {
            "status": ["status", "how am i", "progress"],
            "tasks": ["tasks", "my tasks", "show tasks", "what should"],
            "checkin": ["checkin", "check in", "check-in"],
            "help": ["help", "commands"],
            "create": ["create task", "new task", "add task"],
        }

        for intent, keywords in intents.items():
            if any(kw in text_lower for kw in keywords):
                return intent

        return "help"

    async def _show_status(
        self,
        text: str,
        context: AgentContext
    ) -> Dict[str, Any]:
        """Show user status with Adaptive Card"""
        stats = await self._get_stats(context)

        card = {
            "type": "AdaptiveCard",
            "$schema": "http://adaptivecards.io/schemas/adaptive-card.json",
            "version": "1.4",
            "body": [
                {
                    "type": "TextBlock",
                    "text": "Your Status",
                    "weight": "Bolder",
                    "size": "Large"
                },
                {
                    "type": "ColumnSet",
                    "columns": [
                        {
                            "type": "Column",
                            "width": "stretch",
                            "items": [
                                {"type": "TextBlock", "text": "Active Tasks", "weight": "Bolder"},
                                {"type": "TextBlock", "text": str(stats["active"]), "size": "ExtraLarge", "color": "Accent"}
                            ]
                        },
                        {
                            "type": "Column",
                            "width": "stretch",
                            "items": [
                                {"type": "TextBlock", "text": "Completed Today", "weight": "Bolder"},
                                {"type": "TextBlock", "text": str(stats["completed"]), "size": "ExtraLarge", "color": "Good"}
                            ]
                        },
                        {
                            "type": "Column",
                            "width": "stretch",
                            "items": [
                                {"type": "TextBlock", "text": "On-time %", "weight": "Bolder"},
                                {"type": "TextBlock", "text": f"{stats['on_time']}%", "size": "ExtraLarge"}
                            ]
                        }
                    ]
                },
                {
                    "type": "TextBlock",
                    "text": "Keep up the great work!",
                    "wrap": True,
                    "spacing": "Medium"
                }
            ],
            "actions": [
                {
                    "type": "Action.Submit",
                    "title": "View Tasks",
                    "data": {"action": "view_tasks"}
                },
                {
                    "type": "Action.Submit",
                    "title": "Start Check-in",
                    "data": {"action": "checkin"}
                }
            ]
        }

        return {
            "text": f"Active: {stats['active']} | Completed: {stats['completed']}",
            "adaptive_card": card,
        }

    async def _show_tasks(
        self,
        text: str,
        context: AgentContext
    ) -> Dict[str, Any]:
        """Show tasks with Adaptive Card"""
        tasks = await self._get_tasks(context)

        task_items = []
        for task in tasks[:5]:
            priority_color = {
                "critical": "Attention",
                "high": "Warning",
                "medium": "Accent",
                "low": "Default"
            }.get(task["priority"], "Default")

            task_items.append({
                "type": "Container",
                "items": [
                    {
                        "type": "ColumnSet",
                        "columns": [
                            {
                                "type": "Column",
                                "width": "stretch",
                                "items": [
                                    {
                                        "type": "TextBlock",
                                        "text": task["title"],
                                        "weight": "Bolder",
                                        "wrap": True
                                    },
                                    {
                                        "type": "TextBlock",
                                        "text": f"{task['status']} | {task['priority'].title()} priority",
                                        "isSubtle": True,
                                        "spacing": "None"
                                    }
                                ]
                            },
                            {
                                "type": "Column",
                                "width": "auto",
                                "items": [
                                    {
                                        "type": "ActionSet",
                                        "actions": [
                                            {
                                                "type": "Action.Submit",
                                                "title": "Complete",
                                                "data": {"action": "complete", "task_id": task["id"]}
                                            }
                                        ]
                                    }
                                ]
                            }
                        ]
                    }
                ],
                "separator": True,
                "spacing": "Medium"
            })

        card = {
            "type": "AdaptiveCard",
            "$schema": "http://adaptivecards.io/schemas/adaptive-card.json",
            "version": "1.4",
            "body": [
                {
                    "type": "TextBlock",
                    "text": "Your Tasks",
                    "weight": "Bolder",
                    "size": "Large"
                },
                *task_items
            ],
            "actions": [
                {
                    "type": "Action.Submit",
                    "title": "Create New Task",
                    "data": {"action": "create_task"}
                }
            ]
        }

        return {
            "text": f"You have {len(tasks)} active tasks",
            "adaptive_card": card,
        }

    async def _start_checkin(
        self,
        text: str,
        context: AgentContext
    ) -> Dict[str, Any]:
        """Start check-in with form"""
        tasks = await self._get_tasks(context)
        current_task = tasks[0] if tasks else None

        if not current_task:
            return {"text": "No active tasks for check-in."}

        card = {
            "type": "AdaptiveCard",
            "$schema": "http://adaptivecards.io/schemas/adaptive-card.json",
            "version": "1.4",
            "body": [
                {
                    "type": "TextBlock",
                    "text": "Check-in Time!",
                    "weight": "Bolder",
                    "size": "Large"
                },
                {
                    "type": "TextBlock",
                    "text": f"Task: **{current_task['title']}**",
                    "wrap": True
                },
                {
                    "type": "Input.ChoiceSet",
                    "id": "progress",
                    "label": "How's your progress?",
                    "style": "expanded",
                    "choices": [
                        {"title": "On Track", "value": "on_track"},
                        {"title": "Slight Delay", "value": "delayed"},
                        {"title": "Blocked", "value": "blocked"},
                        {"title": "Need Help", "value": "need_help"}
                    ]
                },
                {
                    "type": "Input.Text",
                    "id": "notes",
                    "label": "Any notes or blockers?",
                    "placeholder": "Optional",
                    "isMultiline": True
                }
            ],
            "actions": [
                {
                    "type": "Action.Submit",
                    "title": "Submit Check-in",
                    "data": {
                        "action": "checkin_submit",
                        "task_id": current_task["id"]
                    }
                }
            ]
        }

        return {
            "text": f"Check-in for: {current_task['title']}",
            "adaptive_card": card,
        }

    async def _create_task(
        self,
        text: str,
        context: AgentContext
    ) -> Dict[str, Any]:
        """Show task creation form"""
        card = {
            "type": "AdaptiveCard",
            "$schema": "http://adaptivecards.io/schemas/adaptive-card.json",
            "version": "1.4",
            "body": [
                {
                    "type": "TextBlock",
                    "text": "Create New Task",
                    "weight": "Bolder",
                    "size": "Large"
                },
                {
                    "type": "Input.Text",
                    "id": "title",
                    "label": "Task Title",
                    "placeholder": "What needs to be done?",
                    "isRequired": True
                },
                {
                    "type": "Input.Text",
                    "id": "description",
                    "label": "Description",
                    "placeholder": "Add details...",
                    "isMultiline": True
                },
                {
                    "type": "Input.ChoiceSet",
                    "id": "priority",
                    "label": "Priority",
                    "value": "medium",
                    "choices": [
                        {"title": "Critical", "value": "critical"},
                        {"title": "High", "value": "high"},
                        {"title": "Medium", "value": "medium"},
                        {"title": "Low", "value": "low"}
                    ]
                },
                {
                    "type": "Input.Date",
                    "id": "due_date",
                    "label": "Due Date"
                }
            ],
            "actions": [
                {
                    "type": "Action.Submit",
                    "title": "Create Task",
                    "data": {"action": "create_task_submit"}
                }
            ]
        }

        return {
            "text": "Create a new task",
            "adaptive_card": card,
        }

    async def _show_help(
        self,
        text: str,
        context: AgentContext
    ) -> Dict[str, Any]:
        """Show help card"""
        card = {
            "type": "AdaptiveCard",
            "$schema": "http://adaptivecards.io/schemas/adaptive-card.json",
            "version": "1.4",
            "body": [
                {
                    "type": "TextBlock",
                    "text": "TaskPulse Commands",
                    "weight": "Bolder",
                    "size": "Large"
                },
                {
                    "type": "FactSet",
                    "facts": [
                        {"title": "status", "value": "View your current status"},
                        {"title": "tasks", "value": "List your active tasks"},
                        {"title": "checkin", "value": "Start a progress check-in"},
                        {"title": "create task", "value": "Create a new task"},
                        {"title": "help", "value": "Show this help message"}
                    ]
                },
                {
                    "type": "TextBlock",
                    "text": "Just mention me and type a command!",
                    "wrap": True,
                    "spacing": "Medium",
                    "isSubtle": True
                }
            ]
        }

        return {
            "text": "TaskPulse Help",
            "adaptive_card": card,
        }

    async def _default_response(
        self,
        text: str,
        context: AgentContext
    ) -> Dict[str, Any]:
        """Default response"""
        return await self._show_help(text, context)

    async def _handle_task_action(
        self,
        data: Dict[str, Any],
        context: AgentContext
    ) -> Dict[str, Any]:
        """Handle task card actions"""
        action = data.get("action")
        task_id = data.get("task_id")

        if action == "complete":
            return {
                "text": f"Task {task_id} marked as complete!",
                "status": 200
            }
        elif action == "view_tasks":
            return await self._show_tasks("", context)
        elif action == "checkin":
            return await self._start_checkin("", context)

        return {"status": 200}

    async def _handle_checkin_submit(
        self,
        data: Dict[str, Any],
        context: AgentContext
    ) -> Dict[str, Any]:
        """Handle check-in form submission"""
        task_id = data.get("task_id")
        progress = data.get("progress")
        notes = data.get("notes", "")

        messages = {
            "on_track": "Great progress! Keep it up!",
            "delayed": "Thanks for the update. Let me know if you need help.",
            "blocked": "I'll help you get unblocked. What's the blocker?",
            "need_help": "I'm here to help! What do you need?",
        }

        return {
            "text": messages.get(progress, "Check-in recorded!"),
            "status": 200,
            "checkin_data": {
                "task_id": task_id,
                "progress": progress,
                "notes": notes
            }
        }

    async def _get_stats(self, context: AgentContext) -> Dict[str, Any]:
        """Get user stats"""
        return {"active": 5, "completed": 2, "blocked": 0, "on_time": 87}

    async def _get_tasks(self, context: AgentContext) -> List[Dict[str, Any]]:
        """Get user tasks"""
        return [
            {"id": "1", "title": "API Implementation", "status": "in_progress", "priority": "high"},
            {"id": "2", "title": "Write Tests", "status": "pending", "priority": "medium"},
            {"id": "3", "title": "Update Docs", "status": "pending", "priority": "low"},
        ]

"""
Chat Agent

Main conversational interface for TaskPulse - AI Assistant.
Handles natural language queries, commands, and provides intelligent responses.
"""

import logging
import re
from typing import Any, Dict, List, Optional, Tuple

from ..base import (
    AgentCapability,
    AgentEvent,
    AgentResult,
    BaseAgent,
    EventType,
)
from ..context import AgentContext, ConversationMessage, MessageRole

logger = logging.getLogger(__name__)


class ChatAgent(BaseAgent):
    """
    Main conversational agent for in-app chat.

    Features:
    - Natural language understanding
    - Command processing
    - Context-aware responses
    - Agent orchestration for complex queries
    - Conversation memory
    """

    name = "chat_agent"
    description = "Main conversational interface for natural language interactions"
    version = "1.0.0"

    capabilities = [
        AgentCapability.CHAT,
        AgentCapability.NATURAL_LANGUAGE,
        AgentCapability.COMMAND_PROCESSING,
    ]

    handled_events = [
        EventType.USER_MESSAGE,
        EventType.USER_COMMAND,
    ]

    priority = 5  # High priority for user interactions

    # Intent patterns
    INTENT_PATTERNS = {
        "status": [
            r"how am i doing",
            r"my status",
            r"how('s| is) my progress",
            r"what('s| is) my status",
        ],
        "tasks": [
            r"my tasks",
            r"what should i work on",
            r"what('s| is) next",
            r"show.*tasks",
            r"list.*tasks",
        ],
        "create_task": [
            r"create.*task",
            r"add.*task",
            r"new task",
            r"todo:?\s*(.+)",
        ],
        "help": [
            r"i('m| am) stuck",
            r"help me",
            r"need help",
            r"can you help",
        ],
        "blocked": [
            r"i('m| am) blocked",
            r"stuck on",
            r"can('t| not) figure out",
            r"having trouble",
        ],
        "complete": [
            r"mark.*complete",
            r"finish.*task",
            r"done with",
            r"completed",
        ],
        "feedback": [
            r"how am i doing",
            r"give me feedback",
            r"my performance",
            r"how('s| is) my work",
        ],
        "greeting": [
            r"^hi$",
            r"^hello$",
            r"^hey$",
            r"good morning",
            r"good afternoon",
        ],
    }

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        super().__init__(config)
        self.max_context_messages = config.get("max_context_messages", 10) if config else 10
        self.personality = config.get("personality", "helpful") if config else "helpful"
        self._compile_patterns()

    def _compile_patterns(self):
        """Compile regex patterns for faster matching"""
        self._compiled_patterns = {}
        for intent, patterns in self.INTENT_PATTERNS.items():
            self._compiled_patterns[intent] = [
                re.compile(p, re.IGNORECASE) for p in patterns
            ]

    async def can_handle(self, event: AgentEvent) -> bool:
        """Always handle user messages"""
        return event.event_type in [EventType.USER_MESSAGE, EventType.USER_COMMAND]

    async def execute(self, context: AgentContext) -> AgentResult:
        """Process user message and generate response"""
        result = AgentResult(
            success=True,
            agent_name=self.name,
            event_id=context.event.id if context.event else "direct"
        )

        try:
            # Get user message
            message = self._get_user_message(context)
            if not message:
                result.message = "I didn't receive a message. How can I help you?"
                return result

            # Detect intent
            intent, entities = await self._detect_intent(message, context)

            # Route to appropriate handler
            response = await self._route_intent(intent, entities, context)

            result.output = {
                "intent": intent,
                "entities": entities,
                "response": response,
            }

            result.message = response.get("text", "I'm here to help!")

            # Add response to conversation
            context.add_message(
                result.message,
                role=MessageRole.AGENT,
                agent_name=self.name,
                metadata={
                    "intent": intent,
                    "actions": response.get("actions", []),
                }
            )

            result.actions = response.get("actions", [])

            # Check if we need to chain to other agents
            if response.get("chain_to"):
                for agent_name in response["chain_to"]:
                    result.follow_up_events.append(
                        AgentEvent(
                            event_type=EventType.AGENT_CHAIN,
                            target_agent=agent_name,
                            payload={"context": context.to_dict()},
                        )
                    )

        except Exception as e:
            logger.error(f"Chat agent error: {e}")
            result.success = False
            result.error = str(e)
            result.message = "I encountered an issue. Let me try to help differently."

        return result

    def _get_user_message(self, context: AgentContext) -> Optional[str]:
        """Extract user message from context"""
        # From event payload
        if context.event and context.event.payload:
            message = context.event.payload.get("message")
            if message:
                return message

        # From conversation history
        last_msg = context.get_last_message()
        if last_msg and last_msg.role == MessageRole.USER:
            return last_msg.content

        return None

    async def _detect_intent(
        self,
        message: str,
        context: AgentContext
    ) -> Tuple[str, Dict[str, Any]]:
        """Detect user intent from message"""
        message_lower = message.lower().strip()
        entities = {}

        # Check against patterns
        for intent, patterns in self._compiled_patterns.items():
            for pattern in patterns:
                match = pattern.search(message_lower)
                if match:
                    # Extract any captured groups as entities
                    if match.groups():
                        entities["extracted"] = match.group(1) if match.lastindex else None
                    return intent, entities

        # Check for task references
        task_match = re.search(r"task[#\s]+(\d+|[\w-]+)", message_lower)
        if task_match:
            entities["task_ref"] = task_match.group(1)

        # Default to general query
        return "general", entities

    async def _route_intent(
        self,
        intent: str,
        entities: Dict[str, Any],
        context: AgentContext
    ) -> Dict[str, Any]:
        """Route to appropriate handler based on intent"""
        handlers = {
            "greeting": self._handle_greeting,
            "status": self._handle_status,
            "tasks": self._handle_tasks,
            "create_task": self._handle_create_task,
            "help": self._handle_help,
            "blocked": self._handle_blocked,
            "complete": self._handle_complete,
            "feedback": self._handle_feedback,
            "general": self._handle_general,
        }

        handler = handlers.get(intent, self._handle_general)
        return await handler(entities, context)

    async def _handle_greeting(
        self,
        entities: Dict[str, Any],
        context: AgentContext
    ) -> Dict[str, Any]:
        """Handle greeting messages"""
        user_name = context.user.full_name if context.user else "there"
        first_name = user_name.split()[0] if user_name else "there"

        greetings = [
            f"Hi {first_name}! How can I help you today?",
            f"Hello {first_name}! Ready to be productive?",
            f"Hey {first_name}! What would you like to work on?",
        ]

        import random
        return {
            "text": random.choice(greetings),
            "actions": [{"type": "greeting"}],
            "suggestions": [
                "Show my tasks",
                "What should I work on?",
                "How am I doing?",
            ],
        }

    async def _handle_status(
        self,
        entities: Dict[str, Any],
        context: AgentContext
    ) -> Dict[str, Any]:
        """Handle status queries"""
        # In production, query actual task data
        stats = await self._get_user_stats(context)

        text = f"""Here's your current status:

**Tasks**
- Active: {stats['active_tasks']}
- Completed today: {stats['completed_today']}
- Blocked: {stats['blocked_tasks']}

**This Week**
- On-time delivery: {stats['on_time_percent']}%
- Hours logged: {stats['hours_logged']}h

Keep up the great work!"""

        return {
            "text": text,
            "actions": [{"type": "status_displayed"}],
            "data": stats,
        }

    async def _handle_tasks(
        self,
        entities: Dict[str, Any],
        context: AgentContext
    ) -> Dict[str, Any]:
        """Handle task list queries"""
        tasks = await self._get_user_tasks(context)

        if not tasks:
            return {
                "text": "You don't have any active tasks. Would you like to create one?",
                "actions": [],
                "suggestions": ["Create a task"],
            }

        task_list = "\n".join([
            f"• **{t['title']}** - {t['status']} (Priority: {t['priority']})"
            for t in tasks[:5]
        ])

        text = f"""Here are your active tasks:

{task_list}

What would you like to work on?"""

        return {
            "text": text,
            "actions": [{"type": "tasks_listed", "count": len(tasks)}],
            "data": {"tasks": tasks},
        }

    async def _handle_create_task(
        self,
        entities: Dict[str, Any],
        context: AgentContext
    ) -> Dict[str, Any]:
        """Handle task creation requests"""
        extracted = entities.get("extracted")

        if extracted:
            # User provided task title inline
            return {
                "text": f"I'll create a task: **{extracted}**\n\nWould you like to add more details like priority or due date?",
                "actions": [
                    {"type": "task_draft", "title": extracted}
                ],
                "pending_action": "confirm_task_creation",
                "suggestions": ["Set priority high", "Due tomorrow", "Just create it"],
            }

        return {
            "text": "What would you like to call this task?",
            "actions": [],
            "pending_action": "await_task_title",
        }

    async def _handle_help(
        self,
        entities: Dict[str, Any],
        context: AgentContext
    ) -> Dict[str, Any]:
        """Handle help requests - chain to unblock agent"""
        return {
            "text": "I'd be happy to help! Can you tell me more about what you're working on and where you're stuck?",
            "actions": [{"type": "help_initiated"}],
            "chain_to": ["unblock_agent"],
        }

    async def _handle_blocked(
        self,
        entities: Dict[str, Any],
        context: AgentContext
    ) -> Dict[str, Any]:
        """Handle blocked/stuck messages - chain to unblock agent"""
        return {
            "text": "I understand you're facing a blocker. Let me help you work through this.\n\nCan you describe what's blocking you?",
            "actions": [{"type": "blocker_detected"}],
            "chain_to": ["unblock_agent"],
        }

    async def _handle_complete(
        self,
        entities: Dict[str, Any],
        context: AgentContext
    ) -> Dict[str, Any]:
        """Handle task completion requests"""
        task_ref = entities.get("task_ref")

        if task_ref:
            return {
                "text": f"Marking task #{task_ref} as complete. Great job!",
                "actions": [{"type": "task_completed", "task_ref": task_ref}],
            }

        # Ask which task to complete
        tasks = await self._get_user_tasks(context)
        if tasks:
            task_list = "\n".join([
                f"{i+1}. {t['title']}"
                for i, t in enumerate(tasks[:5])
            ])
            return {
                "text": f"Which task would you like to mark as complete?\n\n{task_list}",
                "actions": [],
                "pending_action": "select_task_to_complete",
            }

        return {
            "text": "You don't have any active tasks to complete.",
            "actions": [],
        }

    async def _handle_feedback(
        self,
        entities: Dict[str, Any],
        context: AgentContext
    ) -> Dict[str, Any]:
        """Handle feedback requests - chain to coach agent"""
        return {
            "text": "Let me analyze your recent performance and provide some feedback...",
            "actions": [{"type": "feedback_requested"}],
            "chain_to": ["coach_agent"],
        }

    async def _handle_general(
        self,
        entities: Dict[str, Any],
        context: AgentContext
    ) -> Dict[str, Any]:
        """Handle general queries"""
        message = self._get_user_message(context) or ""

        # Try to provide helpful response based on context
        return {
            "text": self._generate_general_response(message, context),
            "actions": [{"type": "general_response"}],
            "suggestions": [
                "Show my tasks",
                "I need help",
                "What should I work on?",
            ],
        }

    def _generate_general_response(
        self,
        message: str,
        context: AgentContext
    ) -> str:
        """Generate response for general queries"""
        # Simple response generation
        return f"""I'm not sure I understood that. Here's what I can help you with:

- **"my tasks"** - View your active tasks
- **"what should I work on"** - Get recommendations
- **"I'm stuck"** - Get help with blockers
- **"how am I doing"** - See your performance
- **"create task: [title]"** - Create a new task

What would you like to do?"""

    async def _get_user_stats(self, context: AgentContext) -> Dict[str, Any]:
        """Get user statistics"""
        # Mock data - in production, query database
        return {
            "active_tasks": 5,
            "completed_today": 2,
            "blocked_tasks": 0,
            "on_time_percent": 87,
            "hours_logged": 6.5,
        }

    async def _get_user_tasks(self, context: AgentContext) -> List[Dict[str, Any]]:
        """Get user's tasks"""
        # Mock data
        return [
            {"id": "1", "title": "Implement API endpoint", "status": "in_progress", "priority": "high"},
            {"id": "2", "title": "Write unit tests", "status": "pending", "priority": "medium"},
            {"id": "3", "title": "Update documentation", "status": "pending", "priority": "low"},
        ]

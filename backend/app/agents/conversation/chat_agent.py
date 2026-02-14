"""
Chat Agent

Main conversational interface for TaskPulse - AI Assistant.
Handles natural language queries, commands, and provides intelligent responses.
Supports smart task creation, check-in responses, and blocker resolution.
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
    - Natural language understanding with AI fallback
    - Smart task creation from natural language (with decomposition + check-in scheduling)
    - Check-in response handling via chat
    - Blocker/error detection and AI-powered solutions
    - Real database queries (no mocks)
    """

    name = "chat_agent"
    description = "Main conversational interface for natural language interactions"
    version = "2.0.0"

    capabilities = [
        AgentCapability.CHAT,
        AgentCapability.NATURAL_LANGUAGE,
        AgentCapability.COMMAND_PROCESSING,
    ]

    handled_events = [
        EventType.USER_MESSAGE,
        EventType.USER_COMMAND,
    ]

    priority = 5

    # Intent patterns — ordered by specificity (most specific first)
    INTENT_PATTERNS = {
        "smart_create_task": [
            r"i need to (?:build|create|develop|implement|design|write|make|finish|complete|do|work on)\s+(.+?)(?:\s+by\s+|\s+before\s+|\s+deadline\s+)(.+)",
            r"(?:build|create|develop|implement|make|write|design)\s+(.+?)(?:\s+by\s+|\s+before\s+)(.+)",
            r"i(?:'m| am) working on\s+(.+?)(?:\s+deadline|\s+due|\s+by\s+)(.+)",
            r"i need to (?:build|create|develop|implement|design|write|make|finish|complete|do|work on)\s+(.+)",
            r"(?:create|set up|make)\s+(?:a )?task (?:for|about|based on)\s+(.+)",
            r"\[Attached file:",
            r"create a task based on this document",
        ],
        "checkin_response": [
            r"(?:i(?:'m| am)) on track",
            r"(?:i(?:'m| am)) (\d+)%\s*(?:done|complete|through|finished)?",
            r"things are going (?:well|great|fine|okay|good)",
            r"making (?:good )?progress",
            r"(?:i(?:'m| am)) (?:slightly |significantly )?behind",
            r"completed (?:it|the task|this)",
            r"(?:i(?:'ve| have)) (?:finished|completed|done)",
        ],
        "blocker_help": [
            r"(?:getting|got|have|seeing) (?:an? |this )?error",
            r"error:?\s+(.+)",
            r"exception:?\s+(.+)",
            r"can(?:'t| ?not) (?:get|figure|proceed|continue)",
            r"failing with",
            r"doesn(?:'t| not) work",
            r"(?:it(?:'s| is)|this is) broken",
        ],
        "status": [
            r"how am i doing",
            r"my status",
            r"how(?:'s| is) my progress",
            r"what(?:'s| is) my status",
        ],
        "tasks": [
            r"my tasks",
            r"what should i work on",
            r"what(?:'s| is) next",
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
            r"i(?:'m| am) stuck",
            r"help me",
            r"need help",
            r"can you help",
        ],
        "blocked": [
            r"i(?:'m| am) blocked",
            r"stuck on",
            r"can(?:'t| not) figure out",
            r"having trouble",
        ],
        "complete": [
            r"mark.*complete",
            r"finish.*task",
            r"done with",
        ],
        "feedback": [
            r"give me feedback",
            r"my performance",
            r"how(?:'s| is) my work",
        ],
        "greeting": [
            r"^hi$",
            r"^hello$",
            r"^hey$",
            r"good morning",
            r"good afternoon",
        ],
    }

    # Multi-turn conversation state for task creation
    # Key: conversation_id, Value: dict with partial task data
    _pending_tasks: Dict[str, Dict[str, Any]] = {}

    @classmethod
    def _get_pending_task(cls, conversation_id: Optional[str]) -> Optional[Dict[str, Any]]:
        if not conversation_id:
            return None
        return cls._pending_tasks.get(conversation_id)

    @classmethod
    def _set_pending_task(cls, conversation_id: str, data: Dict[str, Any]):
        cls._pending_tasks[conversation_id] = data

    @classmethod
    def _clear_pending_task(cls, conversation_id: str):
        cls._pending_tasks.pop(conversation_id, None)

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
        return event.event_type in [EventType.USER_MESSAGE, EventType.USER_COMMAND]

    async def execute(self, context: AgentContext) -> AgentResult:
        """Process user message and generate response"""
        result = AgentResult(
            success=True,
            agent_name=self.name,
            event_id=context.event.id if context.event else "direct"
        )

        try:
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
                "suggestions": response.get("suggestions", []),
            }

            result.message = response.get("text", "I'm here to help!")

            # Add response to conversation
            context.add_message(
                result.message,
                role=MessageRole.AGENT,
                agent_name=self.name,
                metadata={"intent": intent, "actions": response.get("actions", [])},
            )

            result.actions = response.get("actions", [])

            # Chain to other agents if needed
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
            logger.error(f"Chat agent error: {e}", exc_info=True)
            result.success = False
            result.error = str(e)
            result.message = "I encountered an issue processing your request. Could you try rephrasing?"

        return result

    def _get_user_message(self, context: AgentContext) -> Optional[str]:
        if context.event and context.event.payload:
            message = context.event.payload.get("message")
            if message:
                return message
        last_msg = context.get_last_message()
        if last_msg and last_msg.role == MessageRole.USER:
            return last_msg.content
        return None

    async def _detect_intent(
        self,
        message: str,
        context: AgentContext
    ) -> Tuple[str, Dict[str, Any]]:
        """Detect user intent — pending task first, then regex, then AI fallback."""
        message_lower = message.lower().strip()
        entities = {"raw_message": message}

        # Check if there's a pending task creation that needs a follow-up answer
        conversation_id = context.conversation_id
        pending = self._get_pending_task(conversation_id)
        if pending and pending.get("awaiting_field"):
            entities["pending_task"] = pending
            return "task_creation_followup", entities

        # Check against regex patterns
        for intent, patterns in self._compiled_patterns.items():
            for pattern in patterns:
                match = pattern.search(message_lower)
                if match:
                    if match.groups():
                        entities["extracted"] = match.group(1) if match.lastindex else None
                        if match.lastindex and match.lastindex > 1:
                            entities["extracted_2"] = match.group(2)
                    return intent, entities

        # Check for task references
        task_match = re.search(r"task[#\s]+(\d+|[\w-]+)", message_lower)
        if task_match:
            entities["task_ref"] = task_match.group(1)

        # AI fallback for longer/complex messages
        if len(message.split()) > 8:
            ai_intent = await self._ai_classify_intent(message, context)
            if ai_intent and ai_intent != "general":
                return ai_intent, entities

        return "general", entities

    async def _ai_classify_intent(
        self,
        message: str,
        context: AgentContext
    ) -> Optional[str]:
        """Use AI to classify intent for complex messages."""
        try:
            from app.services.ai_service import get_ai_service
            ai_service = get_ai_service()

            system_prompt = """Classify the user's message into exactly one category.
Return ONLY one of these words: smart_create_task, checkin_response, blocker_help, status, tasks, create_task, help, general

- smart_create_task: user wants to create a task with details like deadline, description, office hours
- checkin_response: user is reporting progress on their current work
- blocker_help: user is reporting an error, bug, or technical problem they need help with
- status: user wants to see their overall status/progress
- tasks: user wants to see their task list
- create_task: user wants to create a simple task (no deadline/details)
- help: user needs general help
- general: anything else

Return ONLY the category name, nothing else."""

            response = await ai_service.generate(
                prompt=message,
                system_prompt=system_prompt,
                temperature=0.1,
                max_tokens=20,
                use_cache=True,
            )
            intent = response.content.strip().lower().replace('"', '').replace("'", "")
            valid_intents = [
                "smart_create_task", "checkin_response", "blocker_help",
                "status", "tasks", "create_task", "help", "general",
            ]
            if intent in valid_intents:
                return intent
        except Exception as e:
            logger.debug(f"AI intent classification failed: {e}")

        return None

    async def _route_intent(
        self,
        intent: str,
        entities: Dict[str, Any],
        context: AgentContext
    ) -> Dict[str, Any]:
        handlers = {
            "greeting": self._handle_greeting,
            "status": self._handle_status,
            "tasks": self._handle_tasks,
            "create_task": self._handle_create_task,
            "smart_create_task": self._handle_smart_create_task,
            "task_creation_followup": self._handle_task_creation_followup,
            "help": self._handle_help,
            "blocked": self._handle_blocked,
            "blocker_help": self._handle_blocker_help,
            "checkin_response": self._handle_checkin_response,
            "complete": self._handle_complete,
            "feedback": self._handle_feedback,
            "general": self._handle_general,
        }
        handler = handlers.get(intent, self._handle_general)
        return await handler(entities, context)

    # ==================== Core New Handlers ====================

    def _get_next_missing_field(
        self,
        parsed: Dict[str, Any],
        already_asked: List[str],
    ) -> Optional[Dict[str, Any]]:
        """Determine what info is still needed for task creation."""
        questions = [
            {
                "field": "deadline",
                "check": lambda p: p.get("deadline") is not None,
                "question": "What's the deadline for this task?",
                "suggestions": ["By end of this week", "In 2 weeks", "By end of month", "No specific deadline"],
            },
            {
                "field": "office_hours",
                "check": lambda p: p.get("work_start_hour") not in (None, 9) or p.get("work_end_hour") not in (None, 18),
                "question": "What are your working hours? (e.g., 9am to 6pm)",
                "suggestions": ["9am to 5pm", "10am to 7pm", "9am to 6pm", "Flexible hours"],
            },
            {
                "field": "priority",
                "check": lambda p: p.get("priority") not in (None, "medium"),
                "question": "What priority level would you like?",
                "suggestions": ["Low", "Medium", "High", "Critical"],
            },
        ]

        for q in questions:
            if q["field"] not in already_asked and not q["check"](parsed):
                return q

        return None

    async def _finalize_task_creation(
        self,
        pending: Dict[str, Any],
        context: AgentContext,
    ) -> Dict[str, Any]:
        """Create the task after all info is gathered via conversation."""
        conversation_id = context.conversation_id
        parsed = pending["parsed"]

        user_id = context.user.id if context.user else None
        org_id = context.organization.id if context.organization else None

        if not context.db or not user_id or not org_id:
            if conversation_id:
                self._clear_pending_task(conversation_id)
            return {
                "text": "I couldn't create the task due to a session issue. Please try again.",
                "actions": [],
            }

        try:
            from app.services.smart_task_service import SmartTaskService
            smart_service = SmartTaskService(context.db)
            result = await smart_service.create_smart_task(
                parsed_task=parsed,
                org_id=org_id,
                user_id=user_id,
            )
            await context.db.commit()

            if conversation_id:
                self._clear_pending_task(conversation_id)

            task = result["task"]
            summary = result["summary"]

            return {
                "text": summary,
                "actions": [
                    {"type": "task_created", "task_id": task.id, "title": task.title},
                ],
                "suggestions": [
                    "Show my tasks",
                    "What should I work on next?",
                    "Change the deadline",
                ],
            }
        except Exception as e:
            logger.error(f"Task creation failed: {e}", exc_info=True)
            if conversation_id:
                self._clear_pending_task(conversation_id)
            return {
                "text": f"I had trouble creating the task. Could you try again? ({str(e)[:100]})",
                "actions": [],
                "suggestions": ["Create a task", "Show my tasks"],
            }

    async def _handle_task_creation_followup(
        self,
        entities: Dict[str, Any],
        context: AgentContext,
    ) -> Dict[str, Any]:
        """Handle user response to a task creation follow-up question."""
        message = entities.get("raw_message", "")
        pending = entities.get("pending_task", {})
        awaiting = pending.get("awaiting_field")
        conversation_id = context.conversation_id

        # Update the pending task with the user's response
        if awaiting == "deadline":
            if any(w in message.lower() for w in ["no specific", "no deadline", "none", "flexible", "no"]):
                pending["parsed"]["deadline"] = None
                pending.setdefault("asked_fields", [])  # mark as asked so we skip it
            else:
                try:
                    from dateutil import parser as date_parser
                    from datetime import datetime
                    parsed_date = date_parser.parse(message, fuzzy=True, default=datetime.now())
                    pending["parsed"]["deadline"] = parsed_date.isoformat()
                except Exception:
                    pending["parsed"]["deadline"] = message

        elif awaiting == "office_hours":
            if any(w in message.lower() for w in ["flexible", "default", "normal"]):
                pending["parsed"]["work_start_hour"] = 9
                pending["parsed"]["work_end_hour"] = 18
            else:
                hours_match = re.search(
                    r"(\d{1,2})\s*(?:am|AM|:00)?\s*(?:to|-)\s*(\d{1,2})\s*(?:pm|PM|:00)?",
                    message,
                )
                if hours_match:
                    start_h = int(hours_match.group(1))
                    end_h = int(hours_match.group(2))
                    if end_h <= start_h and end_h < 12:
                        end_h += 12
                    pending["parsed"]["work_start_hour"] = start_h
                    pending["parsed"]["work_end_hour"] = end_h
                else:
                    pending["parsed"]["work_start_hour"] = 9
                    pending["parsed"]["work_end_hour"] = 18

        elif awaiting == "priority":
            msg_lower = message.lower()
            if any(w in msg_lower for w in ["critical", "urgent"]):
                pending["parsed"]["priority"] = "critical"
            elif "high" in msg_lower:
                pending["parsed"]["priority"] = "high"
            elif "low" in msg_lower:
                pending["parsed"]["priority"] = "low"
            else:
                pending["parsed"]["priority"] = "medium"

        # Check what's still missing
        parsed = pending["parsed"]
        next_question = self._get_next_missing_field(parsed, pending.get("asked_fields", []))

        if next_question:
            pending["awaiting_field"] = next_question["field"]
            pending.setdefault("asked_fields", []).append(next_question["field"])
            if conversation_id:
                self._set_pending_task(conversation_id, pending)
            return {
                "text": next_question["question"],
                "actions": [],
                "suggestions": next_question.get("suggestions", []),
            }

        # All info gathered — create the task
        return await self._finalize_task_creation(pending, context)

    async def _handle_smart_create_task(
        self,
        entities: Dict[str, Any],
        context: AgentContext
    ) -> Dict[str, Any]:
        """Handle natural-language task creation with conversational follow-ups."""
        message = entities.get("raw_message", "")

        if not context.db:
            return {
                "text": "I'd love to create that task, but I don't have database access right now. Please try creating it from the Tasks page.",
                "actions": [],
                "suggestions": ["Show my tasks"],
            }

        user_id = context.user.id if context.user else None
        org_id = context.organization.id if context.organization else None

        if not user_id or not org_id:
            return {
                "text": "I couldn't identify your account. Please try again.",
                "actions": [],
            }

        try:
            from app.services.smart_task_service import SmartTaskService
            smart_service = SmartTaskService(context.db)

            # Step 1: AI parses natural language into structured data
            parsed = await smart_service.parse_natural_language_task(message)

            # Step 2: Check if we have all required info
            next_question = self._get_next_missing_field(parsed, [])
            conversation_id = context.conversation_id

            if next_question and conversation_id:
                # Store partial state and ask follow-up
                self._set_pending_task(conversation_id, {
                    "parsed": parsed,
                    "awaiting_field": next_question["field"],
                    "asked_fields": [next_question["field"]],
                    "original_message": message,
                })

                ack = f"Got it! I'll help you set up a task for: **{parsed.get('title', 'your task')}**\n\n"
                return {
                    "text": ack + next_question["question"],
                    "actions": [],
                    "suggestions": next_question.get("suggestions", []),
                }

            # All info present — create immediately (backwards compatible)
            result = await smart_service.create_smart_task(
                parsed_task=parsed,
                org_id=org_id,
                user_id=user_id,
            )
            await context.db.commit()

            return {
                "text": result["summary"],
                "actions": [
                    {"type": "task_created", "task_id": result["task"].id, "title": result["task"].title},
                ],
                "suggestions": [
                    "Show my tasks",
                    "What should I work on next?",
                    "Change the deadline",
                ],
            }

        except Exception as e:
            logger.error(f"Smart task creation failed: {e}", exc_info=True)
            return {
                "text": f"I had trouble creating that task. Could you try rephrasing? ({str(e)[:100]})",
                "actions": [],
                "suggestions": ["Create a task", "Show my tasks"],
            }

    async def _handle_checkin_response(
        self,
        entities: Dict[str, Any],
        context: AgentContext
    ) -> Dict[str, Any]:
        """Handle when user responds to a check-in via chat."""
        message = entities.get("raw_message", "")
        user_id = context.user.id if context.user else None
        org_id = context.organization.id if context.organization else None

        if not context.db or not user_id or not org_id:
            return {
                "text": "Thanks for the update! I've noted your progress.",
                "actions": [{"type": "checkin_acknowledged"}],
            }

        try:
            from app.services.checkin_service import CheckInService
            from app.schemas.checkin import CheckInSubmit
            from app.models.checkin import ProgressIndicator

            checkin_service = CheckInService(context.db)
            pending = await checkin_service.get_pending_checkins_for_user(user_id, org_id)

            if not pending:
                return {
                    "text": "Thanks for the update! You don't have any pending check-ins right now, but I've noted your progress.",
                    "actions": [{"type": "checkin_no_pending"}],
                    "suggestions": ["Show my tasks", "I need help"],
                }

            # Use the most recent pending check-in
            checkin = pending[0]
            task_title = checkin.task.title if checkin.task else "your task"

            # Classify the progress from the message
            progress = await self._classify_progress(message)

            # Check if blocker detected
            is_blocked = progress == "blocked"
            blockers_text = message if is_blocked else None

            response_data = CheckInSubmit(
                progress_indicator=self._map_progress_indicator(progress),
                progress_notes=message,
                blockers_reported=blockers_text,
                help_needed=is_blocked,
            )

            await checkin_service.respond_to_checkin(
                checkin_id=checkin.id,
                org_id=org_id,
                user_id=user_id,
                response=response_data,
            )
            await context.db.commit()

            # If blocked, also get AI help
            if is_blocked:
                blocker_result = await self._handle_blocker_help(
                    {**entities, "task_id": checkin.task_id, "task_title": task_title},
                    context,
                )
                return {
                    "text": f"Check-in recorded for **{task_title}**. I see you're blocked.\n\n{blocker_result['text']}",
                    "actions": [
                        {"type": "checkin_responded", "checkin_id": checkin.id},
                        *blocker_result.get("actions", []),
                    ],
                    "suggestions": blocker_result.get("suggestions", []),
                }

            progress_labels = {
                "on_track": "on track",
                "ahead": "ahead of schedule",
                "slightly_behind": "slightly behind",
                "significantly_behind": "significantly behind",
                "completed": "completed",
            }
            progress_label = progress_labels.get(progress, "making progress")

            return {
                "text": f"Check-in recorded for **{task_title}**. You're {progress_label} — keep it up!",
                "actions": [{"type": "checkin_responded", "checkin_id": checkin.id}],
                "suggestions": ["Show my tasks", "I need help", "What should I work on?"],
            }

        except Exception as e:
            logger.error(f"Check-in response failed: {e}", exc_info=True)
            return {
                "text": "Thanks for the update! I had trouble recording the check-in, but I've noted your progress.",
                "actions": [],
            }

    async def _handle_blocker_help(
        self,
        entities: Dict[str, Any],
        context: AgentContext
    ) -> Dict[str, Any]:
        """Handle when user reports an error/blocker — AI provides solution."""
        message = entities.get("raw_message", "")
        user_id = context.user.id if context.user else None
        org_id = context.organization.id if context.organization else None

        if not context.db or not user_id or not org_id:
            return await self._generate_blocker_help_fallback(message, context)

        try:
            # Find the user's current active task
            task_id = entities.get("task_id")
            task_title = entities.get("task_title", "")
            task_description = ""

            if not task_id:
                # Query user's in-progress tasks
                from sqlalchemy import select
                from app.models.task import Task, TaskStatus

                result = await context.db.execute(
                    select(Task).where(
                        Task.assigned_to == user_id,
                        Task.org_id == org_id,
                        Task.status.in_([TaskStatus.IN_PROGRESS, TaskStatus.BLOCKED]),
                    ).order_by(Task.updated_at.desc()).limit(1)
                )
                task = result.scalar_one_or_none()
                if task:
                    task_id = task.id
                    task_title = task.title
                    task_description = task.description or ""

            if not task_id:
                return await self._generate_blocker_help_fallback(message, context)

            # Get AI unblock suggestion
            from app.services.ai_service import get_ai_service
            ai_service = get_ai_service()

            blocker_desc = message
            suggestion_result = await ai_service.get_unblock_suggestion(
                task_title=task_title,
                task_description=task_description,
                blocker_type="tool",
                blocker_description=blocker_desc,
                user_skill_level=context.user.skill_level if context.user else "intermediate",
            )

            suggestion_text = suggestion_result.get("suggestion", "")
            confidence = suggestion_result.get("confidence", 0)

            # Post as AI comment on the task
            if suggestion_text:
                from app.services.task_service import TaskService
                from app.schemas.task import CommentCreate

                task_service = TaskService(context.db)
                comment_content = f"**AI Solution** (confidence: {int(confidence*100)}%)\n\n{suggestion_text}"
                try:
                    await task_service.add_comment(
                        task_id=task_id,
                        org_id=org_id,
                        comment_data=CommentCreate(content=comment_content),
                        user_id=user_id,
                        is_ai_generated=True,
                    )
                    await context.db.commit()
                except Exception as e:
                    logger.warning(f"Failed to post AI comment: {e}")

            response_text = f"I analyzed your issue on **{task_title}**. Here's what I suggest:\n\n{suggestion_text}"

            if suggestion_result.get("escalation_recommended"):
                response_text += "\n\n*I'd also recommend discussing this with your team lead for additional guidance.*"

            response_text += "\n\nI've posted this solution as a comment on the task."

            return {
                "text": response_text,
                "actions": [
                    {"type": "blocker_resolved", "task_id": task_id, "confidence": confidence},
                ],
                "suggestions": [
                    "That worked, thanks!",
                    "I'm still stuck",
                    "Show my tasks",
                ],
            }

        except Exception as e:
            logger.error(f"Blocker help failed: {e}", exc_info=True)
            return await self._generate_blocker_help_fallback(message, context)

    # ==================== Existing Handlers (upgraded) ====================

    async def _handle_greeting(
        self,
        entities: Dict[str, Any],
        context: AgentContext
    ) -> Dict[str, Any]:
        user_name = context.user.full_name if context.user else "there"
        first_name = user_name.split()[0] if user_name else "there"

        import random
        greetings = [
            f"Hi {first_name}! How can I help you today?",
            f"Hello {first_name}! Ready to be productive?",
            f"Hey {first_name}! What would you like to work on?",
        ]
        return {
            "text": random.choice(greetings),
            "actions": [{"type": "greeting"}],
            "suggestions": ["Show my tasks", "What should I work on?", "How am I doing?"],
        }

    async def _handle_status(
        self,
        entities: Dict[str, Any],
        context: AgentContext
    ) -> Dict[str, Any]:
        stats = await self._get_user_stats(context)

        text = f"""Here's your current status:

**Tasks**
- Active: {stats['active_tasks']}
- Completed today: {stats['completed_today']}
- Blocked: {stats['blocked_tasks']}

**Overview**
- In progress: {stats['in_progress']}
- In review: {stats['in_review']}
- To do: {stats['todo']}

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
        tasks = await self._get_user_tasks(context)

        if not tasks:
            return {
                "text": "You don't have any active tasks. Would you like to create one?",
                "actions": [],
                "suggestions": ["Create a task"],
            }

        task_list = "\n".join([
            f"- **{t['title']}** — {t['status']} (Priority: {t['priority']})"
            for t in tasks[:8]
        ])

        text = f"""Here are your active tasks:

{task_list}

What would you like to work on?"""

        return {
            "text": text,
            "actions": [{"type": "tasks_listed", "count": len(tasks)}],
            "data": {"tasks": tasks},
            "suggestions": ["What should I work on?", "I need help with a task"],
        }

    async def _handle_create_task(
        self,
        entities: Dict[str, Any],
        context: AgentContext
    ) -> Dict[str, Any]:
        extracted = entities.get("extracted")

        if extracted and context.db and context.user and context.organization:
            # Actually create the task
            try:
                from app.services.task_service import TaskService
                from app.schemas.task import TaskCreate

                task_service = TaskService(context.db)
                task = await task_service.create_task(
                    TaskCreate(title=extracted),
                    context.organization.id,
                    context.user.id,
                )
                await context.db.commit()

                return {
                    "text": f"Task created: **{extracted}**\n\nWould you like to add a deadline, priority, or break it into subtasks?",
                    "actions": [{"type": "task_created", "task_id": task.id, "title": extracted}],
                    "suggestions": ["Set priority high", "Add a deadline", "Break into subtasks"],
                }
            except Exception as e:
                logger.warning(f"Task creation failed: {e}")

        if extracted:
            return {
                "text": f"I'll create a task: **{extracted}**\n\nWould you like to add more details like priority or due date?",
                "actions": [{"type": "task_draft", "title": extracted}],
                "suggestions": ["Set priority high", "Due tomorrow", "Just create it"],
            }

        return {
            "text": "What would you like to call this task? You can also say something like:\n\n*\"I need to build a payment API by Feb 15th, I work 10am-7pm\"*\n\nand I'll set up everything automatically!",
            "actions": [],
            "suggestions": ["Show my tasks"],
        }

    async def _handle_help(
        self,
        entities: Dict[str, Any],
        context: AgentContext
    ) -> Dict[str, Any]:
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
        return {
            "text": "I understand you're facing a blocker. Let me help you work through this.\n\nCan you describe what's blocking you? Include any error messages if you have them.",
            "actions": [{"type": "blocker_detected"}],
            "suggestions": ["I'm getting an error", "I don't know how to proceed", "I need a different approach"],
        }

    async def _handle_complete(
        self,
        entities: Dict[str, Any],
        context: AgentContext
    ) -> Dict[str, Any]:
        task_ref = entities.get("task_ref")

        if task_ref:
            return {
                "text": f"Marking task #{task_ref} as complete. Great job!",
                "actions": [{"type": "task_completed", "task_ref": task_ref}],
            }

        tasks = await self._get_user_tasks(context)
        if tasks:
            task_list = "\n".join([
                f"{i+1}. {t['title']}"
                for i, t in enumerate(tasks[:5])
            ])
            return {
                "text": f"Which task would you like to mark as complete?\n\n{task_list}",
                "actions": [],
            }

        return {"text": "You don't have any active tasks to complete.", "actions": []}

    async def _handle_feedback(
        self,
        entities: Dict[str, Any],
        context: AgentContext
    ) -> Dict[str, Any]:
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
        message = self._get_user_message(context) or ""
        ai_response = await self._generate_ai_response(message, context)

        return {
            "text": ai_response,
            "actions": [{"type": "general_response"}],
            "suggestions": ["Show my tasks", "I need help", "What should I work on?"],
        }

    # ==================== Helper Methods ====================

    async def _classify_progress(self, message: str) -> str:
        """Classify a check-in response into a progress category."""
        msg_lower = message.lower()

        if any(w in msg_lower for w in ["completed", "finished", "done", "100%"]):
            return "completed"
        if any(w in msg_lower for w in ["blocked", "stuck", "error", "can't", "cannot", "failing"]):
            return "blocked"
        if any(w in msg_lower for w in ["significantly behind", "very behind", "way behind"]):
            return "significantly_behind"
        if any(w in msg_lower for w in ["behind", "delayed", "slow"]):
            return "slightly_behind"
        if any(w in msg_lower for w in ["ahead", "faster", "early"]):
            return "ahead"

        return "on_track"

    def _map_progress_indicator(self, progress: str):
        """Map progress string to ProgressIndicator enum."""
        from app.models.checkin import ProgressIndicator

        mapping = {
            "on_track": ProgressIndicator.ON_TRACK,
            "ahead": ProgressIndicator.AHEAD,
            "slightly_behind": ProgressIndicator.SLIGHTLY_BEHIND,
            "significantly_behind": ProgressIndicator.SIGNIFICANTLY_BEHIND,
            "blocked": ProgressIndicator.BLOCKED,
            "completed": ProgressIndicator.COMPLETED,
        }
        return mapping.get(progress, ProgressIndicator.ON_TRACK)

    async def _generate_blocker_help_fallback(
        self,
        message: str,
        context: AgentContext
    ) -> Dict[str, Any]:
        """Fallback when we can't find the task — use AI directly."""
        try:
            ai_response = await self._generate_ai_response(
                f"The user is stuck and needs help. Their message: {message}\n\nProvide helpful troubleshooting advice.",
                context,
            )
        except Exception:
            ai_response = "I understand you're facing an issue. Could you describe the error or problem in more detail? I can help you troubleshoot."
        return {
            "text": ai_response,
            "actions": [{"type": "blocker_help_fallback"}],
            "suggestions": ["Show my tasks", "I'm still stuck", "Create a task for this"],
        }

    async def _generate_ai_response(self, message: str, context: AgentContext) -> str:
        """Generate response using AI provider"""
        import json as _json

        from app.services.ai_service import get_ai_service
        ai_service = get_ai_service()

        history = ""
        if context.conversation_history:
            recent = context.conversation_history[-6:]
            for msg in recent:
                role = "User" if msg.role == MessageRole.USER else "Assistant"
                history += f"{role}: {msg.content}\n"

        system_prompt = """You are TaskPulse AI, a helpful project management assistant.
You help users with their tasks, productivity, and work questions.
Keep responses concise (2-4 sentences) and actionable.
You can help with: creating tasks, viewing tasks, getting unblocked, performance feedback, and general work advice."""

        prompt = message
        if history:
            prompt = f"Conversation so far:\n{history}\nUser: {message}\n\nRespond helpfully:"

        try:
            response = await ai_service.generate(
                prompt=prompt,
                system_prompt=system_prompt,
                use_cache=False,
                temperature=0.7,
                max_tokens=500,
            )
            content = response.content

            # Safety net: if AI returned JSON instead of text, extract readable content
            try:
                parsed = _json.loads(content)
                if isinstance(parsed, dict) and "response" in parsed:
                    return parsed["response"]
                if isinstance(parsed, dict) and "suggestion" in parsed:
                    return parsed["suggestion"]
            except (_json.JSONDecodeError, TypeError):
                pass

            return content
        except Exception as e:
            logger.warning(f"AI generation failed: {e}")
            return """I can help you with many things! Here's what I can do:

- **"I need to build X by Y"** — Create a task with subtasks and check-in schedule
- **"my tasks"** — View your active tasks
- **"I'm stuck"** — Get help with blockers
- **"I'm on track"** — Update your check-in status
- **"how am I doing"** — See your performance

What would you like to do?"""

    async def _get_user_stats(self, context: AgentContext) -> Dict[str, Any]:
        """Get user statistics from real data."""
        if not context.db or not context.user:
            return {
                "active_tasks": 0, "completed_today": 0, "blocked_tasks": 0,
                "in_progress": 0, "in_review": 0, "todo": 0,
            }

        try:
            from sqlalchemy import select, func, and_
            from app.models.task import Task, TaskStatus
            from datetime import datetime, timedelta

            user_id = context.user.id
            org_id = context.organization.id if context.organization else None

            if not org_id:
                return {
                    "active_tasks": 0, "completed_today": 0, "blocked_tasks": 0,
                    "in_progress": 0, "in_review": 0, "todo": 0,
                }

            # Count by status
            status_counts = {}
            for status in [TaskStatus.TODO, TaskStatus.IN_PROGRESS, TaskStatus.BLOCKED, TaskStatus.REVIEW, TaskStatus.DONE]:
                result = await context.db.execute(
                    select(func.count()).select_from(Task).where(
                        Task.assigned_to == user_id,
                        Task.org_id == org_id,
                        Task.status == status,
                    )
                )
                status_counts[status.value] = result.scalar() or 0

            # Completed today
            today_start = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
            result = await context.db.execute(
                select(func.count()).select_from(Task).where(
                    Task.assigned_to == user_id,
                    Task.org_id == org_id,
                    Task.status == TaskStatus.DONE,
                    Task.completed_at >= today_start,
                )
            )
            completed_today = result.scalar() or 0

            active = status_counts.get("in_progress", 0) + status_counts.get("blocked", 0) + status_counts.get("review", 0)

            return {
                "active_tasks": active,
                "completed_today": completed_today,
                "blocked_tasks": status_counts.get("blocked", 0),
                "in_progress": status_counts.get("in_progress", 0),
                "in_review": status_counts.get("review", 0),
                "todo": status_counts.get("todo", 0),
            }

        except Exception as e:
            logger.warning(f"Failed to get user stats: {e}")
            return {
                "active_tasks": 0, "completed_today": 0, "blocked_tasks": 0,
                "in_progress": 0, "in_review": 0, "todo": 0,
            }

    async def _get_user_tasks(self, context: AgentContext) -> List[Dict[str, Any]]:
        """Get user's tasks from real data."""
        if not context.db or not context.user:
            return []

        try:
            from sqlalchemy import select
            from app.models.task import Task, TaskStatus

            user_id = context.user.id
            org_id = context.organization.id if context.organization else None

            if not org_id:
                return []

            result = await context.db.execute(
                select(Task).where(
                    Task.assigned_to == user_id,
                    Task.org_id == org_id,
                    Task.status.in_([
                        TaskStatus.TODO, TaskStatus.IN_PROGRESS,
                        TaskStatus.BLOCKED, TaskStatus.REVIEW,
                    ]),
                ).order_by(Task.updated_at.desc()).limit(10)
            )
            tasks = result.scalars().all()

            return [
                {
                    "id": t.id,
                    "title": t.title,
                    "status": t.status.value.lower(),
                    "priority": t.priority.value.lower() if t.priority else "medium",
                    "estimated_hours": t.estimated_hours,
                    "deadline": t.deadline.isoformat() if t.deadline else None,
                }
                for t in tasks
            ]

        except Exception as e:
            logger.warning(f"Failed to get user tasks: {e}")
            return []

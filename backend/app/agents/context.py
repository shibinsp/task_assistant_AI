"""
Agent Context

Provides shared context for agent execution, including conversation history,
task data, user information, and results from previous agents in a chain.
"""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional, TYPE_CHECKING
from uuid import uuid4

if TYPE_CHECKING:
    from .base import AgentEvent, AgentResult


class MessageRole(str, Enum):
    """Role of message sender in conversation"""
    USER = "user"
    AGENT = "agent"
    SYSTEM = "system"


@dataclass
class ConversationMessage:
    """A single message in a conversation"""
    id: str = field(default_factory=lambda: str(uuid4()))
    role: MessageRole = MessageRole.USER
    content: str = ""
    timestamp: datetime = field(default_factory=datetime.utcnow)

    # Optional metadata
    agent_name: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

    # For rich responses
    attachments: List[Dict[str, Any]] = field(default_factory=list)
    actions: List[Dict[str, Any]] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "role": self.role.value,
            "content": self.content,
            "timestamp": self.timestamp.isoformat(),
            "agent_name": self.agent_name,
            "metadata": self.metadata,
            "attachments": self.attachments,
            "actions": self.actions,
        }


@dataclass
class TaskData:
    """Task information for agent context"""
    id: str
    title: str
    description: Optional[str] = None
    status: str = "pending"
    priority: str = "medium"
    estimated_hours: Optional[float] = None
    actual_hours: Optional[float] = None
    due_date: Optional[datetime] = None
    assignee_id: Optional[str] = None
    created_by_id: Optional[str] = None
    tags: List[str] = field(default_factory=list)
    blockers: List[str] = field(default_factory=list)
    subtasks: List["TaskData"] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)

    @classmethod
    def from_model(cls, task: Any) -> "TaskData":
        """Create TaskData from a Task model"""
        return cls(
            id=str(task.id),
            title=task.title,
            description=task.description,
            status=task.status.value if hasattr(task.status, 'value') else task.status,
            priority=task.priority.value if hasattr(task.priority, 'value') else task.priority,
            estimated_hours=task.estimated_hours,
            actual_hours=task.actual_hours,
            due_date=task.due_date,
            assignee_id=str(task.assignee_id) if task.assignee_id else None,
            created_by_id=str(task.created_by_id) if task.created_by_id else None,
        )


@dataclass
class UserData:
    """User information for agent context"""
    id: str
    email: str
    full_name: str
    role: str = "employee"
    skill_level: str = "intermediate"
    skills: List[str] = field(default_factory=list)
    team_id: Optional[str] = None
    manager_id: Optional[str] = None
    preferences: Dict[str, Any] = field(default_factory=dict)

    @classmethod
    def from_model(cls, user: Any) -> "UserData":
        """Create UserData from a User model"""
        return cls(
            id=str(user.id),
            email=user.email,
            full_name=user.full_name,
            role=user.role.value if hasattr(user.role, 'value') else user.role,
        )


@dataclass
class OrganizationData:
    """Organization information for agent context"""
    id: str
    name: str
    settings: Dict[str, Any] = field(default_factory=dict)


@dataclass
class AgentContext:
    """
    Shared context for agent execution.

    Contains all information an agent needs to perform its task,
    including the triggering event, task/user data, conversation
    history, and results from previous agents.
    """

    # Unique context identifier
    id: str = field(default_factory=lambda: str(uuid4()))

    # The triggering event
    event: Optional["AgentEvent"] = None

    # Core data
    task: Optional[TaskData] = None
    user: Optional[UserData] = None
    organization: Optional[OrganizationData] = None

    # Conversation context
    conversation_id: Optional[str] = None
    conversation_history: List[ConversationMessage] = field(default_factory=list)

    # For agent chaining
    previous_results: List["AgentResult"] = field(default_factory=list)
    chain_data: Dict[str, Any] = field(default_factory=dict)

    # General metadata
    metadata: Dict[str, Any] = field(default_factory=dict)

    # Timing
    created_at: datetime = field(default_factory=datetime.utcnow)

    # Database session (set by orchestrator)
    db: Optional[Any] = None

    def add_message(
        self,
        content: str,
        role: MessageRole = MessageRole.USER,
        agent_name: Optional[str] = None,
        **kwargs
    ) -> ConversationMessage:
        """Add a message to the conversation history"""
        message = ConversationMessage(
            role=role,
            content=content,
            agent_name=agent_name,
            **kwargs
        )
        self.conversation_history.append(message)
        return message

    def get_last_message(self) -> Optional[ConversationMessage]:
        """Get the most recent message"""
        if self.conversation_history:
            return self.conversation_history[-1]
        return None

    def get_messages_by_role(self, role: MessageRole) -> List[ConversationMessage]:
        """Get all messages from a specific role"""
        return [m for m in self.conversation_history if m.role == role]

    def get_conversation_text(self, max_messages: int = 10) -> str:
        """Get conversation as formatted text for AI context"""
        messages = self.conversation_history[-max_messages:]
        lines = []
        for msg in messages:
            role_label = msg.agent_name or msg.role.value.capitalize()
            lines.append(f"{role_label}: {msg.content}")
        return "\n".join(lines)

    def add_previous_result(self, result: "AgentResult") -> None:
        """Add a result from a previous agent in the chain"""
        self.previous_results.append(result)

    def get_chain_result(self, agent_name: str) -> Optional["AgentResult"]:
        """Get result from a specific agent in the chain"""
        for result in self.previous_results:
            if result.agent_name == agent_name:
                return result
        return None

    def set_chain_data(self, key: str, value: Any) -> None:
        """Set data to pass to subsequent agents"""
        self.chain_data[key] = value

    def get_chain_data(self, key: str, default: Any = None) -> Any:
        """Get data from previous agents"""
        return self.chain_data.get(key, default)

    def to_dict(self) -> Dict[str, Any]:
        """Convert context to dictionary for serialization"""
        return {
            "id": self.id,
            "event_id": self.event.id if self.event else None,
            "task_id": self.task.id if self.task else None,
            "user_id": self.user.id if self.user else None,
            "org_id": self.organization.id if self.organization else None,
            "conversation_id": self.conversation_id,
            "message_count": len(self.conversation_history),
            "previous_agent_count": len(self.previous_results),
            "created_at": self.created_at.isoformat(),
            "metadata": self.metadata,
        }

    @classmethod
    def for_task(
        cls,
        task: Any,
        user: Any,
        event: Optional["AgentEvent"] = None
    ) -> "AgentContext":
        """Create context for a task-related event"""
        return cls(
            event=event,
            task=TaskData.from_model(task),
            user=UserData.from_model(user),
        )

    @classmethod
    def for_conversation(
        cls,
        user: Any,
        message: str,
        conversation_id: Optional[str] = None
    ) -> "AgentContext":
        """Create context for a conversation"""
        context = cls(
            user=UserData.from_model(user),
            conversation_id=conversation_id or str(uuid4()),
        )
        context.add_message(message, MessageRole.USER)
        return context

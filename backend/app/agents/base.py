"""
Base Agent Classes and Types

Provides the foundational abstract base class and types for all agents
in the TaskPulse - AI Assistant multi-agent system.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional, TYPE_CHECKING
from uuid import uuid4

if TYPE_CHECKING:
    from .context import AgentContext


class AgentStatus(str, Enum):
    """Agent operational status"""
    IDLE = "idle"
    RUNNING = "running"
    PAUSED = "paused"
    ERROR = "error"
    DISABLED = "disabled"


class AgentCapability(str, Enum):
    """Agent capabilities for permission and routing"""
    # AI Capabilities
    TASK_DECOMPOSITION = "task_decomposition"
    UNBLOCK_ASSISTANCE = "unblock_assistance"
    PREDICTION = "prediction"
    SKILL_MATCHING = "skill_matching"
    COACHING = "coaching"

    # Integration Capabilities
    JIRA_SYNC = "jira_sync"
    GITHUB_SYNC = "github_sync"
    SLACK_NOTIFY = "slack_notify"
    EMAIL_NOTIFY = "email_notify"
    CALENDAR_SYNC = "calendar_sync"

    # Conversation Capabilities
    CHAT = "chat"
    NATURAL_LANGUAGE = "natural_language"
    COMMAND_PROCESSING = "command_processing"


class EventType(str, Enum):
    """Types of events that can trigger agents"""
    # Task Events
    TASK_CREATED = "task_created"
    TASK_UPDATED = "task_updated"
    TASK_BLOCKED = "task_blocked"
    TASK_COMPLETED = "task_completed"
    TASK_ASSIGNED = "task_assigned"

    # Check-in Events
    CHECKIN_DUE = "checkin_due"
    CHECKIN_RESPONSE = "checkin_response"
    CHECKIN_MISSED = "checkin_missed"

    # User Events
    USER_MESSAGE = "user_message"
    USER_COMMAND = "user_command"
    USER_STUCK = "user_stuck"

    # System Events
    SCHEDULED = "scheduled"
    INTEGRATION_WEBHOOK = "integration_webhook"
    AGENT_CHAIN = "agent_chain"

    # Integration Events
    EXTERNAL_UPDATE = "external_update"
    SYNC_REQUESTED = "sync_requested"


@dataclass
class AgentEvent:
    """Event that can trigger agent execution"""
    id: str = field(default_factory=lambda: str(uuid4()))
    event_type: EventType = EventType.TASK_CREATED
    source: str = "system"
    timestamp: datetime = field(default_factory=datetime.utcnow)
    payload: Dict[str, Any] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)

    # Routing information
    target_agent: Optional[str] = None
    org_id: Optional[str] = None
    user_id: Optional[str] = None
    task_id: Optional[str] = None

    # Chain information for multi-agent workflows
    parent_event_id: Optional[str] = None
    chain_depth: int = 0
    max_chain_depth: int = 5


@dataclass
class AgentResult:
    """Result from agent execution"""
    success: bool
    agent_name: str
    event_id: str
    started_at: datetime = field(default_factory=datetime.utcnow)
    completed_at: Optional[datetime] = None
    duration_ms: Optional[int] = None

    # Output data
    output: Dict[str, Any] = field(default_factory=dict)
    message: Optional[str] = None

    # Actions taken
    actions: List[Dict[str, Any]] = field(default_factory=list)

    # Follow-up events to trigger
    follow_up_events: List[AgentEvent] = field(default_factory=list)

    # Error information
    error: Optional[str] = None
    error_code: Optional[str] = None

    # Metrics
    tokens_used: int = 0
    api_calls: int = 0

    def complete(self, success: bool = True, error: Optional[str] = None):
        """Mark the result as complete"""
        self.completed_at = datetime.utcnow()
        self.success = success
        self.error = error
        if self.started_at:
            self.duration_ms = int(
                (self.completed_at - self.started_at).total_seconds() * 1000
            )


class AgentError(Exception):
    """Base exception for agent errors"""
    def __init__(
        self,
        message: str,
        code: str = "AGENT_ERROR",
        details: Optional[Dict[str, Any]] = None
    ):
        super().__init__(message)
        self.code = code
        self.details = details or {}


class AgentValidationError(AgentError):
    """Raised when agent input validation fails"""
    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(message, "VALIDATION_ERROR", details)


class AgentExecutionError(AgentError):
    """Raised when agent execution fails"""
    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(message, "EXECUTION_ERROR", details)


class BaseAgent(ABC):
    """
    Abstract base class for all agents in the TaskPulse - AI Assistant system.

    Agents are autonomous units that respond to events and perform
    specific tasks. They can chain together to form complex workflows.

    Example:
        class MyAgent(BaseAgent):
            name = "my_agent"
            description = "Does something useful"
            capabilities = [AgentCapability.TASK_DECOMPOSITION]

            async def can_handle(self, event: AgentEvent) -> bool:
                return event.event_type == EventType.TASK_CREATED

            async def execute(self, context: AgentContext) -> AgentResult:
                # Do work here
                return AgentResult(success=True, agent_name=self.name)
    """

    # Agent identity
    name: str = "base_agent"
    description: str = "Base agent class"
    version: str = "1.0.0"

    # Capabilities and permissions
    capabilities: List[AgentCapability] = []
    required_permissions: List[str] = []

    # Event handling
    handled_events: List[EventType] = []
    priority: int = 100  # Lower = higher priority

    # Configuration
    enabled: bool = True
    max_retries: int = 3
    timeout_seconds: int = 60

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """Initialize the agent with optional configuration"""
        self.config = config or {}
        self.status = AgentStatus.IDLE
        self._error_count = 0
        self._last_execution: Optional[datetime] = None
        self._execution_count = 0

    @abstractmethod
    async def can_handle(self, event: AgentEvent) -> bool:
        """
        Determine if this agent can handle the given event.

        Args:
            event: The event to evaluate

        Returns:
            True if this agent should handle the event
        """
        pass

    @abstractmethod
    async def execute(self, context: "AgentContext") -> AgentResult:
        """
        Execute the agent's main logic.

        Args:
            context: The execution context with all necessary data

        Returns:
            Result of the agent execution
        """
        pass

    async def validate(self, context: "AgentContext") -> bool:
        """
        Validate the context before execution.

        Override this to add custom validation logic.

        Args:
            context: The execution context

        Returns:
            True if validation passes

        Raises:
            AgentValidationError: If validation fails
        """
        return True

    async def before_execute(self, context: "AgentContext") -> None:
        """Hook called before execute(). Override for setup logic."""
        self.status = AgentStatus.RUNNING
        self._last_execution = datetime.utcnow()

    async def after_execute(
        self,
        context: "AgentContext",
        result: AgentResult
    ) -> None:
        """Hook called after execute(). Override for cleanup logic."""
        self.status = AgentStatus.IDLE
        self._execution_count += 1
        if not result.success:
            self._error_count += 1

    async def on_error(
        self,
        context: "AgentContext",
        error: Exception
    ) -> AgentResult:
        """
        Handle errors during execution.

        Override to customize error handling.
        """
        self.status = AgentStatus.ERROR
        self._error_count += 1

        return AgentResult(
            success=False,
            agent_name=self.name,
            event_id=context.event.id if context.event else "unknown",
            message="I encountered an issue processing your request. Could you try again?",
            error=str(error),
            error_code=getattr(error, 'code', 'UNKNOWN_ERROR')
        )

    def get_stats(self) -> Dict[str, Any]:
        """Get agent statistics"""
        return {
            "name": self.name,
            "status": self.status.value,
            "execution_count": self._execution_count,
            "error_count": self._error_count,
            "last_execution": self._last_execution.isoformat() if self._last_execution else None,
            "enabled": self.enabled,
        }

    def __repr__(self) -> str:
        return f"<{self.__class__.__name__}(name={self.name}, status={self.status.value})>"

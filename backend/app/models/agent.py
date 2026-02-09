"""
Agent Database Models

Models for tracking agent configuration, executions, and conversations.
"""

from datetime import datetime
from enum import Enum
from typing import Optional
from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    Enum as SQLEnum,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
    JSON,
)
from sqlalchemy.orm import relationship

from ..database import Base


class AgentType(str, Enum):
    """Types of agents in the system"""
    AI = "ai"
    INTEGRATION = "integration"
    CONVERSATION = "conversation"


class AgentStatusDB(str, Enum):
    """Agent operational status"""
    ACTIVE = "active"
    PAUSED = "paused"
    ERROR = "error"
    DISABLED = "disabled"


class ExecutionStatus(str, Enum):
    """Status of an agent execution"""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class Agent(Base):
    """
    Agent configuration and metadata.

    Stores registered agents and their settings.
    """
    __tablename__ = "agents"

    id = Column(String(36), primary_key=True)
    org_id = Column(String(36), ForeignKey("organizations.id"), nullable=False, index=True)

    # Identity
    name = Column(String(100), nullable=False, unique=True)
    display_name = Column(String(200), nullable=False)
    description = Column(Text, nullable=True)
    version = Column(String(20), default="1.0.0")

    # Classification
    agent_type = Column(SQLEnum(AgentType), nullable=False, default=AgentType.AI)
    capabilities = Column(JSON, default=list)  # List of capability strings

    # Status
    status = Column(SQLEnum(AgentStatusDB), default=AgentStatusDB.ACTIVE)
    is_enabled = Column(Boolean, default=True)

    # Configuration
    config = Column(JSON, default=dict)
    permissions = Column(JSON, default=list)

    # Metrics
    execution_count = Column(Integer, default=0)
    success_count = Column(Integer, default=0)
    error_count = Column(Integer, default=0)
    avg_duration_ms = Column(Float, nullable=True)
    last_execution_at = Column(DateTime, nullable=True)

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    organization = relationship("Organization", backref="agents")
    executions = relationship("AgentExecution", back_populates="agent", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Agent(name={self.name}, type={self.agent_type.value})>"


class AgentExecution(Base):
    """
    Record of an agent execution.

    Tracks each time an agent runs, including input, output, and performance.
    """
    __tablename__ = "agent_executions"

    id = Column(String(36), primary_key=True)
    agent_id = Column(String(36), ForeignKey("agents.id"), nullable=False, index=True)
    org_id = Column(String(36), ForeignKey("organizations.id"), nullable=False, index=True)

    # Trigger information
    event_type = Column(String(100), nullable=False)
    event_id = Column(String(36), nullable=True)
    trigger_source = Column(String(100), nullable=True)  # user, system, scheduled, chain

    # Context
    user_id = Column(String(36), ForeignKey("users.id"), nullable=True)
    task_id = Column(String(36), ForeignKey("tasks.id"), nullable=True)
    context_data = Column(JSON, default=dict)

    # Execution details
    status = Column(SQLEnum(ExecutionStatus), default=ExecutionStatus.PENDING)
    started_at = Column(DateTime, default=datetime.utcnow)
    completed_at = Column(DateTime, nullable=True)
    duration_ms = Column(Integer, nullable=True)

    # Results
    success = Column(Boolean, default=False)
    output_data = Column(JSON, default=dict)
    error_message = Column(Text, nullable=True)
    error_code = Column(String(50), nullable=True)

    # Metrics
    tokens_used = Column(Integer, default=0)
    api_calls = Column(Integer, default=0)

    # Chain information
    parent_execution_id = Column(String(36), ForeignKey("agent_executions.id"), nullable=True)
    chain_depth = Column(Integer, default=0)

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    agent = relationship("Agent", back_populates="executions")
    organization = relationship("Organization")
    user = relationship("User")
    task = relationship("Task")
    parent_execution = relationship("AgentExecution", remote_side=[id])

    def __repr__(self):
        return f"<AgentExecution(agent={self.agent_id}, status={self.status.value})>"


class AgentConversation(Base):
    """
    Chat conversation with an agent.

    Stores conversation history for context continuity.
    """
    __tablename__ = "agent_conversations"

    id = Column(String(36), primary_key=True)
    org_id = Column(String(36), ForeignKey("organizations.id"), nullable=False, index=True)
    user_id = Column(String(36), ForeignKey("users.id"), nullable=False, index=True)

    # Conversation metadata
    title = Column(String(200), nullable=True)
    agent_name = Column(String(100), nullable=False, default="chat_agent")

    # State
    is_active = Column(Boolean, default=True)
    message_count = Column(Integer, default=0)

    # Conversation data
    messages = Column(JSON, default=list)  # List of ConversationMessage dicts
    context_data = Column(JSON, default=dict)  # Persistent context

    # Timestamps
    started_at = Column(DateTime, default=datetime.utcnow)
    last_message_at = Column(DateTime, default=datetime.utcnow)
    ended_at = Column(DateTime, nullable=True)

    # Relationships
    organization = relationship("Organization")
    user = relationship("User")

    def add_message(self, role: str, content: str, agent_name: Optional[str] = None, metadata: Optional[dict] = None):
        """Add a message to the conversation"""
        from uuid import uuid4

        message = {
            "id": str(uuid4()),
            "role": role,
            "content": content,
            "agent_name": agent_name,
            "metadata": metadata or {},
            "timestamp": datetime.utcnow().isoformat(),
        }

        if self.messages is None:
            self.messages = []

        self.messages.append(message)
        self.message_count = len(self.messages)
        self.last_message_at = datetime.utcnow()

        return message

    def get_recent_messages(self, limit: int = 10):
        """Get recent messages"""
        if not self.messages:
            return []
        return self.messages[-limit:]

    def __repr__(self):
        return f"<AgentConversation(user={self.user_id}, messages={self.message_count})>"


class AgentSchedule(Base):
    """
    Scheduled agent executions.

    For agents that need to run on a schedule (e.g., daily predictions).
    """
    __tablename__ = "agent_schedules"

    id = Column(String(36), primary_key=True)
    agent_id = Column(String(36), ForeignKey("agents.id"), nullable=False, index=True)
    org_id = Column(String(36), ForeignKey("organizations.id"), nullable=False, index=True)

    # Schedule definition
    name = Column(String(100), nullable=False)
    cron_expression = Column(String(100), nullable=False)  # e.g., "0 9 * * *"
    timezone = Column(String(50), default="UTC")

    # Configuration
    is_enabled = Column(Boolean, default=True)
    config = Column(JSON, default=dict)  # Additional config for scheduled run

    # Tracking
    last_run_at = Column(DateTime, nullable=True)
    next_run_at = Column(DateTime, nullable=True)
    run_count = Column(Integer, default=0)
    failure_count = Column(Integer, default=0)

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    agent = relationship("Agent")
    organization = relationship("Organization")

    def __repr__(self):
        return f"<AgentSchedule(agent={self.agent_id}, cron={self.cron_expression})>"

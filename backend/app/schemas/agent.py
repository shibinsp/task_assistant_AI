"""
TaskPulse - AI Assistant - Agent Schemas
Pydantic schemas for agent orchestration system
"""

from datetime import datetime
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field

from app.models.agent import AgentType, AgentStatusDB, ExecutionStatus


# ==================== Agent Schemas ====================

class AgentConfigUpdate(BaseModel):
    """Schema for updating agent configuration."""
    is_enabled: Optional[bool] = None
    config: Optional[Dict[str, Any]] = None
    permissions: Optional[List[str]] = None


class AgentResponse(BaseModel):
    """Schema for agent in API responses."""
    id: str
    org_id: str

    # Identity
    name: str
    display_name: str
    description: Optional[str] = None
    version: str = "1.0.0"

    # Classification
    agent_type: AgentType
    capabilities: List[str] = Field(default_factory=list)

    # Status
    status: AgentStatusDB
    is_enabled: bool = True

    # Metrics
    execution_count: int = 0
    success_count: int = 0
    error_count: int = 0
    avg_duration_ms: Optional[float] = None
    last_execution_at: Optional[datetime] = None

    # Computed
    success_rate: float = Field(default=0.0, ge=0, le=100)

    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class AgentDetailResponse(AgentResponse):
    """Detailed agent response with configuration."""
    config: Dict[str, Any] = Field(default_factory=dict)
    permissions: List[str] = Field(default_factory=list)


class AgentListResponse(BaseModel):
    """Response for list of agents."""
    agents: List[AgentResponse]
    total: int
    enabled_count: int = 0
    by_type: Dict[str, int] = Field(default_factory=dict)


class AgentStatsResponse(BaseModel):
    """Response for agent statistics."""
    registered_agents: int
    enabled_agents: int
    total_executions: int
    recent_executions: int

    # By type
    by_type: Dict[str, int] = Field(default_factory=dict)

    # Event bus
    event_bus: Dict[str, Any] = Field(default_factory=dict)

    # Top agents
    most_active: List[Dict[str, Any]] = Field(default_factory=list)
    highest_success_rate: List[Dict[str, Any]] = Field(default_factory=list)


# ==================== Agent Execution Schemas ====================

class ExecuteAgentRequest(BaseModel):
    """Request to execute an agent."""
    event_type: str = Field(..., description="Event type to trigger")
    payload: Dict[str, Any] = Field(default_factory=dict, description="Event payload")
    context: Dict[str, Any] = Field(default_factory=dict, description="Additional context")
    task_id: Optional[str] = Field(None, description="Related task ID")


class AgentExecutionResponse(BaseModel):
    """Schema for agent execution in API responses."""
    id: str
    agent_id: str
    org_id: str

    # Trigger
    event_type: str
    event_id: Optional[str] = None
    trigger_source: Optional[str] = None

    # Context
    user_id: Optional[str] = None
    task_id: Optional[str] = None
    context_data: Dict[str, Any] = Field(default_factory=dict)

    # Status
    status: ExecutionStatus
    started_at: datetime
    completed_at: Optional[datetime] = None
    duration_ms: Optional[int] = None

    # Results
    success: bool = False
    output_data: Dict[str, Any] = Field(default_factory=dict)
    error_message: Optional[str] = None
    error_code: Optional[str] = None

    # Metrics
    tokens_used: int = 0
    api_calls: int = 0

    # Chain info
    parent_execution_id: Optional[str] = None
    chain_depth: int = 0

    created_at: datetime

    model_config = {"from_attributes": True}


class ExecutionListResponse(BaseModel):
    """Response for list of executions."""
    executions: List[AgentExecutionResponse]
    total: int
    page: int
    page_size: int


class ExecutionSummaryResponse(BaseModel):
    """Summary of agent executions."""
    agent_id: str
    agent_name: str

    # Counts
    total_executions: int
    successful: int
    failed: int
    success_rate: float = Field(ge=0, le=100)

    # Performance
    avg_duration_ms: Optional[float] = None
    min_duration_ms: Optional[int] = None
    max_duration_ms: Optional[int] = None

    # Usage
    total_tokens: int = 0
    total_api_calls: int = 0

    # Period
    period_start: datetime
    period_end: datetime


# ==================== Agent Conversation Schemas ====================

class ConversationMessage(BaseModel):
    """Chat message in a conversation."""
    id: str
    role: str = Field(..., description="Role: user, assistant, system")
    content: str
    agent_name: Optional[str] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)
    timestamp: datetime


class AgentConversationResponse(BaseModel):
    """Schema for agent conversation in API responses."""
    id: str
    org_id: str
    user_id: str

    # Metadata
    title: Optional[str] = None
    agent_name: str = "chat_agent"

    # State
    is_active: bool = True
    message_count: int = 0

    # Messages
    messages: List[ConversationMessage] = Field(default_factory=list)
    context_data: Dict[str, Any] = Field(default_factory=dict)

    # Timestamps
    started_at: datetime
    last_message_at: datetime
    ended_at: Optional[datetime] = None

    model_config = {"from_attributes": True}


class ConversationListResponse(BaseModel):
    """Response for list of conversations."""
    conversations: List[AgentConversationResponse]
    total: int
    active_count: int = 0


class SendMessageRequest(BaseModel):
    """Request to send a chat message."""
    message: str = Field(..., min_length=1, description="Message content")
    conversation_id: Optional[str] = Field(None, description="Existing conversation ID")
    context: Dict[str, Any] = Field(default_factory=dict, description="Additional context")


class ChatMessageResponse(BaseModel):
    """Response from chat agent."""
    conversation_id: str
    message_id: str

    # Response
    response: str
    agent_name: str = "chat_agent"

    # Actions taken
    actions: List[Dict[str, Any]] = Field(default_factory=list)

    # Suggestions
    suggestions: List[str] = Field(default_factory=list)

    # Metadata
    intent: Optional[str] = None
    confidence: float = Field(ge=0, le=1)

    timestamp: datetime


# ==================== Orchestration Schemas ====================

class OrchestrationRequest(BaseModel):
    """Request to run agent orchestration pipeline."""
    agents: List[str] = Field(..., min_length=1, description="Agent names to run")
    event_type: str = Field(..., description="Event type")
    payload: Dict[str, Any] = Field(default_factory=dict, description="Event payload")
    parallel: bool = Field(default=False, description="Run agents in parallel")
    stop_on_failure: bool = Field(default=True, description="Stop pipeline on failure")


class OrchestrationStepResult(BaseModel):
    """Result of a single orchestration step."""
    agent_name: str
    execution_id: str
    success: bool
    output: Dict[str, Any] = Field(default_factory=dict)
    error: Optional[str] = None
    duration_ms: Optional[int] = None


class OrchestrationResponse(BaseModel):
    """Response from orchestration pipeline."""
    pipeline_id: str

    # Results
    success: bool
    steps: List[OrchestrationStepResult]

    # Summary
    agents_run: int
    agents_succeeded: int
    agents_failed: int
    total_duration_ms: int

    # Final output
    final_output: Dict[str, Any] = Field(default_factory=dict)

    started_at: datetime
    completed_at: datetime


# ==================== Agent Schedule Schemas ====================

class AgentScheduleCreate(BaseModel):
    """Schema for creating an agent schedule."""
    agent_id: str = Field(..., description="Agent ID")
    name: str = Field(..., min_length=1, max_length=100, description="Schedule name")
    cron_expression: str = Field(..., description="Cron expression")
    timezone: str = Field(default="UTC", description="Timezone")
    config: Dict[str, Any] = Field(default_factory=dict, description="Additional config")


class AgentScheduleUpdate(BaseModel):
    """Schema for updating an agent schedule."""
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    cron_expression: Optional[str] = None
    timezone: Optional[str] = None
    config: Optional[Dict[str, Any]] = None
    is_enabled: Optional[bool] = None


class AgentScheduleResponse(BaseModel):
    """Schema for agent schedule in API responses."""
    id: str
    agent_id: str
    org_id: str

    # Schedule
    name: str
    cron_expression: str
    timezone: str = "UTC"

    # Status
    is_enabled: bool = True

    # Configuration
    config: Dict[str, Any] = Field(default_factory=dict)

    # Tracking
    last_run_at: Optional[datetime] = None
    next_run_at: Optional[datetime] = None
    run_count: int = 0
    failure_count: int = 0

    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class AgentScheduleListResponse(BaseModel):
    """Response for list of agent schedules."""
    schedules: List[AgentScheduleResponse]
    total: int


# ==================== Recommendations Schemas ====================

class AgentRecommendation(BaseModel):
    """AI recommendation from an agent."""
    agent_name: str
    recommendation_type: str
    title: str
    description: str
    priority: str = Field(..., description="Priority: low, medium, high, critical")
    confidence: float = Field(ge=0, le=1)
    action_url: Optional[str] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)


class RecommendationsResponse(BaseModel):
    """Response for AI recommendations."""
    recommendations: List[AgentRecommendation]
    total: int
    by_agent: Dict[str, int] = Field(default_factory=dict)
    generated_at: datetime

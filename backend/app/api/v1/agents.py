"""
Agent API Endpoints

Manage agents, execute them, and view execution history.
"""

from datetime import datetime
from typing import Any, Dict, List, Optional
from uuid import uuid4

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from ...database import get_db
from ..v1.dependencies import get_current_user

router = APIRouter(prefix="/agents", tags=["Agents"])


# ============== Schemas ==============

class AgentInfo(BaseModel):
    """Agent information response - matches frontend ApiOrchestratorAgent"""
    name: str
    display_name: str
    description: Optional[str] = None
    agent_type: str
    capabilities: List[str] = []
    status: str
    is_enabled: bool = True
    execution_count: int = 0
    success_count: int = 0
    error_count: int = 0
    avg_duration_ms: float = 0.0

    class Config:
        from_attributes = True


class AgentExecuteRequest(BaseModel):
    """Request to execute an agent - matches frontend ApiAgentExecuteRequest"""
    event_type: str = "manual"
    event_data: Dict[str, Any] = Field(default_factory=dict)
    task_id: Optional[str] = None
    context: Dict[str, Any] = Field(default_factory=dict)


class AgentExecuteResponse(BaseModel):
    """Response from agent execution - matches frontend ApiAgentExecuteResponse"""
    execution_id: str
    agent_name: str
    status: str = "completed"
    output: Dict[str, Any] = Field(default_factory=dict)
    duration_ms: int = 0
    tokens_used: Optional[int] = None


class AgentConfigUpdate(BaseModel):
    """Update agent configuration"""
    is_enabled: Optional[bool] = None
    config: Optional[Dict[str, Any]] = None


class ExecutionRecord(BaseModel):
    """Agent execution record"""
    id: str
    agent_name: str
    event_type: str
    status: str
    success: bool
    started_at: datetime
    completed_at: Optional[datetime] = None
    duration_ms: Optional[int] = None
    error_message: Optional[str] = None

    class Config:
        from_attributes = True


class OrchestrateRequest(BaseModel):
    """Request to run agent pipeline - matches frontend agentsService.orchestrate()"""
    event_type: str = "orchestrate"
    event_data: Dict[str, Any] = Field(default_factory=dict)
    task_id: Optional[str] = None
    agent_names: List[str] = Field(default_factory=list)
    stop_on_error: bool = True


class RecommendationsResponse(BaseModel):
    """AI recommendations"""
    tasks: List[Dict[str, Any]] = []
    unblock_suggestions: List[Dict[str, Any]] = []
    skill_recommendations: List[Dict[str, Any]] = []
    productivity_tips: List[Dict[str, Any]] = []


# ============== Endpoints ==============

@router.get("", response_model=List[AgentInfo])
async def list_agents(
    agent_type: Optional[str] = Query(None, description="Filter by agent type"),
    is_enabled: Optional[bool] = Query(None, description="Filter by enabled status"),
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    List all available agents.

    Returns registered agents with their status and capabilities.
    """
    # Import orchestrator
    from ...agents.orchestrator import get_orchestrator

    orchestrator = get_orchestrator()
    stats = orchestrator.get_stats()

    agents = []
    for name, agent_info in stats.get("agents", {}).items():
        # Apply filters
        if is_enabled is not None and agent_info.get("enabled") != is_enabled:
            continue

        exec_count = agent_info.get("execution_count", 0)
        error_count = agent_info.get("error_count", 0)
        success_count = exec_count - error_count

        agents.append(AgentInfo(
            name=name,
            display_name=name.replace("_", " ").title(),
            description=None,
            agent_type=_get_agent_type(agent_info.get("capabilities", [])),
            capabilities=agent_info.get("capabilities", []),
            status=agent_info.get("status", "unknown"),
            is_enabled=agent_info.get("enabled", True),
            execution_count=exec_count,
            success_count=success_count,
            error_count=error_count,
            avg_duration_ms=agent_info.get("avg_duration_ms", 0.0),
        ))

    return agents


@router.get("/{agent_name}", response_model=AgentInfo)
async def get_agent(
    agent_name: str,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Get details for a specific agent.
    """
    from ...agents.orchestrator import get_orchestrator

    orchestrator = get_orchestrator()
    agent = orchestrator.get_agent(agent_name)

    if not agent:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Agent '{agent_name}' not found"
        )

    stats = agent.get_stats()
    exec_count = stats.get("execution_count", 0)
    error_count = stats.get("error_count", 0)
    success_count = exec_count - error_count

    return AgentInfo(
        name=agent.name,
        display_name=agent.name.replace("_", " ").title(),
        description=agent.description,
        agent_type=_get_agent_type([c.value for c in agent.capabilities]),
        capabilities=[c.value for c in agent.capabilities],
        status=stats.get("status", "unknown"),
        is_enabled=agent.enabled,
        execution_count=exec_count,
        success_count=success_count,
        error_count=error_count,
        avg_duration_ms=stats.get("avg_duration_ms", 0.0),
    )


@router.post("/{agent_name}/execute", response_model=AgentExecuteResponse)
async def execute_agent(
    agent_name: str,
    request: AgentExecuteRequest,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Manually execute an agent.

    Triggers the agent with the provided payload and context.
    """
    from ...agents.orchestrator import get_orchestrator
    from ...agents.base import AgentEvent, EventType
    from ...agents.context import AgentContext, UserData

    orchestrator = get_orchestrator()
    agent = orchestrator.get_agent(agent_name)

    if not agent:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Agent '{agent_name}' not found"
        )

    if not agent.enabled:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Agent '{agent_name}' is disabled"
        )

    # Create event
    event = AgentEvent(
        event_type=EventType.USER_COMMAND,
        payload=request.event_data,
        user_id=current_user.get("id"),
        task_id=request.task_id,
        metadata=request.context,
    )

    # Create context
    context = AgentContext(
        event=event,
        user=UserData(
            id=current_user.get("id", ""),
            email=current_user.get("email", ""),
            full_name=current_user.get("full_name", ""),
        ),
        db=db,
    )

    # Execute
    try:
        result = await orchestrator.execute_agent(agent_name, context)

        return AgentExecuteResponse(
            execution_id=str(uuid4()),
            agent_name=agent_name,
            status="completed" if result.success else "failed",
            output=result.output,
            duration_ms=result.duration_ms or 0,
        )

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.get("/{agent_name}/executions", response_model=List[ExecutionRecord])
async def get_agent_executions(
    agent_name: str,
    limit: int = Query(50, ge=1, le=100),
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Get execution history for an agent.
    """
    from ...agents.orchestrator import get_orchestrator

    orchestrator = get_orchestrator()
    history = orchestrator.get_execution_history(limit=limit, agent_name=agent_name)

    return [
        ExecutionRecord(
            id=h["id"],
            agent_name=h["agent_name"],
            event_type=h["event_type"],
            status="completed" if h["success"] else "failed",
            success=h["success"],
            started_at=datetime.fromisoformat(h["started_at"]),
            completed_at=datetime.fromisoformat(h["completed_at"]) if h.get("completed_at") else None,
            duration_ms=h.get("duration_ms"),
            error_message=h.get("error"),
        )
        for h in history
    ]


@router.patch("/{agent_name}/config")
async def update_agent_config(
    agent_name: str,
    update: AgentConfigUpdate,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Update agent configuration.
    """
    from ...agents.orchestrator import get_orchestrator

    orchestrator = get_orchestrator()
    agent = orchestrator.get_agent(agent_name)

    if not agent:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Agent '{agent_name}' not found"
        )

    if update.is_enabled is not None:
        agent.enabled = update.is_enabled

    if update.config:
        agent.config.update(update.config)

    return {"message": f"Agent '{agent_name}' configuration updated", "agent_name": agent_name}


@router.post("/orchestrate")
async def run_agent_pipeline(
    request: OrchestrateRequest,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Run a pipeline of agents in sequence.

    Agents are executed in order, with each receiving the context
    from previous agents.
    """
    from ...agents.orchestrator import get_orchestrator
    from ...agents.base import AgentEvent, EventType
    from ...agents.context import AgentContext, UserData

    orchestrator = get_orchestrator()

    # Validate all agents exist
    for agent_name in request.agent_names:
        if not orchestrator.get_agent(agent_name):
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Agent '{agent_name}' not found"
            )

    # Create event
    event = AgentEvent(
        event_type=EventType.AGENT_CHAIN,
        payload=request.event_data,
        user_id=current_user.get("id"),
    )

    # Create context
    context = AgentContext(
        event=event,
        user=UserData(
            id=current_user.get("id", ""),
            email=current_user.get("email", ""),
            full_name=current_user.get("full_name", ""),
        ),
        db=db,
    )

    # Run pipeline
    start_time = datetime.utcnow()

    try:
        results = await orchestrator.run_pipeline(
            request.agent_names,
            context,
            stop_on_error=request.stop_on_error
        )

        end_time = datetime.utcnow()
        total_duration = int((end_time - start_time).total_seconds() * 1000)

        response_results = [
            AgentExecuteResponse(
                execution_id=str(uuid4()),
                agent_name=r.agent_name,
                status="completed" if r.success else "failed",
                output=r.output,
                duration_ms=r.duration_ms or 0,
            )
            for r in results
        ]

        return {
            "pipeline_id": str(uuid4()),
            "results": [r.model_dump() for r in response_results],
            "total_duration_ms": total_duration,
            "success": all(r.success for r in results),
        }

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.get("/recommendations", response_model=RecommendationsResponse)
async def get_recommendations(
    task_id: Optional[str] = Query(None, description="Specific task for recommendations"),
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Get AI-powered recommendations for the current user.

    Aggregates insights from multiple agents (predictor, skill matcher, coach).
    """
    from ...agents.orchestrator import get_orchestrator

    orchestrator = get_orchestrator()

    try:
        recommendations = await orchestrator.get_recommendations(
            user_id=current_user.get("id"),
            task_id=task_id,
            db=db,
        )

        return RecommendationsResponse(**recommendations)

    except Exception as e:
        # Return empty recommendations on error
        return RecommendationsResponse()


@router.get("/stats")
async def get_agent_stats(
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Get overall agent system statistics.
    """
    from ...agents.orchestrator import get_orchestrator

    orchestrator = get_orchestrator()
    return orchestrator.get_stats()


# ============== Helper Functions ==============

def _get_agent_type(capabilities: List[str]) -> str:
    """Determine agent type from capabilities"""
    integration_caps = {"jira_sync", "github_sync", "slack_notify", "email_notify", "calendar_sync"}
    conversation_caps = {"chat", "natural_language", "command_processing"}

    caps_set = set(capabilities)

    if caps_set & integration_caps:
        return "integration"
    if caps_set & conversation_caps:
        return "conversation"
    return "ai"


def _parse_datetime(dt_str: Optional[str]) -> Optional[datetime]:
    """Parse datetime string"""
    if not dt_str:
        return None
    try:
        return datetime.fromisoformat(dt_str)
    except (ValueError, TypeError):
        return None

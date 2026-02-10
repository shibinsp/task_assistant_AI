"""
Agent Orchestrator

Central coordinator for the multi-agent system. Manages agent lifecycle,
routes events, handles agent chaining, and provides execution context.
"""

import asyncio
import logging
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Callable, Dict, List, Optional, Type, TYPE_CHECKING
from uuid import uuid4

from .base import (
    AgentCapability,
    AgentError,
    AgentEvent,
    AgentExecutionError,
    AgentResult,
    AgentStatus,
    BaseAgent,
    EventType,
)
from .context import AgentContext, ConversationMessage, MessageRole
from .event_bus import AgentEventBus, EventPriority, get_event_bus

if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import AsyncSession

logger = logging.getLogger(__name__)


@dataclass
class AgentRegistration:
    """Registration record for an agent"""
    agent: BaseAgent
    agent_class: Type[BaseAgent]
    registered_at: datetime = field(default_factory=datetime.utcnow)
    execution_count: int = 0
    last_execution: Optional[datetime] = None


@dataclass
class ExecutionRecord:
    """Record of an agent execution"""
    id: str = field(default_factory=lambda: str(uuid4()))
    agent_name: str = ""
    event_type: str = ""
    context_id: str = ""
    started_at: datetime = field(default_factory=datetime.utcnow)
    completed_at: Optional[datetime] = None
    success: bool = False
    duration_ms: Optional[int] = None
    error: Optional[str] = None
    result_summary: Optional[Dict[str, Any]] = None


class AgentOrchestrator:
    """
    Central orchestrator for the multi-agent system.

    Responsibilities:
    - Agent registration and lifecycle management
    - Event routing to appropriate agents
    - Execution context management
    - Agent chaining coordination
    - Metrics and monitoring

    Example:
        orchestrator = AgentOrchestrator()

        # Register agents
        orchestrator.register(UnblockAgent)
        orchestrator.register(DecomposerAgent)

        # Handle an event
        result = await orchestrator.handle_event(event, db_session)

        # Run agent pipeline
        results = await orchestrator.run_pipeline(
            ["decomposer", "skill_matcher"],
            context
        )
    """

    def __init__(
        self,
        event_bus: Optional[AgentEventBus] = None,
        max_chain_depth: int = 5
    ):
        self._agents: Dict[str, AgentRegistration] = {}
        self._capability_index: Dict[AgentCapability, List[str]] = {}
        self._event_bus = event_bus or get_event_bus()
        self._max_chain_depth = max_chain_depth
        self._execution_history: List[ExecutionRecord] = []
        self._max_history = 1000
        self._lock = asyncio.Lock()

        # Callbacks
        self._on_execution_start: Optional[Callable] = None
        self._on_execution_complete: Optional[Callable] = None

    def register(
        self,
        agent_class: Type[BaseAgent],
        config: Optional[Dict[str, Any]] = None,
        auto_subscribe: bool = True
    ) -> BaseAgent:
        """
        Register an agent with the orchestrator.

        Args:
            agent_class: The agent class to instantiate
            config: Optional configuration for the agent
            auto_subscribe: Whether to subscribe to the event bus

        Returns:
            The instantiated agent
        """
        agent = agent_class(config=config)

        registration = AgentRegistration(
            agent=agent,
            agent_class=agent_class,
        )

        self._agents[agent.name] = registration

        # Index by capabilities
        for capability in agent.capabilities:
            if capability not in self._capability_index:
                self._capability_index[capability] = []
            self._capability_index[capability].append(agent.name)

        # Subscribe to event bus
        if auto_subscribe and agent.handled_events:
            asyncio.create_task(
                self._event_bus.subscribe(agent, priority=agent.priority)
            )

        logger.info(
            f"Registered agent: {agent.name} "
            f"(capabilities: {[c.value for c in agent.capabilities]})"
        )

        return agent

    def unregister(self, agent_name: str) -> bool:
        """Unregister an agent"""
        registration = self._agents.pop(agent_name, None)
        if registration:
            # Remove from capability index
            for capability in registration.agent.capabilities:
                if capability in self._capability_index:
                    self._capability_index[capability] = [
                        n for n in self._capability_index[capability]
                        if n != agent_name
                    ]
            # Unsubscribe from event bus
            asyncio.create_task(self._event_bus.unsubscribe(agent_name))
            logger.info(f"Unregistered agent: {agent_name}")
            return True
        return False

    def get_agent(self, name: str) -> Optional[BaseAgent]:
        """Get an agent by name"""
        registration = self._agents.get(name)
        return registration.agent if registration else None

    def get_agents_by_capability(
        self,
        capability: AgentCapability
    ) -> List[BaseAgent]:
        """Get all agents with a specific capability"""
        agent_names = self._capability_index.get(capability, [])
        return [
            self._agents[name].agent
            for name in agent_names
            if name in self._agents
        ]

    async def handle_event(
        self,
        event: AgentEvent,
        db: Optional["AsyncSession"] = None
    ) -> List[AgentResult]:
        """
        Handle an event by routing to appropriate agents.

        Args:
            event: The event to handle
            db: Optional database session

        Returns:
            List of results from all agents that handled the event
        """
        results = []

        # Find agents that can handle this event
        handlers = await self._find_handlers(event)

        if not handlers:
            logger.debug(f"No handlers for event: {event.event_type.value}")
            return results

        # Create base context
        context = AgentContext(event=event, db=db)

        # Execute each handler
        for agent in handlers:
            try:
                result = await self._execute_agent(agent, context)
                results.append(result)

                # Handle follow-up events (chaining)
                if result.success and result.follow_up_events:
                    await self._handle_follow_ups(result.follow_up_events, event)

            except Exception as e:
                logger.error(f"Error executing agent {agent.name}: {e}")
                results.append(AgentResult(
                    success=False,
                    agent_name=agent.name,
                    event_id=event.id,
                    error=str(e)
                ))

        return results

    async def execute_agent(
        self,
        agent_name: str,
        context: AgentContext
    ) -> AgentResult:
        """
        Execute a specific agent with the given context.

        Args:
            agent_name: Name of the agent to execute
            context: Execution context

        Returns:
            Agent result
        """
        agent = self.get_agent(agent_name)
        if not agent:
            raise AgentError(f"Agent not found: {agent_name}", "AGENT_NOT_FOUND")

        return await self._execute_agent(agent, context)

    async def run_pipeline(
        self,
        agent_names: List[str],
        context: AgentContext,
        stop_on_error: bool = True
    ) -> List[AgentResult]:
        """
        Run a pipeline of agents in sequence.

        Args:
            agent_names: Ordered list of agent names to execute
            context: Shared execution context
            stop_on_error: Whether to stop on first error

        Returns:
            List of results from all agents
        """
        results = []

        for agent_name in agent_names:
            agent = self.get_agent(agent_name)
            if not agent:
                if stop_on_error:
                    raise AgentError(f"Agent not found: {agent_name}")
                continue

            try:
                result = await self._execute_agent(agent, context)
                results.append(result)

                # Add result to context for next agent
                context.add_previous_result(result)

                if not result.success and stop_on_error:
                    break

            except Exception as e:
                logger.error(f"Pipeline error at {agent_name}: {e}")
                if stop_on_error:
                    raise

        return results

    async def run_parallel(
        self,
        agent_names: List[str],
        context: AgentContext
    ) -> List[AgentResult]:
        """
        Run multiple agents in parallel.

        Args:
            agent_names: List of agent names to execute concurrently
            context: Shared execution context

        Returns:
            List of results from all agents
        """
        tasks = []

        for agent_name in agent_names:
            agent = self.get_agent(agent_name)
            if agent:
                # Create a copy of context for each agent
                agent_context = AgentContext(
                    event=context.event,
                    task=context.task,
                    user=context.user,
                    organization=context.organization,
                    conversation_history=context.conversation_history.copy(),
                    metadata=context.metadata.copy(),
                    db=context.db,
                )
                tasks.append(self._execute_agent(agent, agent_context))

        if not tasks:
            return []

        results = await asyncio.gather(*tasks, return_exceptions=True)

        # Convert exceptions to error results
        final_results = []
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                final_results.append(AgentResult(
                    success=False,
                    agent_name=agent_names[i],
                    event_id=context.event.id if context.event else "unknown",
                    error=str(result)
                ))
            else:
                final_results.append(result)

        return final_results

    async def chat(
        self,
        message: str,
        user_id: str,
        conversation_id: Optional[str] = None,
        db: Optional["AsyncSession"] = None
    ) -> AgentResult:
        """
        Process a chat message through the conversational agent.

        Args:
            message: User's message
            user_id: User ID
            conversation_id: Optional conversation ID for context
            db: Database session

        Returns:
            Agent result with response
        """
        # Find chat-capable agent
        chat_agents = self.get_agents_by_capability(AgentCapability.CHAT)
        if not chat_agents:
            return AgentResult(
                success=False,
                agent_name="orchestrator",
                event_id="",
                message="I'm sorry, the chat service is temporarily unavailable.",
                error="No chat agent available"
            )

        # Create event
        event = AgentEvent(
            event_type=EventType.USER_MESSAGE,
            payload={"message": message},
            user_id=user_id,
            metadata={"conversation_id": conversation_id}
        )

        # Create context
        context = AgentContext(
            event=event,
            conversation_id=conversation_id,
            db=db,
        )
        context.add_message(message, MessageRole.USER)

        # Execute primary chat agent
        return await self._execute_agent(chat_agents[0], context)

    async def get_recommendations(
        self,
        user_id: str,
        task_id: Optional[str] = None,
        db: Optional["AsyncSession"] = None
    ) -> Dict[str, Any]:
        """
        Get AI recommendations for a user.

        Aggregates recommendations from multiple agents.
        """
        recommendations = {
            "tasks": [],
            "unblock_suggestions": [],
            "skill_recommendations": [],
            "productivity_tips": [],
        }

        # Create context
        context = AgentContext(
            db=db,
            metadata={"user_id": user_id, "task_id": task_id}
        )

        # Run recommendation agents in parallel
        agent_names = ["predictor_agent", "skill_matcher_agent", "coach_agent"]
        available_agents = [
            name for name in agent_names
            if self.get_agent(name)
        ]

        if available_agents:
            results = await self.run_parallel(available_agents, context)
            for result in results:
                if result.success and result.output:
                    recommendations.update(result.output)

        return recommendations

    async def _find_handlers(self, event: AgentEvent) -> List[BaseAgent]:
        """Find all agents that can handle an event"""
        handlers = []

        # Check specific target first
        if event.target_agent:
            agent = self.get_agent(event.target_agent)
            if agent and agent.enabled:
                handlers.append(agent)
            return handlers

        # Find all agents that handle this event type
        for registration in self._agents.values():
            agent = registration.agent
            if (
                agent.enabled
                and event.event_type in agent.handled_events
                and await agent.can_handle(event)
            ):
                handlers.append(agent)

        # Sort by priority
        handlers.sort(key=lambda a: a.priority)

        return handlers

    async def _execute_agent(
        self,
        agent: BaseAgent,
        context: AgentContext
    ) -> AgentResult:
        """Execute a single agent with full lifecycle handling"""
        record = ExecutionRecord(
            agent_name=agent.name,
            event_type=context.event.event_type.value if context.event else "direct",
            context_id=context.id,
        )

        try:
            # Validation
            await agent.validate(context)

            # Before hook
            await agent.before_execute(context)

            if self._on_execution_start:
                await self._on_execution_start(agent, context)

            # Execute
            result = await agent.execute(context)
            result.complete(success=True)

            # After hook
            await agent.after_execute(context, result)

            record.success = True
            record.result_summary = {
                "message": result.message,
                "actions_count": len(result.actions),
            }

        except Exception as e:
            logger.error(f"Agent execution error ({agent.name}): {e}")
            result = await agent.on_error(context, e)
            record.error = str(e)

        finally:
            record.completed_at = datetime.utcnow()
            record.duration_ms = int(
                (record.completed_at - record.started_at).total_seconds() * 1000
            )

            # Update registration stats
            if agent.name in self._agents:
                self._agents[agent.name].execution_count += 1
                self._agents[agent.name].last_execution = record.completed_at

            self._record_execution(record)

            if self._on_execution_complete:
                await self._on_execution_complete(agent, context, result)

        return result

    async def _handle_follow_ups(
        self,
        events: List[AgentEvent],
        parent_event: AgentEvent
    ) -> None:
        """Handle follow-up events from agent execution"""
        for event in events:
            # Check chain depth
            if event.chain_depth >= self._max_chain_depth:
                logger.warning(
                    f"Max chain depth reached for event: {event.id}"
                )
                continue

            # Set chain information
            event.parent_event_id = parent_event.id
            event.chain_depth = parent_event.chain_depth + 1

            # Publish to event bus
            await self._event_bus.publish(event, EventPriority.NORMAL)

    def _record_execution(self, record: ExecutionRecord) -> None:
        """Record execution in history"""
        self._execution_history.append(record)
        if len(self._execution_history) > self._max_history:
            self._execution_history = self._execution_history[-self._max_history:]

    def get_stats(self) -> Dict[str, Any]:
        """Get orchestrator statistics"""
        return {
            "registered_agents": len(self._agents),
            "agents": {
                name: {
                    "status": reg.agent.status.value,
                    "enabled": reg.agent.enabled,
                    "capabilities": [c.value for c in reg.agent.capabilities],
                    "execution_count": reg.execution_count,
                    "last_execution": reg.last_execution.isoformat() if reg.last_execution else None,
                }
                for name, reg in self._agents.items()
            },
            "capabilities": {
                cap.value: len(agents)
                for cap, agents in self._capability_index.items()
            },
            "recent_executions": len(self._execution_history),
            "event_bus": self._event_bus.get_stats(),
        }

    def get_execution_history(
        self,
        limit: int = 50,
        agent_name: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """Get recent execution history"""
        history = self._execution_history

        if agent_name:
            history = [r for r in history if r.agent_name == agent_name]

        return [
            {
                "id": r.id,
                "agent_name": r.agent_name,
                "event_type": r.event_type,
                "started_at": r.started_at.isoformat(),
                "completed_at": r.completed_at.isoformat() if r.completed_at else None,
                "duration_ms": r.duration_ms,
                "success": r.success,
                "error": r.error,
            }
            for r in list(reversed(history))[:limit]
        ]

    def on_execution_start(self, callback: Callable) -> None:
        """Register callback for execution start"""
        self._on_execution_start = callback

    def on_execution_complete(self, callback: Callable) -> None:
        """Register callback for execution complete"""
        self._on_execution_complete = callback


# Global orchestrator instance
_orchestrator: Optional[AgentOrchestrator] = None


def get_orchestrator() -> AgentOrchestrator:
    """Get the global orchestrator instance"""
    global _orchestrator
    if _orchestrator is None:
        _orchestrator = AgentOrchestrator()
    return _orchestrator


async def init_orchestrator() -> AgentOrchestrator:
    """Initialize the global orchestrator with default agents"""
    from .event_bus import init_event_bus

    # Start event bus
    await init_event_bus()

    # Get or create orchestrator
    orchestrator = get_orchestrator()

    # Register default agents (lazy import to avoid circular deps)
    try:
        from .conversation.chat_agent import ChatAgent
        from .unblock_agent import UnblockAgent
        from .decomposer_agent import DecomposerAgent
        from .predictor_agent import PredictorAgent
        from .skill_matcher_agent import SkillMatcherAgent
        from .coach_agent import CoachAgent

        orchestrator.register(ChatAgent)
        orchestrator.register(UnblockAgent)
        orchestrator.register(DecomposerAgent)
        orchestrator.register(PredictorAgent)
        orchestrator.register(SkillMatcherAgent)
        orchestrator.register(CoachAgent)
    except ImportError as e:
        logger.warning(f"Some agents not available: {e}")

    logger.info("Agent orchestrator initialized")
    return orchestrator


async def shutdown_orchestrator() -> None:
    """Shutdown the global orchestrator"""
    from .event_bus import shutdown_event_bus

    global _orchestrator
    if _orchestrator:
        await shutdown_event_bus()
        _orchestrator = None

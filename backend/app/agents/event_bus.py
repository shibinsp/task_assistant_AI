"""
Agent Event Bus

Provides event-driven communication between agents, enabling
loose coupling and complex multi-agent workflows.
"""

import asyncio
import logging
from collections import defaultdict
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Callable, Dict, List, Optional, Set, TYPE_CHECKING
from uuid import uuid4

if TYPE_CHECKING:
    from .base import BaseAgent, AgentEvent

logger = logging.getLogger(__name__)


class EventPriority(int, Enum):
    """Priority levels for event processing"""
    CRITICAL = 0
    HIGH = 1
    NORMAL = 2
    LOW = 3


class EventStatus(str, Enum):
    """Status of an event in the queue"""
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


# Re-export EventType from base for convenience
from .base import EventType


@dataclass
class EventSubscription:
    """Subscription record for an agent"""
    agent_name: str
    event_types: Set[EventType]
    handler: Callable
    priority: int = 100
    filter_fn: Optional[Callable[["AgentEvent"], bool]] = None
    created_at: datetime = field(default_factory=datetime.utcnow)


@dataclass
class QueuedEvent:
    """Event waiting to be processed"""
    event: "AgentEvent"
    priority: EventPriority = EventPriority.NORMAL
    status: EventStatus = EventStatus.PENDING
    queued_at: datetime = field(default_factory=datetime.utcnow)
    processed_at: Optional[datetime] = None
    attempts: int = 0
    max_attempts: int = 3
    error: Optional[str] = None

    def __lt__(self, other: "QueuedEvent") -> bool:
        """For priority queue comparison"""
        if self.priority != other.priority:
            return self.priority.value < other.priority.value
        return self.queued_at < other.queued_at


class AgentEventBus:
    """
    Central event bus for agent communication.

    Manages event subscriptions, publishing, and routing.
    Supports priority-based processing and event filtering.

    Example:
        bus = AgentEventBus()

        # Subscribe an agent
        await bus.subscribe(my_agent, [EventType.TASK_CREATED])

        # Publish an event
        await bus.publish(AgentEvent(event_type=EventType.TASK_CREATED))
    """

    def __init__(self, max_queue_size: int = 10000):
        self._subscriptions: Dict[str, EventSubscription] = {}
        self._event_handlers: Dict[EventType, List[EventSubscription]] = defaultdict(list)
        self._event_queue: asyncio.PriorityQueue = asyncio.PriorityQueue(maxsize=max_queue_size)
        self._event_history: List[QueuedEvent] = []
        self._max_history: int = 1000
        self._running: bool = False
        self._processor_task: Optional[asyncio.Task] = None
        self._lock = asyncio.Lock()

        # Metrics
        self._events_published: int = 0
        self._events_processed: int = 0
        self._events_failed: int = 0

    async def subscribe(
        self,
        agent: "BaseAgent",
        event_types: Optional[List[EventType]] = None,
        priority: int = 100,
        filter_fn: Optional[Callable[["AgentEvent"], bool]] = None
    ) -> str:
        """
        Subscribe an agent to specific event types.

        Args:
            agent: The agent to subscribe
            event_types: List of event types to subscribe to (uses agent.handled_events if None)
            priority: Processing priority (lower = higher priority)
            filter_fn: Optional function to filter events

        Returns:
            Subscription ID
        """
        event_types = event_types or agent.handled_events

        async with self._lock:
            subscription = EventSubscription(
                agent_name=agent.name,
                event_types=set(event_types),
                handler=agent.execute,
                priority=priority,
                filter_fn=filter_fn,
            )

            self._subscriptions[agent.name] = subscription

            # Index by event type for fast lookup
            for event_type in event_types:
                handlers = self._event_handlers[event_type]
                handlers.append(subscription)
                # Keep sorted by priority
                handlers.sort(key=lambda s: s.priority)

            logger.info(
                f"Agent '{agent.name}' subscribed to events: {[e.value for e in event_types]}"
            )

            return agent.name

    async def unsubscribe(self, agent_name: str) -> bool:
        """
        Unsubscribe an agent from all events.

        Args:
            agent_name: Name of the agent to unsubscribe

        Returns:
            True if the agent was subscribed
        """
        async with self._lock:
            subscription = self._subscriptions.pop(agent_name, None)
            if subscription:
                for event_type in subscription.event_types:
                    self._event_handlers[event_type] = [
                        s for s in self._event_handlers[event_type]
                        if s.agent_name != agent_name
                    ]
                logger.info(f"Agent '{agent_name}' unsubscribed")
                return True
            return False

    async def publish(
        self,
        event: "AgentEvent",
        priority: EventPriority = EventPriority.NORMAL
    ) -> str:
        """
        Publish an event to the bus.

        Args:
            event: The event to publish
            priority: Processing priority

        Returns:
            Event ID
        """
        queued = QueuedEvent(event=event, priority=priority)

        try:
            await self._event_queue.put((priority.value, queued))
            self._events_published += 1
            logger.debug(f"Event published: {event.event_type.value} (id={event.id})")
        except asyncio.QueueFull:
            logger.error(f"Event queue full, dropping event: {event.id}")
            raise RuntimeError("Event queue is full")

        return event.id

    async def publish_immediate(
        self,
        event: "AgentEvent"
    ) -> List[Any]:
        """
        Publish and immediately process an event (synchronous).

        Args:
            event: The event to process

        Returns:
            List of results from handlers
        """
        handlers = self._get_handlers_for_event(event)
        results = []

        for subscription in handlers:
            try:
                result = await subscription.handler(event)
                results.append(result)
            except Exception as e:
                logger.error(f"Handler error for {subscription.agent_name}: {e}")
                results.append({"error": str(e), "agent": subscription.agent_name})

        return results

    def _get_handlers_for_event(
        self,
        event: "AgentEvent"
    ) -> List[EventSubscription]:
        """Get all handlers that should process this event"""
        handlers = self._event_handlers.get(event.event_type, [])

        # Apply filters
        filtered = []
        for subscription in handlers:
            if subscription.filter_fn:
                try:
                    if subscription.filter_fn(event):
                        filtered.append(subscription)
                except Exception as e:
                    logger.warning(f"Filter error for {subscription.agent_name}: {e}")
            else:
                filtered.append(subscription)

        # Check target agent if specified
        if event.target_agent:
            filtered = [s for s in filtered if s.agent_name == event.target_agent]

        return filtered

    async def start_processing(self) -> None:
        """Start the background event processor"""
        if self._running:
            return

        self._running = True
        self._processor_task = asyncio.create_task(self._process_loop())
        logger.info("Event bus processor started")

    async def stop_processing(self) -> None:
        """Stop the background event processor"""
        self._running = False
        if self._processor_task:
            self._processor_task.cancel()
            try:
                await self._processor_task
            except asyncio.CancelledError:
                pass
        logger.info("Event bus processor stopped")

    async def _process_loop(self) -> None:
        """Main processing loop"""
        while self._running:
            try:
                # Wait for next event with timeout
                try:
                    priority, queued = await asyncio.wait_for(
                        self._event_queue.get(),
                        timeout=1.0
                    )
                except asyncio.TimeoutError:
                    continue

                await self._process_event(queued)

            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in event processing loop: {e}")
                await asyncio.sleep(0.1)

    async def _process_event(self, queued: QueuedEvent) -> None:
        """Process a single event"""
        queued.status = EventStatus.PROCESSING
        queued.attempts += 1
        event = queued.event

        handlers = self._get_handlers_for_event(event)

        if not handlers:
            logger.debug(f"No handlers for event: {event.event_type.value}")
            queued.status = EventStatus.COMPLETED
            self._record_history(queued)
            return

        try:
            for subscription in handlers:
                try:
                    await subscription.handler(event)
                except Exception as e:
                    logger.error(
                        f"Handler error for {subscription.agent_name} "
                        f"on event {event.id}: {e}"
                    )
                    if queued.attempts >= queued.max_attempts:
                        raise

            queued.status = EventStatus.COMPLETED
            queued.processed_at = datetime.utcnow()
            self._events_processed += 1

        except Exception as e:
            if queued.attempts < queued.max_attempts:
                # Retry
                queued.status = EventStatus.PENDING
                queued.error = str(e)
                await self._event_queue.put((queued.priority.value, queued))
            else:
                queued.status = EventStatus.FAILED
                queued.error = str(e)
                self._events_failed += 1
                logger.error(f"Event {event.id} failed after {queued.attempts} attempts: {e}")

        self._record_history(queued)

    def _record_history(self, queued: QueuedEvent) -> None:
        """Record event in history"""
        self._event_history.append(queued)
        # Trim history
        if len(self._event_history) > self._max_history:
            self._event_history = self._event_history[-self._max_history:]

    async def get_pending_count(self) -> int:
        """Get number of pending events"""
        return self._event_queue.qsize()

    def get_stats(self) -> Dict[str, Any]:
        """Get event bus statistics"""
        return {
            "running": self._running,
            "subscriptions": len(self._subscriptions),
            "pending_events": self._event_queue.qsize(),
            "events_published": self._events_published,
            "events_processed": self._events_processed,
            "events_failed": self._events_failed,
            "event_types": {
                event_type.value: len(handlers)
                for event_type, handlers in self._event_handlers.items()
            },
        }

    def get_subscriptions(self) -> List[Dict[str, Any]]:
        """Get all active subscriptions"""
        return [
            {
                "agent_name": sub.agent_name,
                "event_types": [e.value for e in sub.event_types],
                "priority": sub.priority,
                "created_at": sub.created_at.isoformat(),
            }
            for sub in self._subscriptions.values()
        ]

    async def clear_queue(self) -> int:
        """Clear all pending events. Returns count of cleared events."""
        count = 0
        while not self._event_queue.empty():
            try:
                self._event_queue.get_nowait()
                count += 1
            except asyncio.QueueEmpty:
                break
        return count


# Global event bus instance
_event_bus: Optional[AgentEventBus] = None


def get_event_bus() -> AgentEventBus:
    """Get the global event bus instance"""
    global _event_bus
    if _event_bus is None:
        _event_bus = AgentEventBus()
    return _event_bus


async def init_event_bus() -> AgentEventBus:
    """Initialize and start the global event bus"""
    bus = get_event_bus()
    await bus.start_processing()
    return bus


async def shutdown_event_bus() -> None:
    """Shutdown the global event bus"""
    global _event_bus
    if _event_bus:
        await _event_bus.stop_processing()
        _event_bus = None

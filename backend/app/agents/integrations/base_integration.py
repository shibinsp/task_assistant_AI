"""
Base Integration Agent

Abstract base class for all external integration agents.
Provides common functionality for OAuth, webhooks, and sync operations.
"""

import logging
from abc import abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional, TYPE_CHECKING

from ..base import (
    AgentCapability,
    AgentEvent,
    AgentResult,
    BaseAgent,
    EventType,
)
from ..context import AgentContext

if TYPE_CHECKING:
    pass

logger = logging.getLogger(__name__)


class IntegrationStatus(str, Enum):
    """Status of an integration connection"""
    PENDING = "pending"
    CONNECTED = "connected"
    SYNCING = "syncing"
    ERROR = "error"
    DISCONNECTED = "disconnected"


class SyncDirection(str, Enum):
    """Direction of data sync"""
    INBOUND = "inbound"  # External → TaskPulse
    OUTBOUND = "outbound"  # TaskPulse → External
    BIDIRECTIONAL = "bidirectional"


@dataclass
class SyncResult:
    """Result of a sync operation"""
    success: bool
    direction: SyncDirection
    items_synced: int = 0
    items_created: int = 0
    items_updated: int = 0
    items_failed: int = 0
    errors: List[str] = field(default_factory=list)
    started_at: datetime = field(default_factory=datetime.utcnow)
    completed_at: Optional[datetime] = None
    duration_ms: Optional[int] = None

    def complete(self):
        self.completed_at = datetime.utcnow()
        self.duration_ms = int(
            (self.completed_at - self.started_at).total_seconds() * 1000
        )


@dataclass
class ExternalItem:
    """Represents an item from an external system"""
    external_id: str
    title: str
    description: Optional[str] = None
    status: Optional[str] = None
    external_url: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


@dataclass
class WebhookEvent:
    """Incoming webhook event from external system"""
    source: str
    event_type: str
    payload: Dict[str, Any]
    signature: Optional[str] = None
    timestamp: datetime = field(default_factory=datetime.utcnow)


class BaseIntegrationAgent(BaseAgent):
    """
    Abstract base class for external integration agents.

    Provides:
    - OAuth connection management
    - Webhook handling
    - Inbound/outbound sync
    - Error handling and retry logic
    """

    # Integration type identifier
    integration_type: str = "base"

    # Sync configuration
    sync_direction: SyncDirection = SyncDirection.BIDIRECTIONAL
    sync_interval_minutes: int = 15

    # API configuration
    api_base_url: str = ""
    api_version: str = "v1"

    handled_events = [
        EventType.INTEGRATION_WEBHOOK,
        EventType.SYNC_REQUESTED,
        EventType.SCHEDULED,
    ]

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        super().__init__(config)
        self.credentials: Dict[str, str] = {}
        self.connection_status = IntegrationStatus.PENDING
        self._last_sync: Optional[datetime] = None
        self._sync_cursor: Optional[str] = None

    async def can_handle(self, event: AgentEvent) -> bool:
        """Check if this agent should handle the event"""
        if event.event_type == EventType.INTEGRATION_WEBHOOK:
            return event.payload.get("integration_type") == self.integration_type

        if event.event_type == EventType.SYNC_REQUESTED:
            return event.payload.get("integration_type") == self.integration_type

        if event.event_type == EventType.SCHEDULED:
            return (
                event.payload.get("job_type") == "integration_sync" and
                event.payload.get("integration_type") == self.integration_type
            )

        return False

    async def execute(self, context: AgentContext) -> AgentResult:
        """Execute integration action based on event type"""
        result = AgentResult(
            success=True,
            agent_name=self.name,
            event_id=context.event.id if context.event else "direct"
        )

        try:
            event = context.event

            if event.event_type == EventType.INTEGRATION_WEBHOOK:
                webhook_result = await self.handle_webhook(
                    WebhookEvent(
                        source=self.integration_type,
                        event_type=event.payload.get("webhook_event", ""),
                        payload=event.payload.get("data", {}),
                        signature=event.payload.get("signature"),
                    )
                )
                result.output = {"webhook_result": webhook_result}
                result.message = f"Processed webhook: {event.payload.get('webhook_event')}"

            elif event.event_type in [EventType.SYNC_REQUESTED, EventType.SCHEDULED]:
                sync_result = await self.sync(context)
                result.output = {
                    "sync_result": {
                        "success": sync_result.success,
                        "items_synced": sync_result.items_synced,
                        "direction": sync_result.direction.value,
                        "duration_ms": sync_result.duration_ms,
                    }
                }
                result.message = f"Synced {sync_result.items_synced} items"

            result.actions = [
                {"type": "integration_action", "integration": self.integration_type}
            ]

        except Exception as e:
            logger.error(f"Integration agent error ({self.name}): {e}")
            result.success = False
            result.error = str(e)
            self.connection_status = IntegrationStatus.ERROR

        return result

    async def sync(self, context: AgentContext) -> SyncResult:
        """Perform sync operation"""
        sync_result = SyncResult(
            success=True,
            direction=self.sync_direction
        )

        try:
            if self.sync_direction in [SyncDirection.INBOUND, SyncDirection.BIDIRECTIONAL]:
                inbound = await self.sync_inbound(context)
                sync_result.items_synced += len(inbound)
                sync_result.items_created += len([i for i in inbound if i.get("is_new")])

            if self.sync_direction in [SyncDirection.OUTBOUND, SyncDirection.BIDIRECTIONAL]:
                outbound_result = await self.sync_outbound(context)
                sync_result.items_synced += outbound_result.get("count", 0)
                sync_result.items_updated += outbound_result.get("updated", 0)

            self._last_sync = datetime.utcnow()
            self.connection_status = IntegrationStatus.CONNECTED

        except Exception as e:
            sync_result.success = False
            sync_result.errors.append(str(e))
            self.connection_status = IntegrationStatus.ERROR

        sync_result.complete()
        return sync_result

    @abstractmethod
    async def sync_inbound(self, context: AgentContext) -> List[Dict[str, Any]]:
        """
        Sync data from external system to TaskPulse.

        Returns list of synced items.
        """
        pass

    @abstractmethod
    async def sync_outbound(self, context: AgentContext) -> Dict[str, Any]:
        """
        Sync data from TaskPulse to external system.

        Returns sync statistics.
        """
        pass

    @abstractmethod
    async def handle_webhook(self, event: WebhookEvent) -> Dict[str, Any]:
        """
        Handle incoming webhook from external system.

        Returns processing result.
        """
        pass

    async def validate_connection(self) -> bool:
        """Validate that the connection is still active"""
        # Override in subclasses to implement actual validation
        return self.connection_status == IntegrationStatus.CONNECTED

    async def refresh_credentials(self) -> bool:
        """Refresh OAuth credentials if needed"""
        # Override in subclasses to implement token refresh
        return True

    def get_integration_info(self) -> Dict[str, Any]:
        """Get integration status and info"""
        return {
            "type": self.integration_type,
            "status": self.connection_status.value,
            "last_sync": self._last_sync.isoformat() if self._last_sync else None,
            "sync_direction": self.sync_direction.value,
            "api_version": self.api_version,
        }


class MockIntegrationAgent(BaseIntegrationAgent):
    """Mock integration for testing"""

    integration_type = "mock"
    name = "mock_integration_agent"
    description = "Mock integration for testing"

    capabilities = []

    async def sync_inbound(self, context: AgentContext) -> List[Dict[str, Any]]:
        return [{"id": "mock_1", "title": "Mock Item", "is_new": True}]

    async def sync_outbound(self, context: AgentContext) -> Dict[str, Any]:
        return {"count": 1, "updated": 1}

    async def handle_webhook(self, event: WebhookEvent) -> Dict[str, Any]:
        return {"processed": True, "event_type": event.event_type}

"""
TaskPulse - AI Assistant - Integration Service
Third-party integrations and webhooks
"""

from typing import Optional, List, Dict, Any
from datetime import datetime, timedelta
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
import hashlib
import hmac
import json

from app.models.notification import (
    Integration, IntegrationType, IntegrationStatus,
    Webhook, WebhookDelivery
)
from app.utils.helpers import generate_uuid


class IntegrationService:
    """Service for managing integrations and webhooks."""

    def __init__(self, db: AsyncSession):
        self.db = db

    # ==================== Integrations ====================

    async def create_integration(
        self,
        org_id: str,
        integration_type: IntegrationType,
        name: str,
        config: Dict[str, Any],
        created_by: str
    ) -> Integration:
        """Create a new integration."""
        integration = Integration(
            id=generate_uuid(),
            org_id=org_id,
            integration_type=integration_type,
            name=name,
            status=IntegrationStatus.PENDING,
            created_by=created_by
        )
        integration.config = config

        self.db.add(integration)
        await self.db.flush()
        await self.db.refresh(integration)

        return integration

    async def get_integration(
        self,
        integration_id: str,
        org_id: str
    ) -> Optional[Integration]:
        """Get an integration by ID."""
        result = await self.db.execute(
            select(Integration).where(
                Integration.id == integration_id,
                Integration.org_id == org_id
            )
        )
        return result.scalar_one_or_none()

    async def get_integrations(
        self,
        org_id: str,
        integration_type: Optional[IntegrationType] = None,
        status: Optional[IntegrationStatus] = None
    ) -> List[Integration]:
        """Get all integrations for an organization."""
        query = select(Integration).where(Integration.org_id == org_id)

        if integration_type:
            query = query.where(Integration.integration_type == integration_type)
        if status:
            query = query.where(Integration.status == status)

        result = await self.db.execute(query.order_by(Integration.created_at.desc()))
        return list(result.scalars().all())

    async def update_integration_status(
        self,
        integration_id: str,
        org_id: str,
        status: IntegrationStatus,
        error_message: Optional[str] = None
    ) -> Optional[Integration]:
        """Update integration status."""
        integration = await self.get_integration(integration_id, org_id)

        if integration:
            integration.status = status
            if status == IntegrationStatus.ACTIVE:
                integration.connected_at = datetime.utcnow()
            if error_message:
                integration.error_message = error_message
            else:
                integration.error_message = None

            await self.db.flush()

        return integration

    async def delete_integration(
        self,
        integration_id: str,
        org_id: str
    ) -> bool:
        """Delete an integration."""
        integration = await self.get_integration(integration_id, org_id)

        if integration:
            await self.db.delete(integration)
            await self.db.flush()
            return True

        return False

    async def sync_integration(
        self,
        integration_id: str,
        org_id: str
    ) -> Dict[str, Any]:
        """Trigger sync for an integration."""
        integration = await self.get_integration(integration_id, org_id)

        if not integration:
            return {"success": False, "error": "Integration not found"}

        if integration.status != IntegrationStatus.ACTIVE:
            return {"success": False, "error": "Integration not active"}

        # Perform sync based on type
        sync_result = await self._perform_sync(integration)

        # Update last sync time
        integration.last_sync_at = datetime.utcnow()
        integration.sync_status = "completed" if sync_result["success"] else "failed"
        await self.db.flush()

        return sync_result

    async def _perform_sync(self, integration: Integration) -> Dict[str, Any]:
        """Perform sync for specific integration type."""
        if integration.integration_type == IntegrationType.JIRA:
            return await self._sync_jira(integration)
        elif integration.integration_type == IntegrationType.GITHUB:
            return await self._sync_github(integration)
        elif integration.integration_type == IntegrationType.SLACK:
            return await self._sync_slack(integration)
        else:
            return {"success": True, "message": "No sync required", "items_synced": 0}

    async def _sync_jira(self, integration: Integration) -> Dict[str, Any]:
        """Sync with Jira (stub)."""
        # In production, this would use Jira API
        return {
            "success": True,
            "message": "Jira sync completed",
            "items_synced": 0,
            "details": {
                "issues_imported": 0,
                "issues_updated": 0
            }
        }

    async def _sync_github(self, integration: Integration) -> Dict[str, Any]:
        """Sync with GitHub (stub)."""
        return {
            "success": True,
            "message": "GitHub sync completed",
            "items_synced": 0,
            "details": {
                "issues_imported": 0,
                "prs_imported": 0
            }
        }

    async def _sync_slack(self, integration: Integration) -> Dict[str, Any]:
        """Sync with Slack (stub)."""
        return {
            "success": True,
            "message": "Slack connection verified",
            "items_synced": 0
        }

    # ==================== OAuth Flow ====================

    async def initiate_oauth(
        self,
        org_id: str,
        integration_type: IntegrationType,
        redirect_uri: str
    ) -> Dict[str, Any]:
        """Initiate OAuth flow for an integration."""
        # Generate state token
        state = generate_uuid()

        # Store state for verification
        # In production, this would be stored in cache/session

        oauth_urls = {
            IntegrationType.JIRA: "https://auth.atlassian.com/authorize",
            IntegrationType.GITHUB: "https://github.com/login/oauth/authorize",
            IntegrationType.GITLAB: "https://gitlab.com/oauth/authorize",
            IntegrationType.SLACK: "https://slack.com/oauth/v2/authorize",
        }

        base_url = oauth_urls.get(integration_type)
        if not base_url:
            return {"error": "OAuth not supported for this integration type"}

        return {
            "auth_url": f"{base_url}?state={state}&redirect_uri={redirect_uri}",
            "state": state,
            "message": "Redirect user to auth_url to complete OAuth"
        }

    async def complete_oauth(
        self,
        org_id: str,
        integration_type: IntegrationType,
        code: str,
        state: str,
        created_by: str
    ) -> Optional[Integration]:
        """Complete OAuth flow and create integration."""
        # In production, exchange code for tokens
        # Verify state matches stored state

        # Create integration with tokens
        integration = await self.create_integration(
            org_id=org_id,
            integration_type=integration_type,
            name=f"{integration_type.value.title()} Integration",
            config={
                "oauth_completed": True,
                "access_token": "mock_token",  # Would be real token
                "refresh_token": "mock_refresh"
            },
            created_by=created_by
        )

        # Mark as active
        await self.update_integration_status(
            integration.id, org_id, IntegrationStatus.ACTIVE
        )

        return integration

    # ==================== Webhooks ====================

    async def create_webhook(
        self,
        org_id: str,
        name: str,
        url: str,
        events: List[str],
        created_by: str,
        secret: Optional[str] = None,
        headers: Optional[Dict[str, str]] = None
    ) -> Webhook:
        """Create a new webhook."""
        webhook = Webhook(
            id=generate_uuid(),
            org_id=org_id,
            name=name,
            url=url,
            secret=secret or generate_uuid(),
            is_active=True,
            created_by=created_by
        )
        webhook.events = events
        webhook.headers = headers or {}

        self.db.add(webhook)
        await self.db.flush()
        await self.db.refresh(webhook)

        return webhook

    async def get_webhook(
        self,
        webhook_id: str,
        org_id: str
    ) -> Optional[Webhook]:
        """Get a webhook by ID."""
        result = await self.db.execute(
            select(Webhook).where(
                Webhook.id == webhook_id,
                Webhook.org_id == org_id
            )
        )
        return result.scalar_one_or_none()

    async def get_webhooks(
        self,
        org_id: str,
        active_only: bool = False
    ) -> List[Webhook]:
        """Get all webhooks for an organization."""
        query = select(Webhook).where(Webhook.org_id == org_id)

        if active_only:
            query = query.where(Webhook.is_active == True)

        result = await self.db.execute(query.order_by(Webhook.created_at.desc()))
        return list(result.scalars().all())

    async def update_webhook(
        self,
        webhook_id: str,
        org_id: str,
        updates: Dict[str, Any]
    ) -> Optional[Webhook]:
        """Update a webhook."""
        webhook = await self.get_webhook(webhook_id, org_id)

        if webhook:
            if "name" in updates:
                webhook.name = updates["name"]
            if "url" in updates:
                webhook.url = updates["url"]
            if "events" in updates:
                webhook.events = updates["events"]
            if "headers" in updates:
                webhook.headers = updates["headers"]
            if "is_active" in updates:
                webhook.is_active = updates["is_active"]

            await self.db.flush()

        return webhook

    async def delete_webhook(
        self,
        webhook_id: str,
        org_id: str
    ) -> bool:
        """Delete a webhook."""
        webhook = await self.get_webhook(webhook_id, org_id)

        if webhook:
            await self.db.delete(webhook)
            await self.db.flush()
            return True

        return False

    async def trigger_webhook(
        self,
        org_id: str,
        event_type: str,
        payload: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """Trigger webhooks for an event."""
        # Get active webhooks subscribed to this event
        webhooks = await self.get_webhooks(org_id, active_only=True)
        subscribed = [w for w in webhooks if event_type in (w.events or [])]

        results = []
        for webhook in subscribed:
            delivery = await self._deliver_webhook(webhook, event_type, payload)
            results.append({
                "webhook_id": webhook.id,
                "delivery_id": delivery.id,
                "success": delivery.success
            })

        return results

    async def _deliver_webhook(
        self,
        webhook: Webhook,
        event_type: str,
        payload: Dict[str, Any]
    ) -> WebhookDelivery:
        """Deliver a webhook and record the result."""
        delivery = WebhookDelivery(
            id=generate_uuid(),
            org_id=webhook.org_id,
            webhook_id=webhook.id,
            event_type=event_type
        )
        delivery.payload = payload

        # Generate signature
        signature = self._generate_signature(webhook.secret, payload)

        # Attempt delivery
        try:
            # In production, this would make actual HTTP request
            # import httpx
            # async with httpx.AsyncClient() as client:
            #     response = await client.post(
            #         webhook.url,
            #         json=payload,
            #         headers={
            #             "X-Webhook-Signature": signature,
            #             "X-Webhook-Event": event_type,
            #             **webhook.headers
            #         }
            #     )

            # Mock successful delivery
            delivery.success = True
            delivery.response_status = 200
            delivery.response_body = '{"received": true}'

            # Update webhook stats
            webhook.delivery_count = (webhook.delivery_count or 0) + 1
            webhook.last_delivery_at = datetime.utcnow()

        except Exception as e:
            delivery.success = False
            delivery.response_status = 0
            delivery.error_message = str(e)

            # Update failure count
            webhook.failure_count = (webhook.failure_count or 0) + 1
            webhook.last_failure_at = datetime.utcnow()

        self.db.add(delivery)
        await self.db.flush()

        return delivery

    def _generate_signature(
        self,
        secret: str,
        payload: Dict[str, Any]
    ) -> str:
        """Generate HMAC signature for webhook payload."""
        payload_bytes = json.dumps(payload, sort_keys=True).encode()
        signature = hmac.new(
            secret.encode(),
            payload_bytes,
            hashlib.sha256
        ).hexdigest()
        return f"sha256={signature}"

    async def get_webhook_deliveries(
        self,
        webhook_id: str,
        org_id: str,
        limit: int = 50
    ) -> List[WebhookDelivery]:
        """Get delivery logs for a webhook."""
        result = await self.db.execute(
            select(WebhookDelivery).where(
                WebhookDelivery.webhook_id == webhook_id,
                WebhookDelivery.org_id == org_id
            ).order_by(WebhookDelivery.created_at.desc()).limit(limit)
        )
        return list(result.scalars().all())

    async def retry_delivery(
        self,
        delivery_id: str,
        org_id: str
    ) -> Optional[WebhookDelivery]:
        """Retry a failed webhook delivery."""
        result = await self.db.execute(
            select(WebhookDelivery).where(
                WebhookDelivery.id == delivery_id,
                WebhookDelivery.org_id == org_id
            )
        )
        original = result.scalar_one_or_none()

        if not original or original.success:
            return None

        webhook = await self.get_webhook(original.webhook_id, org_id)
        if not webhook:
            return None

        # Create new delivery attempt
        return await self._deliver_webhook(
            webhook,
            original.event_type,
            original.payload or {}
        )

    async def test_webhook(
        self,
        webhook_id: str,
        org_id: str
    ) -> Dict[str, Any]:
        """Send a test event to a webhook."""
        webhook = await self.get_webhook(webhook_id, org_id)

        if not webhook:
            return {"success": False, "error": "Webhook not found"}

        test_payload = {
            "event": "test",
            "message": "This is a test webhook delivery",
            "timestamp": datetime.utcnow().isoformat(),
            "webhook_id": webhook_id
        }

        delivery = await self._deliver_webhook(webhook, "test", test_payload)

        return {
            "success": delivery.success,
            "delivery_id": delivery.id,
            "response_status": delivery.response_status,
            "message": "Test delivery successful" if delivery.success else delivery.error_message
        }

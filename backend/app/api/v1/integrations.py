"""
TaskPulse - AI Assistant - Integrations API
Third-party integrations and webhooks endpoints
"""

from typing import Optional, List
from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import datetime

from app.database import get_db
from app.models.user import User, UserRole
from app.models.notification import IntegrationType, IntegrationStatus
from app.services.integration_service import IntegrationService
from app.api.v1.dependencies import get_current_active_user, require_roles
from app.core.permissions import Permission, has_permission
from app.core.exceptions import NotFoundException, ForbiddenException
from pydantic import BaseModel, Field, HttpUrl

router = APIRouter()


# Schemas
class IntegrationCreate(BaseModel):
    integration_type: IntegrationType
    name: str = Field(..., min_length=1, max_length=200)
    config: dict = Field(default_factory=dict)


class IntegrationResponse(BaseModel):
    id: str
    integration_type: IntegrationType
    name: str
    status: IntegrationStatus
    connected_at: Optional[datetime]
    last_sync_at: Optional[datetime]
    sync_status: Optional[str]
    error_message: Optional[str]
    created_at: datetime

    class Config:
        from_attributes = True


class WebhookCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=200)
    url: str = Field(..., description="Webhook endpoint URL")
    events: List[str] = Field(..., min_length=1, description="Events to subscribe to")
    secret: Optional[str] = Field(None, description="Webhook secret for signature verification")
    headers: Optional[dict] = Field(default_factory=dict)


class WebhookUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=200)
    url: Optional[str] = None
    events: Optional[List[str]] = None
    headers: Optional[dict] = None
    is_active: Optional[bool] = None


class WebhookResponse(BaseModel):
    id: str
    name: str
    url: str
    events: List[str]
    is_active: bool
    delivery_count: int
    failure_count: int
    last_delivery_at: Optional[datetime]
    last_failure_at: Optional[datetime]
    created_at: datetime

    class Config:
        from_attributes = True


class WebhookDeliveryResponse(BaseModel):
    id: str
    event_type: str
    success: bool
    response_status: Optional[int]
    error_message: Optional[str]
    created_at: datetime

    class Config:
        from_attributes = True


def get_integration_service(db: AsyncSession = Depends(get_db)) -> IntegrationService:
    return IntegrationService(db)


# Integration Endpoints
@router.get(
    "",
    response_model=List[IntegrationResponse],
    summary="List integrations"
)
async def list_integrations(
    integration_type: Optional[IntegrationType] = Query(None),
    status: Optional[IntegrationStatus] = Query(None),
    current_user: User = Depends(require_roles(
        UserRole.SUPER_ADMIN, UserRole.ORG_ADMIN
    )),
    service: IntegrationService = Depends(get_integration_service)
):
    """List all integrations for the organization."""
    if not has_permission(current_user.role, Permission.INTEGRATIONS_VIEW):
        raise ForbiddenException("Not authorized to view integrations")

    integrations = await service.get_integrations(
        org_id=current_user.org_id,
        integration_type=integration_type,
        status=status
    )

    return [
        IntegrationResponse(
            id=i.id,
            integration_type=i.integration_type,
            name=i.name,
            status=i.status,
            connected_at=i.connected_at,
            last_sync_at=i.last_sync_at,
            sync_status=i.sync_status,
            error_message=i.error_message,
            created_at=i.created_at
        ) for i in integrations
    ]


@router.post(
    "",
    response_model=IntegrationResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create integration"
)
async def create_integration(
    data: IntegrationCreate,
    current_user: User = Depends(require_roles(
        UserRole.SUPER_ADMIN, UserRole.ORG_ADMIN
    )),
    service: IntegrationService = Depends(get_integration_service)
):
    """Create a new integration."""
    if not has_permission(current_user.role, Permission.INTEGRATIONS_MANAGE):
        raise ForbiddenException("Not authorized to manage integrations")

    integration = await service.create_integration(
        org_id=current_user.org_id,
        integration_type=data.integration_type,
        name=data.name,
        config=data.config,
        created_by=current_user.id
    )

    return IntegrationResponse(
        id=integration.id,
        integration_type=integration.integration_type,
        name=integration.name,
        status=integration.status,
        connected_at=integration.connected_at,
        last_sync_at=integration.last_sync_at,
        sync_status=integration.sync_status,
        error_message=integration.error_message,
        created_at=integration.created_at
    )


@router.get(
    "/{integration_id}",
    response_model=IntegrationResponse,
    summary="Get integration"
)
async def get_integration(
    integration_id: str,
    current_user: User = Depends(require_roles(
        UserRole.SUPER_ADMIN, UserRole.ORG_ADMIN
    )),
    service: IntegrationService = Depends(get_integration_service)
):
    """Get integration details."""
    integration = await service.get_integration(integration_id, current_user.org_id)

    if not integration:
        raise NotFoundException("Integration", integration_id)

    return IntegrationResponse(
        id=integration.id,
        integration_type=integration.integration_type,
        name=integration.name,
        status=integration.status,
        connected_at=integration.connected_at,
        last_sync_at=integration.last_sync_at,
        sync_status=integration.sync_status,
        error_message=integration.error_message,
        created_at=integration.created_at
    )


@router.post(
    "/{integration_id}/sync",
    summary="Sync integration"
)
async def sync_integration(
    integration_id: str,
    current_user: User = Depends(require_roles(
        UserRole.SUPER_ADMIN, UserRole.ORG_ADMIN
    )),
    service: IntegrationService = Depends(get_integration_service)
):
    """Trigger sync for an integration."""
    if not has_permission(current_user.role, Permission.INTEGRATIONS_MANAGE):
        raise ForbiddenException("Not authorized to manage integrations")

    return await service.sync_integration(integration_id, current_user.org_id)


@router.delete(
    "/{integration_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete integration"
)
async def delete_integration(
    integration_id: str,
    current_user: User = Depends(require_roles(
        UserRole.SUPER_ADMIN, UserRole.ORG_ADMIN
    )),
    service: IntegrationService = Depends(get_integration_service)
):
    """Delete an integration."""
    if not has_permission(current_user.role, Permission.INTEGRATIONS_MANAGE):
        raise ForbiddenException("Not authorized to manage integrations")

    success = await service.delete_integration(integration_id, current_user.org_id)

    if not success:
        raise NotFoundException("Integration", integration_id)


@router.get(
    "/{integration_type}/oauth/init",
    summary="Initiate OAuth"
)
async def initiate_oauth(
    integration_type: IntegrationType,
    redirect_uri: str = Query(...),
    current_user: User = Depends(require_roles(
        UserRole.SUPER_ADMIN, UserRole.ORG_ADMIN
    )),
    service: IntegrationService = Depends(get_integration_service)
):
    """Initiate OAuth flow for an integration."""
    return await service.initiate_oauth(
        org_id=current_user.org_id,
        integration_type=integration_type,
        redirect_uri=redirect_uri
    )


@router.post(
    "/{integration_type}/oauth/callback",
    response_model=IntegrationResponse,
    summary="Complete OAuth"
)
async def complete_oauth(
    integration_type: IntegrationType,
    code: str = Query(...),
    state: str = Query(...),
    current_user: User = Depends(require_roles(
        UserRole.SUPER_ADMIN, UserRole.ORG_ADMIN
    )),
    service: IntegrationService = Depends(get_integration_service)
):
    """Complete OAuth flow and create integration."""
    integration = await service.complete_oauth(
        org_id=current_user.org_id,
        integration_type=integration_type,
        code=code,
        state=state,
        created_by=current_user.id
    )

    if not integration:
        raise ForbiddenException("OAuth flow failed")

    return IntegrationResponse(
        id=integration.id,
        integration_type=integration.integration_type,
        name=integration.name,
        status=integration.status,
        connected_at=integration.connected_at,
        last_sync_at=integration.last_sync_at,
        sync_status=integration.sync_status,
        error_message=integration.error_message,
        created_at=integration.created_at
    )


# Webhook Endpoints
@router.get(
    "/webhooks",
    response_model=List[WebhookResponse],
    summary="List webhooks"
)
async def list_webhooks(
    active_only: bool = Query(False),
    current_user: User = Depends(require_roles(
        UserRole.SUPER_ADMIN, UserRole.ORG_ADMIN
    )),
    service: IntegrationService = Depends(get_integration_service)
):
    """List all webhooks for the organization."""
    if not has_permission(current_user.role, Permission.WEBHOOKS_VIEW):
        raise ForbiddenException("Not authorized to view webhooks")

    webhooks = await service.get_webhooks(
        org_id=current_user.org_id,
        active_only=active_only
    )

    return [
        WebhookResponse(
            id=w.id,
            name=w.name,
            url=w.url,
            events=w.events or [],
            is_active=w.is_active,
            delivery_count=w.delivery_count or 0,
            failure_count=w.failure_count or 0,
            last_delivery_at=w.last_delivery_at,
            last_failure_at=w.last_failure_at,
            created_at=w.created_at
        ) for w in webhooks
    ]


@router.post(
    "/webhooks",
    response_model=WebhookResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create webhook"
)
async def create_webhook(
    data: WebhookCreate,
    current_user: User = Depends(require_roles(
        UserRole.SUPER_ADMIN, UserRole.ORG_ADMIN
    )),
    service: IntegrationService = Depends(get_integration_service)
):
    """Create a new webhook."""
    if not has_permission(current_user.role, Permission.WEBHOOKS_MANAGE):
        raise ForbiddenException("Not authorized to manage webhooks")

    webhook = await service.create_webhook(
        org_id=current_user.org_id,
        name=data.name,
        url=data.url,
        events=data.events,
        created_by=current_user.id,
        secret=data.secret,
        headers=data.headers
    )

    return WebhookResponse(
        id=webhook.id,
        name=webhook.name,
        url=webhook.url,
        events=webhook.events or [],
        is_active=webhook.is_active,
        delivery_count=webhook.delivery_count or 0,
        failure_count=webhook.failure_count or 0,
        last_delivery_at=webhook.last_delivery_at,
        last_failure_at=webhook.last_failure_at,
        created_at=webhook.created_at
    )


@router.get(
    "/webhooks/{webhook_id}",
    response_model=WebhookResponse,
    summary="Get webhook"
)
async def get_webhook(
    webhook_id: str,
    current_user: User = Depends(require_roles(
        UserRole.SUPER_ADMIN, UserRole.ORG_ADMIN
    )),
    service: IntegrationService = Depends(get_integration_service)
):
    """Get webhook details."""
    webhook = await service.get_webhook(webhook_id, current_user.org_id)

    if not webhook:
        raise NotFoundException("Webhook", webhook_id)

    return WebhookResponse(
        id=webhook.id,
        name=webhook.name,
        url=webhook.url,
        events=webhook.events or [],
        is_active=webhook.is_active,
        delivery_count=webhook.delivery_count or 0,
        failure_count=webhook.failure_count or 0,
        last_delivery_at=webhook.last_delivery_at,
        last_failure_at=webhook.last_failure_at,
        created_at=webhook.created_at
    )


@router.patch(
    "/webhooks/{webhook_id}",
    response_model=WebhookResponse,
    summary="Update webhook"
)
async def update_webhook(
    webhook_id: str,
    data: WebhookUpdate,
    current_user: User = Depends(require_roles(
        UserRole.SUPER_ADMIN, UserRole.ORG_ADMIN
    )),
    service: IntegrationService = Depends(get_integration_service)
):
    """Update a webhook."""
    if not has_permission(current_user.role, Permission.WEBHOOKS_MANAGE):
        raise ForbiddenException("Not authorized to manage webhooks")

    updates = data.model_dump(exclude_unset=True)
    webhook = await service.update_webhook(webhook_id, current_user.org_id, updates)

    if not webhook:
        raise NotFoundException("Webhook", webhook_id)

    return WebhookResponse(
        id=webhook.id,
        name=webhook.name,
        url=webhook.url,
        events=webhook.events or [],
        is_active=webhook.is_active,
        delivery_count=webhook.delivery_count or 0,
        failure_count=webhook.failure_count or 0,
        last_delivery_at=webhook.last_delivery_at,
        last_failure_at=webhook.last_failure_at,
        created_at=webhook.created_at
    )


@router.delete(
    "/webhooks/{webhook_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete webhook"
)
async def delete_webhook(
    webhook_id: str,
    current_user: User = Depends(require_roles(
        UserRole.SUPER_ADMIN, UserRole.ORG_ADMIN
    )),
    service: IntegrationService = Depends(get_integration_service)
):
    """Delete a webhook."""
    if not has_permission(current_user.role, Permission.WEBHOOKS_MANAGE):
        raise ForbiddenException("Not authorized to manage webhooks")

    success = await service.delete_webhook(webhook_id, current_user.org_id)

    if not success:
        raise NotFoundException("Webhook", webhook_id)


@router.post(
    "/webhooks/{webhook_id}/test",
    summary="Test webhook"
)
async def test_webhook(
    webhook_id: str,
    current_user: User = Depends(require_roles(
        UserRole.SUPER_ADMIN, UserRole.ORG_ADMIN
    )),
    service: IntegrationService = Depends(get_integration_service)
):
    """Send a test event to a webhook."""
    return await service.test_webhook(webhook_id, current_user.org_id)


@router.get(
    "/webhooks/{webhook_id}/deliveries",
    response_model=List[WebhookDeliveryResponse],
    summary="Get webhook deliveries"
)
async def get_webhook_deliveries(
    webhook_id: str,
    limit: int = Query(50, ge=1, le=100),
    current_user: User = Depends(require_roles(
        UserRole.SUPER_ADMIN, UserRole.ORG_ADMIN
    )),
    service: IntegrationService = Depends(get_integration_service)
):
    """Get delivery logs for a webhook."""
    if not has_permission(current_user.role, Permission.WEBHOOKS_VIEW):
        raise ForbiddenException("Not authorized to view webhook logs")

    deliveries = await service.get_webhook_deliveries(
        webhook_id, current_user.org_id, limit
    )

    return [
        WebhookDeliveryResponse(
            id=d.id,
            event_type=d.event_type,
            success=d.success,
            response_status=d.response_status,
            error_message=d.error_message,
            created_at=d.created_at
        ) for d in deliveries
    ]


@router.post(
    "/webhooks/deliveries/{delivery_id}/retry",
    summary="Retry webhook delivery"
)
async def retry_delivery(
    delivery_id: str,
    current_user: User = Depends(require_roles(
        UserRole.SUPER_ADMIN, UserRole.ORG_ADMIN
    )),
    service: IntegrationService = Depends(get_integration_service)
):
    """Retry a failed webhook delivery."""
    if not has_permission(current_user.role, Permission.WEBHOOKS_MANAGE):
        raise ForbiddenException("Not authorized to manage webhooks")

    delivery = await service.retry_delivery(delivery_id, current_user.org_id)

    if not delivery:
        return {"success": False, "error": "Delivery not found or already successful"}

    return {
        "success": delivery.success,
        "delivery_id": delivery.id,
        "message": "Retry successful" if delivery.success else "Retry failed"
    }

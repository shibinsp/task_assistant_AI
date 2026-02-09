"""
TaskPulse - AI Assistant - Admin API
Security, compliance, and admin endpoints
"""

from typing import Optional, List
from fastapi import APIRouter, Depends, Query, status, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, text
from datetime import datetime, timedelta

from app.database import get_db
from app.models.user import User, UserRole
from app.models.audit import AuditLog, GDPRRequest, APIKey, SystemHealth, ActorType, AuditAction
from app.api.v1.dependencies import get_current_active_user, require_roles, get_pagination, PaginationParams
from app.core.permissions import Permission, has_permission
from app.core.exceptions import NotFoundException, ForbiddenException
from app.utils.helpers import generate_uuid
from app.core.security import hash_password
from pydantic import BaseModel, Field
import secrets

router = APIRouter()


# Schemas
class AuditLogResponse(BaseModel):
    id: str
    actor_type: ActorType
    actor_id: Optional[str]
    actor_name: Optional[str]
    action: AuditAction
    resource_type: str
    resource_id: Optional[str]
    description: Optional[str]
    ip_address: Optional[str]
    timestamp: datetime

    class Config:
        from_attributes = True


class AuditLogListResponse(BaseModel):
    logs: List[AuditLogResponse]
    total: int
    page: int
    page_size: int


class GDPRExportRequest(BaseModel):
    user_id: str
    include_tasks: bool = True
    include_checkins: bool = True
    include_skills: bool = True


class GDPRExportResponse(BaseModel):
    request_id: str
    status: str
    estimated_completion: datetime
    message: str


class APIKeyCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=200)
    scopes: List[str] = Field(default_factory=list)
    expires_in_days: Optional[int] = Field(None, ge=1, le=365)


class APIKeyResponse(BaseModel):
    id: str
    name: str
    key_prefix: str
    scopes: List[str]
    is_active: bool
    expires_at: Optional[datetime]
    last_used_at: Optional[datetime]
    usage_count: int
    created_at: datetime

    class Config:
        from_attributes = True


class APIKeyCreatedResponse(APIKeyResponse):
    api_key: str  # Full key only shown once at creation


class SystemHealthResponse(BaseModel):
    status: str
    database: dict
    api: dict
    ai: dict
    background_jobs: dict
    storage: dict
    active_alerts: List[str]
    snapshot_time: datetime


# Endpoints
@router.get(
    "/audit-logs",
    response_model=AuditLogListResponse,
    summary="Get audit logs"
)
async def get_audit_logs(
    pagination: PaginationParams = Depends(get_pagination),
    actor_type: Optional[ActorType] = Query(None),
    action: Optional[AuditAction] = Query(None),
    resource_type: Optional[str] = Query(None),
    start_date: Optional[datetime] = Query(None),
    end_date: Optional[datetime] = Query(None),
    current_user: User = Depends(require_roles(UserRole.SUPER_ADMIN, UserRole.ORG_ADMIN)),
    db: AsyncSession = Depends(get_db)
):
    """Get audit logs with filters."""
    if not has_permission(current_user.role, Permission.ADMIN_AUDIT_LOGS):
        raise ForbiddenException("Not authorized")

    query = select(AuditLog).where(AuditLog.org_id == current_user.org_id)

    if actor_type:
        query = query.where(AuditLog.actor_type == actor_type)
    if action:
        query = query.where(AuditLog.action == action)
    if resource_type:
        query = query.where(AuditLog.resource_type == resource_type)
    if start_date:
        query = query.where(AuditLog.timestamp >= start_date)
    if end_date:
        query = query.where(AuditLog.timestamp <= end_date)

    count_query = select(func.count()).select_from(query.subquery())
    total = (await db.execute(count_query)).scalar() or 0

    result = await db.execute(
        query.order_by(AuditLog.timestamp.desc())
        .offset(pagination.skip).limit(pagination.limit)
    )
    logs = result.scalars().all()

    return AuditLogListResponse(
        logs=[AuditLogResponse(
            id=log.id, actor_type=log.actor_type, actor_id=log.actor_id,
            actor_name=log.actor_name, action=log.action, resource_type=log.resource_type,
            resource_id=log.resource_id, description=log.description,
            ip_address=log.ip_address, timestamp=log.timestamp
        ) for log in logs],
        total=total,
        page=pagination.page,
        page_size=pagination.page_size
    )


@router.get(
    "/system/health",
    response_model=SystemHealthResponse,
    summary="Get system health"
)
async def get_system_health(
    current_user: User = Depends(require_roles(UserRole.SUPER_ADMIN)),
    db: AsyncSession = Depends(get_db)
):
    """Get system health status."""
    if not has_permission(current_user.role, Permission.ADMIN_SYSTEM_HEALTH):
        raise ForbiddenException("Not authorized")

    # Check database
    db_healthy = True
    db_error = None
    try:
        await db.execute(text("SELECT 1"))
    except Exception as e:
        db_healthy = False
        db_error = str(e)

    return SystemHealthResponse(
        status="healthy" if db_healthy else "degraded",
        database={
            "status": "healthy" if db_healthy else "unhealthy",
            "error": db_error,
            "connections_active": 5,  # Mock
            "query_avg_ms": 12.5
        },
        api={
            "status": "healthy",
            "requests_per_minute": 150,
            "error_rate": 0.02,
            "latency_p50_ms": 45,
            "latency_p99_ms": 250
        },
        ai={
            "status": "healthy",
            "requests_per_hour": 500,
            "avg_latency_ms": 850,
            "cache_hit_rate": 0.65
        },
        background_jobs={
            "status": "healthy",
            "pending": 3,
            "failed": 0
        },
        storage={
            "status": "healthy",
            "used_mb": 256,
            "total_mb": 10240
        },
        active_alerts=[],
        snapshot_time=datetime.utcnow()
    )


@router.post(
    "/gdpr/export/{user_id}",
    response_model=GDPRExportResponse,
    summary="Request GDPR data export"
)
async def request_gdpr_export(
    user_id: str,
    current_user: User = Depends(require_roles(UserRole.SUPER_ADMIN, UserRole.ORG_ADMIN)),
    db: AsyncSession = Depends(get_db)
):
    """Request GDPR data export for a user."""
    if not has_permission(current_user.role, Permission.ADMIN_GDPR):
        raise ForbiddenException("Not authorized")

    # Create GDPR request
    request = GDPRRequest(
        id=generate_uuid(),
        org_id=current_user.org_id,
        user_id=user_id,
        request_type="export",
        status="pending"
    )
    db.add(request)

    # Log audit
    audit = AuditLog(
        id=generate_uuid(),
        org_id=current_user.org_id,
        actor_type=ActorType.ADMIN,
        actor_id=current_user.id,
        actor_name=f"{current_user.first_name} {current_user.last_name}",
        action=AuditAction.DATA_REQUEST,
        resource_type="user",
        resource_id=user_id,
        description=f"GDPR data export requested for user {user_id}"
    )
    db.add(audit)

    await db.flush()

    return GDPRExportResponse(
        request_id=request.id,
        status="pending",
        estimated_completion=datetime.utcnow() + timedelta(hours=24),
        message="Data export request submitted. You will be notified when ready."
    )


@router.delete(
    "/gdpr/erase/{user_id}",
    summary="Request GDPR data erasure"
)
async def request_gdpr_erasure(
    user_id: str,
    current_user: User = Depends(require_roles(UserRole.SUPER_ADMIN)),
    db: AsyncSession = Depends(get_db)
):
    """Request GDPR right to erasure for a user."""
    if not has_permission(current_user.role, Permission.ADMIN_GDPR):
        raise ForbiddenException("Not authorized")

    # Create GDPR request
    request = GDPRRequest(
        id=generate_uuid(),
        org_id=current_user.org_id,
        user_id=user_id,
        request_type="erasure",
        status="pending"
    )
    db.add(request)

    # Log audit
    audit = AuditLog(
        id=generate_uuid(),
        org_id=current_user.org_id,
        actor_type=ActorType.ADMIN,
        actor_id=current_user.id,
        actor_name=f"{current_user.first_name} {current_user.last_name}",
        action=AuditAction.DATA_DELETION,
        resource_type="user",
        resource_id=user_id,
        description=f"GDPR data erasure requested for user {user_id}"
    )
    db.add(audit)

    await db.flush()

    return {
        "request_id": request.id,
        "status": "pending",
        "message": "Data erasure request submitted. This action is irreversible."
    }


@router.get(
    "/ai/governance",
    summary="Get AI governance dashboard"
)
async def get_ai_governance(
    current_user: User = Depends(require_roles(UserRole.SUPER_ADMIN, UserRole.ORG_ADMIN)),
    db: AsyncSession = Depends(get_db)
):
    """Get AI governance and ethics dashboard."""
    if not has_permission(current_user.role, Permission.ADMIN_AI_GOVERNANCE):
        raise ForbiddenException("Not authorized")

    return {
        "model_info": {
            "provider": "mock",
            "version": "v1.0",
            "last_updated": datetime.utcnow().isoformat()
        },
        "usage_stats": {
            "total_requests_30d": 15000,
            "total_tokens_30d": 2500000,
            "cost_30d": 125.50
        },
        "quality_metrics": {
            "hallucination_rate": 0.02,
            "user_satisfaction": 0.87,
            "accuracy_score": 0.92
        },
        "bias_monitoring": {
            "gender_bias_score": 0.05,
            "role_bias_score": 0.08,
            "last_audit": datetime.utcnow().isoformat()
        },
        "human_overrides": {
            "total_30d": 45,
            "reasons": [
                {"reason": "Incorrect suggestion", "count": 20},
                {"reason": "Missing context", "count": 15},
                {"reason": "Better alternative found", "count": 10}
            ]
        }
    }


# API Key Management
@router.get(
    "/api-keys",
    response_model=List[APIKeyResponse],
    summary="List API keys"
)
async def list_api_keys(
    current_user: User = Depends(require_roles(UserRole.SUPER_ADMIN, UserRole.ORG_ADMIN)),
    db: AsyncSession = Depends(get_db)
):
    """List API keys for the organization."""
    if not has_permission(current_user.role, Permission.API_KEYS_MANAGE):
        raise ForbiddenException("Not authorized")

    result = await db.execute(
        select(APIKey).where(APIKey.org_id == current_user.org_id)
        .order_by(APIKey.created_at.desc())
    )
    keys = result.scalars().all()

    return [APIKeyResponse(
        id=k.id, name=k.name, key_prefix=k.key_prefix, scopes=k.scopes,
        is_active=k.is_active, expires_at=k.expires_at, last_used_at=k.last_used_at,
        usage_count=k.usage_count, created_at=k.created_at
    ) for k in keys]


@router.post(
    "/api-keys",
    response_model=APIKeyCreatedResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create API key"
)
async def create_api_key(
    key_data: APIKeyCreate,
    current_user: User = Depends(require_roles(UserRole.SUPER_ADMIN, UserRole.ORG_ADMIN)),
    db: AsyncSession = Depends(get_db)
):
    """Create a new API key."""
    if not has_permission(current_user.role, Permission.API_KEYS_MANAGE):
        raise ForbiddenException("Not authorized")

    # Generate key
    raw_key = f"tp_{secrets.token_urlsafe(32)}"
    key_prefix = raw_key[:10]

    expires_at = None
    if key_data.expires_in_days:
        expires_at = datetime.utcnow() + timedelta(days=key_data.expires_in_days)

    api_key = APIKey(
        id=generate_uuid(),
        org_id=current_user.org_id,
        user_id=current_user.id,
        name=key_data.name,
        key_hash=hash_password(raw_key),
        key_prefix=key_prefix,
        expires_at=expires_at,
        created_by=current_user.id
    )
    api_key.scopes = key_data.scopes

    db.add(api_key)
    await db.flush()
    await db.refresh(api_key)

    return APIKeyCreatedResponse(
        id=api_key.id, name=api_key.name, key_prefix=api_key.key_prefix,
        scopes=api_key.scopes, is_active=api_key.is_active,
        expires_at=api_key.expires_at, last_used_at=api_key.last_used_at,
        usage_count=api_key.usage_count, created_at=api_key.created_at,
        api_key=raw_key  # Only shown once!
    )


@router.delete(
    "/api-keys/{key_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Revoke API key"
)
async def revoke_api_key(
    key_id: str,
    current_user: User = Depends(require_roles(UserRole.SUPER_ADMIN, UserRole.ORG_ADMIN)),
    db: AsyncSession = Depends(get_db)
):
    """Revoke an API key."""
    if not has_permission(current_user.role, Permission.API_KEYS_MANAGE):
        raise ForbiddenException("Not authorized")

    result = await db.execute(
        select(APIKey).where(APIKey.id == key_id, APIKey.org_id == current_user.org_id)
    )
    key = result.scalar_one_or_none()
    if not key:
        raise NotFoundException("APIKey", key_id)

    key.is_active = False
    await db.flush()

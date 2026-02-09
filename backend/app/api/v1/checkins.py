"""
TaskPulse - AI Assistant - Check-Ins API
Endpoints for the Smart Check-In Engine
"""

from typing import Optional, List
from fastapi import APIRouter, Depends, Query, status, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.user import User, UserRole
from app.models.checkin import CheckInStatus, CheckInTrigger
from app.schemas.checkin import (
    CheckInResponse, CheckInDetailResponse, CheckInListResponse,
    CheckInSubmit, CheckInSkip, CheckInCreate,
    CheckInConfigCreate, CheckInConfigUpdate, CheckInConfigResponse,
    EscalationRequest, EscalationResponse,
    CheckInStatistics, CheckInFeedItem, CheckInFeedResponse
)
from app.services.checkin_service import CheckInService
from app.api.v1.dependencies import (
    get_current_active_user, require_roles, get_pagination, PaginationParams
)
from app.core.permissions import Permission, has_permission
from app.core.exceptions import NotFoundException, ForbiddenException

router = APIRouter()


def get_checkin_service(db: AsyncSession = Depends(get_db)) -> CheckInService:
    """Dependency to get check-in service."""
    return CheckInService(db)


# ==================== Check-In CRUD ====================

@router.get(
    "",
    response_model=CheckInListResponse,
    summary="List check-ins",
    description="List check-ins with filters"
)
async def list_checkins(
    pagination: PaginationParams = Depends(get_pagination),
    status_filter: Optional[CheckInStatus] = Query(None, alias="status"),
    task_id: Optional[str] = Query(None),
    user_id: Optional[str] = Query(None),
    team_id: Optional[str] = Query(None),
    pending_only: bool = Query(False),
    current_user: User = Depends(get_current_active_user),
    service: CheckInService = Depends(get_checkin_service)
):
    """List check-ins."""
    # Permission check
    can_read_all = has_permission(current_user.role, Permission.CHECKINS_READ)
    can_read_team = has_permission(current_user.role, Permission.CHECKINS_READ_TEAM)
    can_read_own = has_permission(current_user.role, Permission.CHECKINS_READ_OWN)

    if not can_read_all:
        if can_read_team:
            team_id = current_user.team_id
        elif can_read_own:
            user_id = current_user.id

    checkins, total = await service.get_checkins(
        org_id=current_user.org_id,
        user_id=user_id,
        task_id=task_id,
        team_id=team_id,
        status=status_filter,
        pending_only=pending_only,
        skip=pagination.skip,
        limit=pagination.limit
    )

    return CheckInListResponse(
        checkins=[
            CheckInResponse(
                **c.__dict__,
                is_overdue=c.is_overdue,
                response_time_minutes=c.response_time_minutes,
                task_title=c.task.title if c.task else None
            ) for c in checkins
        ],
        total=total,
        page=pagination.page,
        page_size=pagination.page_size
    )


@router.get(
    "/pending",
    response_model=List[CheckInResponse],
    summary="Get pending check-ins",
    description="Get all pending check-ins for the current user"
)
async def get_pending_checkins(
    current_user: User = Depends(get_current_active_user),
    service: CheckInService = Depends(get_checkin_service)
):
    """Get pending check-ins for current user."""
    checkins = await service.get_pending_checkins_for_user(
        current_user.id, current_user.org_id
    )

    return [
        CheckInResponse(
            **c.__dict__,
            is_overdue=c.is_overdue,
            response_time_minutes=c.response_time_minutes,
            task_title=c.task.title if c.task else None
        ) for c in checkins
    ]


@router.get(
    "/statistics",
    response_model=CheckInStatistics,
    summary="Get check-in statistics",
    description="Get check-in statistics for the organization"
)
async def get_statistics(
    team_id: Optional[str] = Query(None),
    user_id: Optional[str] = Query(None),
    days: int = Query(30, ge=1, le=365),
    current_user: User = Depends(get_current_active_user),
    service: CheckInService = Depends(get_checkin_service)
):
    """Get check-in statistics."""
    stats = await service.get_statistics(
        org_id=current_user.org_id,
        team_id=team_id,
        user_id=user_id,
        days=days
    )
    return CheckInStatistics(**stats)


@router.get(
    "/feed",
    response_model=CheckInFeedResponse,
    summary="Get manager feed",
    description="Get check-in feed for managers"
)
async def get_manager_feed(
    pagination: PaginationParams = Depends(get_pagination),
    needs_attention: bool = Query(False, description="Only show items needing attention"),
    current_user: User = Depends(require_roles(
        UserRole.SUPER_ADMIN, UserRole.ORG_ADMIN, UserRole.MANAGER, UserRole.TEAM_LEAD
    )),
    service: CheckInService = Depends(get_checkin_service)
):
    """Get check-in feed for managers."""
    checkins, total, attention_count = await service.get_manager_feed(
        org_id=current_user.org_id,
        manager_id=current_user.id,
        needs_attention_only=needs_attention,
        skip=pagination.skip,
        limit=pagination.limit
    )

    return CheckInFeedResponse(
        items=[
            CheckInFeedItem(
                checkin_id=c.id,
                task_id=c.task_id,
                task_title=c.task.title if c.task else "Unknown",
                user_id=c.user_id or "",
                user_name=f"{c.user.first_name} {c.user.last_name}" if c.user else "Unknown",
                status=c.status,
                progress_indicator=c.progress_indicator,
                help_needed=c.help_needed,
                friction_detected=c.friction_detected,
                ai_suggestion=c.ai_suggestion,
                escalated=c.escalated,
                scheduled_at=c.scheduled_at,
                responded_at=c.responded_at
            ) for c in checkins
        ],
        total=total,
        needs_attention=attention_count,
        page=pagination.page,
        page_size=pagination.page_size
    )


@router.post(
    "",
    response_model=CheckInResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create check-in",
    description="Manually create a check-in"
)
async def create_checkin(
    checkin_data: CheckInCreate,
    current_user: User = Depends(require_roles(
        UserRole.SUPER_ADMIN, UserRole.ORG_ADMIN, UserRole.MANAGER, UserRole.TEAM_LEAD
    )),
    service: CheckInService = Depends(get_checkin_service)
):
    """Manually create a check-in."""
    checkin = await service.create_checkin(
        org_id=current_user.org_id,
        task_id=checkin_data.task_id,
        user_id=checkin_data.user_id,
        trigger=checkin_data.trigger,
        scheduled_at=checkin_data.scheduled_at
    )

    return CheckInResponse(
        **checkin.__dict__,
        is_overdue=checkin.is_overdue,
        response_time_minutes=checkin.response_time_minutes
    )


@router.get(
    "/{checkin_id}",
    response_model=CheckInDetailResponse,
    summary="Get check-in",
    description="Get check-in details"
)
async def get_checkin(
    checkin_id: str,
    current_user: User = Depends(get_current_active_user),
    service: CheckInService = Depends(get_checkin_service)
):
    """Get check-in details."""
    checkin = await service.get_checkin_by_id(checkin_id, current_user.org_id)
    if not checkin:
        raise NotFoundException("CheckIn", checkin_id)

    # Permission check
    can_view = (
        has_permission(current_user.role, Permission.CHECKINS_READ) or
        checkin.user_id == current_user.id
    )
    if not can_view:
        raise ForbiddenException("Not authorized to view this check-in")

    return CheckInDetailResponse(
        **checkin.__dict__,
        is_overdue=checkin.is_overdue,
        response_time_minutes=checkin.response_time_minutes,
        task_title=checkin.task.title if checkin.task else None,
        reminders_sent=len(checkin.reminders) if checkin.reminders else 0
    )


@router.post(
    "/{checkin_id}/respond",
    response_model=CheckInResponse,
    summary="Respond to check-in",
    description="Submit a response to a check-in"
)
async def respond_to_checkin(
    checkin_id: str,
    response: CheckInSubmit,
    current_user: User = Depends(get_current_active_user),
    service: CheckInService = Depends(get_checkin_service)
):
    """Respond to a check-in."""
    if not has_permission(current_user.role, Permission.CHECKINS_RESPOND):
        raise ForbiddenException("Not authorized to respond to check-ins")

    checkin = await service.respond_to_checkin(
        checkin_id, current_user.org_id, current_user.id, response
    )

    return CheckInResponse(
        **checkin.__dict__,
        is_overdue=checkin.is_overdue,
        response_time_minutes=checkin.response_time_minutes
    )


@router.post(
    "/{checkin_id}/skip",
    response_model=CheckInResponse,
    summary="Skip check-in",
    description="Skip a check-in"
)
async def skip_checkin(
    checkin_id: str,
    skip_data: CheckInSkip,
    current_user: User = Depends(get_current_active_user),
    service: CheckInService = Depends(get_checkin_service)
):
    """Skip a check-in."""
    checkin = await service.skip_checkin(
        checkin_id, current_user.org_id, current_user.id, skip_data
    )

    return CheckInResponse(
        **checkin.__dict__,
        is_overdue=checkin.is_overdue,
        response_time_minutes=checkin.response_time_minutes
    )


@router.post(
    "/{checkin_id}/escalate",
    response_model=EscalationResponse,
    summary="Escalate check-in",
    description="Escalate a check-in to a manager"
)
async def escalate_checkin(
    checkin_id: str,
    escalation: EscalationRequest,
    current_user: User = Depends(get_current_active_user),
    service: CheckInService = Depends(get_checkin_service)
):
    """Escalate a check-in."""
    checkin = await service.escalate_checkin(
        checkin_id, current_user.org_id, escalation, current_user.id
    )

    return EscalationResponse(
        checkin_id=checkin.id,
        escalated_to=checkin.escalated_to or "",
        escalated_at=checkin.escalated_at or checkin.updated_at,
        reason=checkin.escalation_reason or "",
        notification_sent=True
    )


# ==================== Configuration Endpoints ====================

@router.get(
    "/config",
    response_model=List[CheckInConfigResponse],
    summary="Get check-in configs",
    description="Get check-in configurations for the organization"
)
async def get_configs(
    current_user: User = Depends(require_roles(
        UserRole.SUPER_ADMIN, UserRole.ORG_ADMIN, UserRole.MANAGER
    )),
    service: CheckInService = Depends(get_checkin_service),
    db: AsyncSession = Depends(get_db)
):
    """Get all check-in configurations."""
    from sqlalchemy import select
    from app.models.checkin import CheckInConfig

    result = await db.execute(
        select(CheckInConfig).where(
            CheckInConfig.org_id == current_user.org_id
        )
    )
    configs = result.scalars().all()

    return [CheckInConfigResponse.model_validate(c) for c in configs]


@router.post(
    "/config",
    response_model=CheckInConfigResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create check-in config",
    description="Create a check-in configuration"
)
async def create_config(
    config_data: CheckInConfigCreate,
    current_user: User = Depends(require_roles(
        UserRole.SUPER_ADMIN, UserRole.ORG_ADMIN
    )),
    service: CheckInService = Depends(get_checkin_service)
):
    """Create a check-in configuration."""
    if not has_permission(current_user.role, Permission.CHECKINS_CONFIGURE):
        raise ForbiddenException("Not authorized to configure check-ins")

    config = await service.create_config(current_user.org_id, config_data)
    return CheckInConfigResponse.model_validate(config)


@router.get(
    "/config/{config_id}",
    response_model=CheckInConfigResponse,
    summary="Get check-in config",
    description="Get a specific check-in configuration"
)
async def get_config(
    config_id: str,
    current_user: User = Depends(get_current_active_user),
    service: CheckInService = Depends(get_checkin_service)
):
    """Get a check-in configuration."""
    config = await service.get_config(config_id, current_user.org_id)
    if not config:
        raise NotFoundException("CheckInConfig", config_id)
    return CheckInConfigResponse.model_validate(config)


@router.patch(
    "/config/{config_id}",
    response_model=CheckInConfigResponse,
    summary="Update check-in config",
    description="Update a check-in configuration"
)
async def update_config(
    config_id: str,
    config_data: CheckInConfigUpdate,
    current_user: User = Depends(require_roles(
        UserRole.SUPER_ADMIN, UserRole.ORG_ADMIN
    )),
    service: CheckInService = Depends(get_checkin_service)
):
    """Update a check-in configuration."""
    if not has_permission(current_user.role, Permission.CHECKINS_CONFIGURE):
        raise ForbiddenException("Not authorized to configure check-ins")

    config = await service.update_config(
        config_id, current_user.org_id, config_data
    )
    return CheckInConfigResponse.model_validate(config)


@router.delete(
    "/config/{config_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete check-in config",
    description="Delete a check-in configuration"
)
async def delete_config(
    config_id: str,
    current_user: User = Depends(require_roles(
        UserRole.SUPER_ADMIN, UserRole.ORG_ADMIN
    )),
    service: CheckInService = Depends(get_checkin_service)
):
    """Delete a check-in configuration."""
    if not has_permission(current_user.role, Permission.CHECKINS_CONFIGURE):
        raise ForbiddenException("Not authorized to configure check-ins")

    await service.delete_config(config_id, current_user.org_id)

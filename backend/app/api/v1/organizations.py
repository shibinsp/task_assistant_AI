"""
TaskPulse - AI Assistant - Organizations API
Endpoints for organization management
"""

from typing import Optional
from fastapi import APIRouter, Depends, Query, status, HTTPException
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.user import User, UserRole
from app.models.organization import Organization, PlanTier
from app.schemas.organization import (
    OrganizationResponse, OrganizationDetailResponse,
    OrganizationUpdate, OrganizationSettings, OrganizationListResponse
)
from app.api.v1.dependencies import (
    get_current_active_user, require_roles, get_pagination, PaginationParams
)
from app.core.permissions import Permission, has_permission
from app.core.exceptions import NotFoundException

router = APIRouter()


@router.get(
    "",
    response_model=OrganizationListResponse,
    summary="List organizations",
    description="List all organizations (super admin only)"
)
async def list_organizations(
    pagination: PaginationParams = Depends(get_pagination),
    plan: Optional[PlanTier] = Query(None, description="Filter by plan"),
    is_active: Optional[bool] = Query(None, description="Filter by active status"),
    search: Optional[str] = Query(None, description="Search by name"),
    current_user: User = Depends(require_roles(UserRole.SUPER_ADMIN)),
    db: AsyncSession = Depends(get_db)
):
    """List all organizations. Super admin only."""
    query = select(Organization)

    if plan:
        query = query.where(Organization.plan == plan)
    if is_active is not None:
        query = query.where(Organization.is_active == is_active)
    if search:
        query = query.where(Organization.name.ilike(f"%{search}%"))

    # Get total
    count_query = select(func.count()).select_from(query.subquery())
    total = (await db.execute(count_query)).scalar() or 0

    # Paginate
    query = query.offset(pagination.skip).limit(pagination.limit)
    query = query.order_by(Organization.created_at.desc())

    result = await db.execute(query)
    orgs = result.scalars().all()

    return OrganizationListResponse(
        organizations=[OrganizationResponse.model_validate(o) for o in orgs],
        total=total,
        page=pagination.page,
        page_size=pagination.page_size
    )


@router.get(
    "/current",
    response_model=OrganizationDetailResponse,
    summary="Get current organization",
    description="Get the current user's organization"
)
async def get_current_organization(
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """Get the current user's organization details."""
    result = await db.execute(
        select(Organization).where(Organization.id == current_user.org_id)
    )
    org = result.scalar_one_or_none()

    if not org:
        raise NotFoundException("Organization", current_user.org_id)

    # Get user count
    user_count_result = await db.execute(
        select(func.count()).select_from(User).where(
            User.org_id == org.id,
            User.is_active == True
        )
    )
    user_count = user_count_result.scalar() or 0

    return OrganizationDetailResponse(
        id=org.id,
        name=org.name,
        slug=org.slug,
        description=org.description,
        plan=org.plan,
        is_active=org.is_active,
        settings=org.settings,
        features=org.features,
        max_users=org.max_users,
        user_count=user_count,
        created_at=org.created_at,
        updated_at=org.updated_at
    )


@router.get(
    "/{org_id}",
    response_model=OrganizationDetailResponse,
    summary="Get organization",
    description="Get organization details"
)
async def get_organization(
    org_id: str,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """Get organization details by ID."""
    # Check access
    if current_user.role != UserRole.SUPER_ADMIN and current_user.org_id != org_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to access this organization"
        )

    result = await db.execute(
        select(Organization).where(Organization.id == org_id)
    )
    org = result.scalar_one_or_none()

    if not org:
        raise NotFoundException("Organization", org_id)

    # Get user count
    user_count_result = await db.execute(
        select(func.count()).select_from(User).where(
            User.org_id == org.id,
            User.is_active == True
        )
    )
    user_count = user_count_result.scalar() or 0

    return OrganizationDetailResponse(
        id=org.id,
        name=org.name,
        slug=org.slug,
        description=org.description,
        plan=org.plan,
        is_active=org.is_active,
        settings=org.settings,
        features=org.features,
        max_users=org.max_users,
        user_count=user_count,
        created_at=org.created_at,
        updated_at=org.updated_at
    )


@router.patch(
    "/{org_id}",
    response_model=OrganizationResponse,
    summary="Update organization",
    description="Update organization details (admin only)"
)
async def update_organization(
    org_id: str,
    org_data: OrganizationUpdate,
    current_user: User = Depends(require_roles(UserRole.SUPER_ADMIN, UserRole.ORG_ADMIN)),
    db: AsyncSession = Depends(get_db)
):
    """Update organization details."""
    # Org admins can only update their own org
    if current_user.role != UserRole.SUPER_ADMIN and current_user.org_id != org_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to update this organization"
        )

    result = await db.execute(
        select(Organization).where(Organization.id == org_id)
    )
    org = result.scalar_one_or_none()

    if not org:
        raise NotFoundException("Organization", org_id)

    # Apply updates
    update_data = org_data.model_dump(exclude_unset=True)

    for field, value in update_data.items():
        if field == 'settings' and value:
            # Merge settings
            current_settings = org.settings
            current_settings.update(value)
            org.settings = current_settings
        else:
            setattr(org, field, value)

    await db.flush()
    await db.refresh(org)

    return OrganizationResponse.model_validate(org)


@router.get(
    "/{org_id}/settings",
    response_model=OrganizationSettings,
    summary="Get organization settings",
    description="Get organization settings"
)
async def get_organization_settings(
    org_id: str,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """Get organization settings."""
    if current_user.role != UserRole.SUPER_ADMIN and current_user.org_id != org_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized"
        )

    result = await db.execute(
        select(Organization).where(Organization.id == org_id)
    )
    org = result.scalar_one_or_none()

    if not org:
        raise NotFoundException("Organization", org_id)

    settings = org.settings
    return OrganizationSettings(**settings)


@router.patch(
    "/{org_id}/settings",
    response_model=OrganizationSettings,
    summary="Update organization settings",
    description="Update organization settings (admin only)"
)
async def update_organization_settings(
    org_id: str,
    settings_data: OrganizationSettings,
    current_user: User = Depends(require_roles(UserRole.SUPER_ADMIN, UserRole.ORG_ADMIN)),
    db: AsyncSession = Depends(get_db)
):
    """Update organization settings."""
    if current_user.role != UserRole.SUPER_ADMIN and current_user.org_id != org_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized"
        )

    result = await db.execute(
        select(Organization).where(Organization.id == org_id)
    )
    org = result.scalar_one_or_none()

    if not org:
        raise NotFoundException("Organization", org_id)

    org.settings = settings_data.model_dump()
    await db.flush()

    return settings_data


@router.get(
    "/{org_id}/features",
    summary="Get organization features",
    description="Get features available for organization's plan"
)
async def get_organization_features(
    org_id: str,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """Get features available for the organization based on plan."""
    if current_user.role != UserRole.SUPER_ADMIN and current_user.org_id != org_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized"
        )

    result = await db.execute(
        select(Organization).where(Organization.id == org_id)
    )
    org = result.scalar_one_or_none()

    if not org:
        raise NotFoundException("Organization", org_id)

    return {
        "plan": org.plan.value,
        "features": org.features,
        "max_users": org.max_users,
        "is_enterprise": org.is_enterprise
    }


@router.get(
    "/{org_id}/stats",
    summary="Get organization statistics",
    description="Get organization usage statistics"
)
async def get_organization_stats(
    org_id: str,
    current_user: User = Depends(require_roles(UserRole.SUPER_ADMIN, UserRole.ORG_ADMIN)),
    db: AsyncSession = Depends(get_db)
):
    """Get organization statistics."""
    if current_user.role != UserRole.SUPER_ADMIN and current_user.org_id != org_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized"
        )

    result = await db.execute(
        select(Organization).where(Organization.id == org_id)
    )
    org = result.scalar_one_or_none()

    if not org:
        raise NotFoundException("Organization", org_id)

    # Get user stats
    total_users = (await db.execute(
        select(func.count()).select_from(User).where(User.org_id == org_id)
    )).scalar() or 0

    active_users = (await db.execute(
        select(func.count()).select_from(User).where(
            User.org_id == org_id,
            User.is_active == True
        )
    )).scalar() or 0

    # Get role distribution
    role_counts = {}
    for role in UserRole:
        count = (await db.execute(
            select(func.count()).select_from(User).where(
                User.org_id == org_id,
                User.role == role,
                User.is_active == True
            )
        )).scalar() or 0
        role_counts[role.value] = count

    return {
        "organization_id": org_id,
        "plan": org.plan.value,
        "users": {
            "total": total_users,
            "active": active_users,
            "inactive": total_users - active_users,
            "max_allowed": org.max_users,
            "usage_percent": round((active_users / org.max_users) * 100, 1) if org.max_users > 0 else 0
        },
        "roles": role_counts
    }

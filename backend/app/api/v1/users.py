"""
TaskPulse - AI Assistant - Users API
Endpoints for user management
"""

from typing import Optional
from fastapi import APIRouter, Depends, Query, status, HTTPException
from sqlalchemy import select, func, and_
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.user import User, UserRole
from app.schemas.user import (
    UserCreate, UserResponse, UserDetailResponse,
    UserUpdate, UserAdminUpdate, UserListResponse
)
from app.api.v1.dependencies import (
    get_current_active_user, require_roles, get_pagination, PaginationParams
)
from app.core.permissions import Permission, has_permission
from app.core.security import hash_password
from app.core.exceptions import NotFoundException, AlreadyExistsException
from app.utils.helpers import generate_uuid

router = APIRouter()


@router.get(
    "",
    response_model=UserListResponse,
    summary="List users",
    description="List users in the organization"
)
async def list_users(
    pagination: PaginationParams = Depends(get_pagination),
    role: Optional[UserRole] = Query(None, description="Filter by role"),
    team_id: Optional[str] = Query(None, description="Filter by team"),
    is_active: Optional[bool] = Query(None, description="Filter by active status"),
    search: Optional[str] = Query(None, description="Search by name or email"),
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """
    List users in the current user's organization.

    - Admins see all users
    - Managers see their team members
    - Employees see limited info
    """
    # Build query
    query = select(User).where(User.org_id == current_user.org_id)

    # Apply filters
    if role:
        query = query.where(User.role == role)
    if team_id:
        query = query.where(User.team_id == team_id)
    if is_active is not None:
        query = query.where(User.is_active == is_active)
    if search:
        search_term = f"%{search}%"
        query = query.where(
            (User.email.ilike(search_term)) |
            (User.first_name.ilike(search_term)) |
            (User.last_name.ilike(search_term))
        )

    # For non-admins, filter based on permissions
    if not has_permission(current_user.role, Permission.USERS_READ):
        if has_permission(current_user.role, Permission.USERS_READ_OWN):
            query = query.where(User.id == current_user.id)

    # Get total count
    count_query = select(func.count()).select_from(query.subquery())
    total = (await db.execute(count_query)).scalar() or 0

    # Apply pagination
    query = query.offset(pagination.skip).limit(pagination.limit)
    query = query.order_by(User.created_at.desc())

    result = await db.execute(query)
    users = result.scalars().all()

    return UserListResponse(
        users=[UserResponse.model_validate(u) for u in users],
        total=total,
        page=pagination.page,
        page_size=pagination.page_size
    )


@router.post(
    "",
    response_model=UserResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create user",
    description="Create a new user (admin only)"
)
async def create_user(
    user_data: UserCreate,
    current_user: User = Depends(require_roles(UserRole.SUPER_ADMIN, UserRole.ORG_ADMIN)),
    db: AsyncSession = Depends(get_db)
):
    """
    Create a new user in the organization.

    Only admins can create users directly.
    """
    # Check if email exists
    result = await db.execute(
        select(User).where(
            and_(
                User.org_id == current_user.org_id,
                User.email == user_data.email.lower()
            )
        )
    )
    if result.scalar_one_or_none():
        raise AlreadyExistsException("User", "email", user_data.email)

    # Create user
    user = User(
        id=generate_uuid(),
        org_id=current_user.org_id,
        email=user_data.email.lower(),
        password_hash=hash_password(user_data.password) if user_data.password else None,
        first_name=user_data.first_name,
        last_name=user_data.last_name,
        role=user_data.role,
        skill_level=user_data.skill_level,
        team_id=user_data.team_id,
        manager_id=user_data.manager_id,
        timezone=user_data.timezone,
        is_sso_user=user_data.is_sso_user,
        is_active=True
    )

    db.add(user)
    await db.flush()
    await db.refresh(user)

    return UserResponse.model_validate(user)


@router.get(
    "/{user_id}",
    response_model=UserDetailResponse,
    summary="Get user",
    description="Get user details"
)
async def get_user(
    user_id: str,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """Get user details by ID."""
    # Check permissions
    if user_id != current_user.id:
        if not has_permission(current_user.role, Permission.USERS_READ):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not authorized to view this user"
            )

    result = await db.execute(
        select(User).where(
            and_(
                User.id == user_id,
                User.org_id == current_user.org_id
            )
        )
    )
    user = result.scalar_one_or_none()

    if not user:
        raise NotFoundException("User", user_id)

    return UserDetailResponse.model_validate(user)


@router.patch(
    "/{user_id}",
    response_model=UserResponse,
    summary="Update user",
    description="Update user details"
)
async def update_user(
    user_id: str,
    user_data: UserAdminUpdate,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Update user details.

    - Users can update their own profile (limited fields)
    - Admins can update any user (all fields)
    """
    # Get user
    result = await db.execute(
        select(User).where(
            and_(
                User.id == user_id,
                User.org_id == current_user.org_id
            )
        )
    )
    user = result.scalar_one_or_none()

    if not user:
        raise NotFoundException("User", user_id)

    # Check permissions
    is_self = user_id == current_user.id
    is_admin = has_permission(current_user.role, Permission.USERS_UPDATE)

    if not is_self and not is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to update this user"
        )

    # Apply updates
    update_data = user_data.model_dump(exclude_unset=True)

    # Non-admins can only update limited fields
    if not is_admin:
        allowed_fields = {'first_name', 'last_name', 'phone', 'timezone', 'avatar_url'}
        update_data = {k: v for k, v in update_data.items() if k in allowed_fields}

    for field, value in update_data.items():
        setattr(user, field, value)

    await db.flush()
    await db.refresh(user)

    return UserResponse.model_validate(user)


@router.delete(
    "/{user_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete user",
    description="Deactivate a user (admin only)"
)
async def delete_user(
    user_id: str,
    current_user: User = Depends(require_roles(UserRole.SUPER_ADMIN, UserRole.ORG_ADMIN)),
    db: AsyncSession = Depends(get_db)
):
    """
    Deactivate a user (soft delete).

    Users cannot delete themselves.
    """
    if user_id == current_user.id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot delete your own account"
        )

    result = await db.execute(
        select(User).where(
            and_(
                User.id == user_id,
                User.org_id == current_user.org_id
            )
        )
    )
    user = result.scalar_one_or_none()

    if not user:
        raise NotFoundException("User", user_id)

    # Soft delete
    user.is_active = False
    await db.flush()


@router.post(
    "/{user_id}/activate",
    response_model=UserResponse,
    summary="Activate user",
    description="Reactivate a deactivated user (admin only)"
)
async def activate_user(
    user_id: str,
    current_user: User = Depends(require_roles(UserRole.SUPER_ADMIN, UserRole.ORG_ADMIN)),
    db: AsyncSession = Depends(get_db)
):
    """Reactivate a deactivated user."""
    result = await db.execute(
        select(User).where(
            and_(
                User.id == user_id,
                User.org_id == current_user.org_id
            )
        )
    )
    user = result.scalar_one_or_none()

    if not user:
        raise NotFoundException("User", user_id)

    user.is_active = True
    await db.flush()
    await db.refresh(user)

    return UserResponse.model_validate(user)


@router.get(
    "/{user_id}/permissions",
    summary="Get user permissions",
    description="Get list of permissions for a user"
)
async def get_user_permissions(
    user_id: str,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """Get list of permissions for a user based on their role."""
    # Can view own permissions or admins can view any
    if user_id != current_user.id:
        if not has_permission(current_user.role, Permission.USERS_READ):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not authorized"
            )

    result = await db.execute(
        select(User).where(
            and_(
                User.id == user_id,
                User.org_id == current_user.org_id
            )
        )
    )
    user = result.scalar_one_or_none()

    if not user:
        raise NotFoundException("User", user_id)

    from app.core.permissions import get_permissions_list
    permissions = get_permissions_list(user.role)

    return {
        "user_id": user_id,
        "role": user.role.value,
        "permissions": permissions,
        "permission_count": len(permissions)
    }

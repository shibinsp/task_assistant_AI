"""
TaskPulse - AI Assistant - API Dependencies
FastAPI dependencies for authentication and authorization
"""

from typing import Optional
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.core.security import verify_token, TokenPayload
from app.core.exceptions import (
    AuthenticationException,
    InvalidTokenException,
    InactiveUserException,
    InsufficientPermissionsException
)
from app.models.user import User, UserRole


# OAuth2 scheme for token extraction
oauth2_scheme = OAuth2PasswordBearer(
    tokenUrl="/api/v1/auth/login",
    auto_error=False
)


async def get_current_user(
    token: Optional[str] = Depends(oauth2_scheme),
    db: AsyncSession = Depends(get_db)
) -> Optional[User]:
    """
    Get current user from JWT token.

    Returns None if no token or invalid token.
    Use get_current_active_user for endpoints that require authentication.
    """
    if not token:
        return None

    # Verify token
    payload = verify_token(token, token_type="access")
    if not payload:
        return None

    user_id = payload.get("sub")
    if not user_id:
        return None

    # Get user from database
    result = await db.execute(
        select(User).where(User.id == user_id)
    )
    user = result.scalar_one_or_none()

    return user


async def get_current_active_user(
    current_user: Optional[User] = Depends(get_current_user)
) -> User:
    """
    Get current active user.

    Raises exception if:
    - No token provided
    - Invalid token
    - User not found
    - User is inactive
    """
    if not current_user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
            headers={"WWW-Authenticate": "Bearer"}
        )

    if not current_user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User account is inactive"
        )

    return current_user


async def get_current_verified_user(
    current_user: User = Depends(get_current_active_user)
) -> User:
    """
    Get current user with verified email.

    Raises exception if email is not verified.
    """
    if not current_user.is_email_verified:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Email verification required"
        )

    return current_user


# ==================== Role-Based Access Dependencies ====================

def require_roles(*allowed_roles: UserRole):
    """
    Dependency factory that requires user to have one of the specified roles.

    Usage:
        @router.get("/admin-only")
        async def admin_endpoint(
            user: User = Depends(require_roles(UserRole.SUPER_ADMIN, UserRole.ORG_ADMIN))
        ):
            ...
    """
    async def role_checker(
        current_user: User = Depends(get_current_active_user)
    ) -> User:
        if current_user.role not in allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Insufficient permissions. Required roles: {[r.value for r in allowed_roles]}"
            )
        return current_user

    return role_checker


def require_admin():
    """Require user to be an admin (super_admin or org_admin)."""
    return require_roles(UserRole.SUPER_ADMIN, UserRole.ORG_ADMIN)


def require_manager_or_above():
    """Require user to be manager or above."""
    return require_roles(
        UserRole.SUPER_ADMIN,
        UserRole.ORG_ADMIN,
        UserRole.MANAGER,
        UserRole.TEAM_LEAD
    )


def require_super_admin():
    """Require user to be a super admin."""
    return require_roles(UserRole.SUPER_ADMIN)


# ==================== Organization Access Dependencies ====================

async def verify_org_access(
    org_id: str,
    current_user: User = Depends(get_current_active_user)
) -> User:
    """
    Verify user has access to the specified organization.

    Super admins can access any organization.
    Other users can only access their own organization.
    """
    if current_user.role == UserRole.SUPER_ADMIN:
        return current_user

    if current_user.org_id != org_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You don't have access to this organization"
        )

    return current_user


class OrgAccessChecker:
    """
    Dependency class for checking organization access.

    Usage:
        @router.get("/orgs/{org_id}/users")
        async def get_org_users(
            org_id: str,
            current_user: User = Depends(OrgAccessChecker())
        ):
            ...
    """

    def __init__(self, allow_super_admin: bool = True):
        self.allow_super_admin = allow_super_admin

    async def __call__(
        self,
        org_id: str,
        current_user: User = Depends(get_current_active_user)
    ) -> User:
        if self.allow_super_admin and current_user.role == UserRole.SUPER_ADMIN:
            return current_user

        if current_user.org_id != org_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You don't have access to this organization"
            )

        return current_user


# ==================== Resource Access Dependencies ====================

class ResourceOwnerChecker:
    """
    Dependency class for checking resource ownership.

    Allows:
    - Super admins and org admins to access any resource in their org
    - Managers to access resources of their team members
    - Users to access their own resources
    """

    def __init__(
        self,
        allow_managers: bool = True,
        allow_admins: bool = True
    ):
        self.allow_managers = allow_managers
        self.allow_admins = allow_admins

    async def __call__(
        self,
        user_id: str,
        current_user: User = Depends(get_current_active_user),
        db: AsyncSession = Depends(get_db)
    ) -> User:
        # User accessing own resource
        if current_user.id == user_id:
            return current_user

        # Admins can access all
        if self.allow_admins and current_user.role in (
            UserRole.SUPER_ADMIN,
            UserRole.ORG_ADMIN
        ):
            # Verify same org for org admins
            if current_user.role == UserRole.ORG_ADMIN:
                result = await db.execute(
                    select(User).where(User.id == user_id)
                )
                target_user = result.scalar_one_or_none()
                if target_user and target_user.org_id == current_user.org_id:
                    return current_user

            elif current_user.role == UserRole.SUPER_ADMIN:
                return current_user

        # Managers can access their direct reports
        if self.allow_managers and current_user.role in (
            UserRole.MANAGER,
            UserRole.TEAM_LEAD
        ):
            result = await db.execute(
                select(User).where(User.id == user_id)
            )
            target_user = result.scalar_one_or_none()
            if target_user and target_user.manager_id == current_user.id:
                return current_user

        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You don't have access to this resource"
        )


# ==================== Consent Dependencies ====================

async def require_ai_monitoring_consent(
    current_user: User = Depends(get_current_active_user)
) -> User:
    """Require user to have consented to AI monitoring."""
    if not current_user.has_ai_monitoring_consent:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="AI monitoring consent required for this feature"
        )
    return current_user


async def require_skill_tracking_consent(
    current_user: User = Depends(get_current_active_user)
) -> User:
    """Require user to have consented to skill tracking."""
    if not current_user.has_skill_tracking_consent:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Skill tracking consent required for this feature"
        )
    return current_user


# ==================== Pagination Dependencies ====================

class PaginationParams:
    """Pagination parameters dependency."""

    def __init__(
        self,
        page: int = 1,
        page_size: int = 20
    ):
        from app.config import settings

        self.page = max(1, page)
        self.page_size = min(max(1, page_size), settings.MAX_PAGE_SIZE)
        self.skip = (self.page - 1) * self.page_size
        self.limit = self.page_size


def get_pagination(
    page: int = 1,
    page_size: int = 20
) -> PaginationParams:
    """Get pagination parameters."""
    return PaginationParams(page=page, page_size=page_size)

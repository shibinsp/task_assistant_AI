"""
TaskPulse - AI Assistant - Authentication API
Endpoints for user authentication via Supabase Auth
"""

from fastapi import APIRouter, Depends, Request, status
from sqlalchemy.ext.asyncio import AsyncSession

from pydantic import BaseModel, Field

from app.database import get_db
from app.services.auth_service import AuthService
from app.schemas.user import (
    UserRegister,
    UserLogin,
    PasswordReset,
    PasswordChange,
    UserResponse,
    CurrentUserResponse,
    ConsentUpdate,
    ConsentResponse,
)
from app.api.v1.dependencies import get_current_active_user
from app.models.user import User


router = APIRouter()


# ==================== Request/Response Models ====================

class RefreshTokenRequest(BaseModel):
    """Request body for token refresh."""
    refresh_token: str = Field(..., description="Supabase refresh token")


# ==================== Registration & Login ====================

@router.post(
    "/register",
    response_model=dict,
    status_code=status.HTTP_201_CREATED,
    summary="Register new user",
    description="Register a new user via Supabase Auth. Creates new organization if org_name provided, or joins existing if org_id provided.",
)
async def register(
    user_data: UserRegister,
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    """
    Register a new user account.

    - **email**: User's email address (must be unique)
    - **password**: Strong password (min 8 chars, mixed case, digit)
    - **first_name**: User's first name
    - **last_name**: User's last name
    - **org_name**: Name for new organization (creates user as admin)
    - **org_id**: ID of existing organization to join
    """
    auth_service = AuthService(db)

    ip_address = request.client.host if request.client else None
    user_agent = request.headers.get("User-Agent")

    user, org = await auth_service.register(
        user_data,
        ip_address=ip_address,
        user_agent=user_agent,
    )

    return {
        "message": "Registration successful",
        "user": UserResponse.model_validate(user),
        "organization": {
            "id": org.id,
            "name": org.name,
            "slug": org.slug,
        },
    }


@router.post(
    "/login",
    response_model=dict,
    summary="User login",
    description="Authenticate user with email and password via Supabase Auth",
)
async def login(
    credentials: UserLogin,
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    """
    Authenticate user and get Supabase session tokens.

    - **email**: User's email address
    - **password**: User's password

    Returns user info and Supabase access/refresh tokens.
    """
    auth_service = AuthService(db)

    ip_address = request.client.host if request.client else None
    user_agent = request.headers.get("User-Agent")

    user, supabase_session = await auth_service.login(
        email=credentials.email,
        password=credentials.password,
        ip_address=ip_address,
        user_agent=user_agent,
    )

    return {
        "message": "Login successful",
        "user": UserResponse.model_validate(user),
        "tokens": supabase_session,
    }


@router.post(
    "/refresh",
    response_model=dict,
    summary="Refresh tokens",
    description="Get new Supabase session tokens using refresh token",
)
async def refresh_token(
    token_data: RefreshTokenRequest,
    db: AsyncSession = Depends(get_db),
):
    """
    Refresh access token using Supabase refresh token.

    - **refresh_token**: Valid refresh token from login

    Returns new access and refresh tokens.
    """
    auth_service = AuthService(db)
    tokens = await auth_service.refresh_tokens(
        refresh_token=token_data.refresh_token,
    )

    return {
        "message": "Tokens refreshed",
        "tokens": tokens,
    }


@router.post(
    "/logout",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Logout",
    description="Logout current session (frontend calls supabase.auth.signOut())",
)
async def logout(
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Logout from current session.

    The frontend is responsible for calling supabase.auth.signOut().
    This endpoint logs the event server-side.
    """
    auth_service = AuthService(db)
    await auth_service.logout(current_user.id)


# ==================== Password Management ====================

@router.post(
    "/forgot-password",
    summary="Request password reset",
    description="Send password reset email via Supabase",
)
async def forgot_password(
    data: PasswordReset,
    db: AsyncSession = Depends(get_db),
):
    """
    Request password reset.

    - **email**: User's email address

    Supabase sends a reset link to the user's email.
    Always returns success to prevent email enumeration.
    """
    auth_service = AuthService(db)
    await auth_service.request_password_reset(data.email)

    return {"message": "If the email exists, a reset link has been sent"}


@router.post(
    "/change-password",
    summary="Change password",
    description="Change password for authenticated user via Supabase",
)
async def change_password(
    data: PasswordChange,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Change password for current user.

    - **new_password**: New strong password

    Uses Supabase admin API to update the password.
    """
    auth_service = AuthService(db)
    await auth_service.change_password(
        user_id=current_user.id,
        current_password=data.current_password,
        new_password=data.new_password,
    )

    return {"message": "Password changed successfully"}


# ==================== Current User ====================

@router.get(
    "/me",
    response_model=CurrentUserResponse,
    summary="Get current user",
    description="Get details of authenticated user",
)
async def get_current_user_info(
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Get current authenticated user's profile.

    Returns user details including organization and permissions.
    """
    from app.models.organization import Organization
    from sqlalchemy import select

    result = await db.execute(
        select(Organization).where(Organization.id == current_user.org_id)
    )
    org = result.scalar_one_or_none()

    permissions = _get_role_permissions(current_user.role.value)

    return CurrentUserResponse(
        id=current_user.id,
        org_id=current_user.org_id,
        email=current_user.email,
        first_name=current_user.first_name,
        last_name=current_user.last_name,
        role=current_user.role,
        skill_level=current_user.skill_level,
        timezone=current_user.timezone,
        is_active=current_user.is_active,
        is_email_verified=current_user.is_email_verified,
        avatar_url=current_user.avatar_url,
        phone=current_user.phone,
        team_id=current_user.team_id,
        manager_id=current_user.manager_id,
        last_login=current_user.last_login,
        consent=ConsentResponse(**current_user.consent),
        created_at=current_user.created_at,
        updated_at=current_user.updated_at,
        organization_name=org.name if org else "",
        organization_plan=org.plan.value if org else "",
        permissions=permissions,
    )


# ==================== Consent Management ====================

@router.get(
    "/consent",
    response_model=ConsentResponse,
    summary="Get consent status",
    description="Get current user's consent settings",
)
async def get_consent(
    current_user: User = Depends(get_current_active_user),
):
    """Get current user's GDPR consent status."""
    return ConsentResponse(**current_user.consent)


@router.patch(
    "/consent",
    response_model=ConsentResponse,
    summary="Update consent",
    description="Update user consent settings",
)
async def update_consent(
    consent_data: ConsentUpdate,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Update GDPR consent settings.

    - **ai_monitoring**: Consent for AI monitoring features
    - **skill_tracking**: Consent for skill tracking
    - **analytics**: Consent for analytics
    - **marketing**: Consent for marketing communications
    """
    auth_service = AuthService(db)
    user = await auth_service.update_consent(current_user.id, consent_data)

    return ConsentResponse(**user.consent)


# ==================== Helper Functions ====================

def _get_role_permissions(role: str) -> list[str]:
    """Get list of permissions for a role."""
    permissions_map = {
        "super_admin": [
            "users:read", "users:write", "users:delete",
            "organizations:read", "organizations:write",
            "tasks:read", "tasks:write", "tasks:delete",
            "reports:read", "reports:write",
            "admin:access",
        ],
        "org_admin": [
            "users:read", "users:write",
            "organizations:read", "organizations:write",
            "tasks:read", "tasks:write", "tasks:delete",
            "reports:read", "reports:write",
        ],
        "manager": [
            "users:read",
            "tasks:read", "tasks:write",
            "reports:read",
        ],
        "team_lead": [
            "users:read",
            "tasks:read", "tasks:write",
            "reports:read",
        ],
        "employee": [
            "tasks:read", "tasks:write_own",
            "reports:read_own",
        ],
        "viewer": [
            "tasks:read",
            "reports:read",
        ],
    }

    return permissions_map.get(role, [])

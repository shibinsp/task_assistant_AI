"""
TaskPulse - AI Assistant - Authentication API
Endpoints for user authentication and session management
"""

from typing import Optional
from fastapi import APIRouter, Depends, Request, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.config import settings
from app.services.auth_service import AuthService
from app.schemas.user import (
    UserRegister,
    UserLogin,
    TokenResponse,
    TokenRefresh,
    PasswordReset,
    PasswordResetConfirm,
    PasswordChange,
    UserResponse,
    CurrentUserResponse,
    ConsentUpdate,
    ConsentResponse,
    SessionResponse,
    SessionListResponse
)
from app.api.v1.dependencies import get_current_user, get_current_active_user
from app.models.user import User


router = APIRouter()


# ==================== Registration & Login ====================

@router.post(
    "/register",
    response_model=dict,
    status_code=status.HTTP_201_CREATED,
    summary="Register new user",
    description="Register a new user. Creates new organization if org_name provided, or joins existing if org_id provided."
)
async def register(
    user_data: UserRegister,
    request: Request,
    db: AsyncSession = Depends(get_db)
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

    # Get client info
    ip_address = request.client.host if request.client else None
    user_agent = request.headers.get("User-Agent")

    user, org, tokens = await auth_service.register(
        user_data,
        ip_address=ip_address,
        user_agent=user_agent
    )

    return {
        "message": "Registration successful",
        "user": UserResponse.model_validate(user),
        "organization": {
            "id": org.id,
            "name": org.name,
            "slug": org.slug
        },
        "tokens": tokens
    }


@router.post(
    "/login",
    response_model=dict,
    summary="User login",
    description="Authenticate user with email and password"
)
async def login(
    credentials: UserLogin,
    request: Request,
    db: AsyncSession = Depends(get_db)
):
    """
    Authenticate user and get access tokens.

    - **email**: User's email address
    - **password**: User's password

    Returns access and refresh tokens for API authentication.
    """
    auth_service = AuthService(db)

    # Get client info
    ip_address = request.client.host if request.client else None
    user_agent = request.headers.get("User-Agent")

    user, tokens = await auth_service.login(
        email=credentials.email,
        password=credentials.password,
        ip_address=ip_address,
        user_agent=user_agent
    )

    return {
        "message": "Login successful",
        "user": UserResponse.model_validate(user),
        "tokens": tokens
    }


@router.post(
    "/refresh",
    response_model=TokenResponse,
    summary="Refresh tokens",
    description="Get new access token using refresh token"
)
async def refresh_token(
    token_data: TokenRefresh,
    request: Request,
    db: AsyncSession = Depends(get_db)
):
    """
    Refresh access token using refresh token.

    - **refresh_token**: Valid refresh token from login

    Returns new access and refresh tokens.
    """
    auth_service = AuthService(db)

    ip_address = request.client.host if request.client else None

    tokens = await auth_service.refresh_tokens(
        refresh_token=token_data.refresh_token,
        ip_address=ip_address
    )

    return tokens


@router.post(
    "/logout",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Logout",
    description="Logout current session"
)
async def logout(
    request: Request,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Logout from current session.

    Invalidates the current access token.
    """
    auth_service = AuthService(db)

    # Get token from header
    auth_header = request.headers.get("Authorization", "")
    token = auth_header.replace("Bearer ", "") if auth_header.startswith("Bearer ") else ""

    await auth_service.logout(current_user.id, token)


@router.post(
    "/logout-all",
    summary="Logout all sessions",
    description="Logout from all active sessions"
)
async def logout_all(
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Logout from all active sessions.

    Invalidates all tokens for the current user.
    """
    auth_service = AuthService(db)
    count = await auth_service.logout_all(current_user.id)

    return {
        "message": f"Logged out from {count} session(s)"
    }


# ==================== Password Management ====================

@router.post(
    "/forgot-password",
    summary="Request password reset",
    description="Send password reset email"
)
async def forgot_password(
    data: PasswordReset,
    db: AsyncSession = Depends(get_db)
):
    """
    Request password reset token.

    - **email**: User's email address

    Note: Always returns success to prevent email enumeration.
    In production, sends email with reset link.
    """
    auth_service = AuthService(db)
    token = await auth_service.request_password_reset(data.email)

    response = {"message": "If the email exists, a reset link has been sent"}

    # Only include token in development for testing purposes
    # NEVER expose in production - tokens should only be sent via email
    if settings.is_development and settings.DEBUG:
        response["debug_token"] = token

    return response


@router.post(
    "/reset-password",
    summary="Reset password",
    description="Reset password using reset token"
)
async def reset_password(
    data: PasswordResetConfirm,
    db: AsyncSession = Depends(get_db)
):
    """
    Reset password using reset token.

    - **token**: Password reset token from email
    - **new_password**: New strong password
    """
    auth_service = AuthService(db)
    await auth_service.reset_password(data.token, data.new_password)

    return {
        "message": "Password reset successful. Please login with your new password."
    }


@router.post(
    "/change-password",
    summary="Change password",
    description="Change password for authenticated user"
)
async def change_password(
    data: PasswordChange,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Change password for current user.

    - **current_password**: Current password
    - **new_password**: New strong password
    """
    auth_service = AuthService(db)
    await auth_service.change_password(
        user_id=current_user.id,
        current_password=data.current_password,
        new_password=data.new_password
    )

    return {
        "message": "Password changed successfully"
    }


# ==================== Current User ====================

@router.get(
    "/me",
    response_model=CurrentUserResponse,
    summary="Get current user",
    description="Get details of authenticated user"
)
async def get_current_user_info(
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Get current authenticated user's profile.

    Returns user details including organization and permissions.
    """
    # Get organization info
    from app.models.organization import Organization
    from sqlalchemy import select

    result = await db.execute(
        select(Organization).where(Organization.id == current_user.org_id)
    )
    org = result.scalar_one_or_none()

    # Build permissions list based on role
    # This will be expanded in Phase 3 (RBAC)
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
        permissions=permissions
    )


# ==================== Consent Management ====================

@router.get(
    "/consent",
    response_model=ConsentResponse,
    summary="Get consent status",
    description="Get current user's consent settings"
)
async def get_consent(
    current_user: User = Depends(get_current_active_user)
):
    """Get current user's GDPR consent status."""
    return ConsentResponse(**current_user.consent)


@router.patch(
    "/consent",
    response_model=ConsentResponse,
    summary="Update consent",
    description="Update user consent settings"
)
async def update_consent(
    consent_data: ConsentUpdate,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
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


# ==================== Session Management ====================

@router.get(
    "/sessions",
    response_model=SessionListResponse,
    summary="List sessions",
    description="List all active sessions for current user"
)
async def list_sessions(
    request: Request,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """Get all active sessions for current user."""
    auth_service = AuthService(db)

    # Get current token
    auth_header = request.headers.get("Authorization", "")
    current_token = auth_header.replace("Bearer ", "") if auth_header.startswith("Bearer ") else ""

    sessions = await auth_service.get_user_sessions(current_user.id, current_token)

    # Mark current session
    from app.core.security import hash_token
    current_hash = hash_token(current_token) if current_token else ""

    session_responses = []
    for session in sessions:
        session_responses.append(SessionResponse(
            id=session.id,
            device_info=session.device_info,
            ip_address=session.ip_address,
            last_activity=session.last_activity,
            created_at=session.created_at,
            is_current=session.token_hash == current_hash
        ))

    return SessionListResponse(
        sessions=session_responses,
        total=len(session_responses)
    )


# ==================== Helper Functions ====================

def _get_role_permissions(role: str) -> list[str]:
    """Get list of permissions for a role."""
    # Basic permission mapping - will be expanded in Phase 3
    permissions_map = {
        "super_admin": [
            "users:read", "users:write", "users:delete",
            "organizations:read", "organizations:write",
            "tasks:read", "tasks:write", "tasks:delete",
            "reports:read", "reports:write",
            "admin:access"
        ],
        "org_admin": [
            "users:read", "users:write",
            "organizations:read", "organizations:write",
            "tasks:read", "tasks:write", "tasks:delete",
            "reports:read", "reports:write"
        ],
        "manager": [
            "users:read",
            "tasks:read", "tasks:write",
            "reports:read"
        ],
        "team_lead": [
            "users:read",
            "tasks:read", "tasks:write",
            "reports:read"
        ],
        "employee": [
            "tasks:read", "tasks:write_own",
            "reports:read_own"
        ],
        "viewer": [
            "tasks:read",
            "reports:read"
        ]
    }

    return permissions_map.get(role, [])

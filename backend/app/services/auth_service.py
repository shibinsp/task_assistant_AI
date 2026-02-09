"""
TaskPulse - AI Assistant - Authentication Service
Business logic for user authentication and session management
"""

from datetime import datetime, timedelta, timezone
from typing import Optional, Tuple
import logging

from sqlalchemy import select, and_, or_
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.core.security import (
    hash_password,
    verify_password,
    create_access_token,
    create_refresh_token,
    verify_token,
    hash_token,
    generate_password_reset_token,
    verify_password_reset_token
)
from app.core.exceptions import (
    InvalidCredentialsException,
    AlreadyExistsException,
    NotFoundException,
    InactiveUserException,
    InvalidTokenException,
    TokenExpiredException,
    AccountLockedException,
    ValidationException
)
from app.models.user import User, Session, UserRole
from app.models.organization import Organization, PlanTier
from app.schemas.user import (
    UserRegister,
    UserCreate,
    TokenResponse,
    ConsentUpdate
)
from app.utils.helpers import generate_uuid, slugify

logger = logging.getLogger(__name__)


class AuthService:
    """Service for authentication operations."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def register(
        self,
        user_data: UserRegister,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None
    ) -> Tuple[User, Organization, TokenResponse]:
        """
        Register a new user and optionally create an organization.

        Args:
            user_data: Registration data
            ip_address: Client IP address
            user_agent: Client user agent

        Returns:
            Tuple of (User, Organization, TokenResponse)
        """
        # Check if email already exists
        existing_user = await self._get_user_by_email(user_data.email)
        if existing_user:
            raise AlreadyExistsException("User", "email", user_data.email)

        # Determine organization
        if user_data.org_id:
            # Join existing organization
            org = await self._get_organization_by_id(user_data.org_id)
            if not org:
                raise NotFoundException("Organization", user_data.org_id)
            role = UserRole.EMPLOYEE
        elif user_data.org_name:
            # Create new organization
            org = await self._create_organization(user_data.org_name)
            role = UserRole.ORG_ADMIN  # Creator becomes admin
        else:
            raise ValidationException(
                "Either org_name (for new org) or org_id (to join) is required"
            )

        # Create user
        user = User(
            id=generate_uuid(),
            org_id=org.id,
            email=user_data.email.lower(),
            password_hash=hash_password(user_data.password),
            first_name=user_data.first_name,
            last_name=user_data.last_name,
            role=role,
            is_active=True,
            is_email_verified=False  # Would send verification email in production
        )

        self.db.add(user)
        await self.db.flush()

        # Create session and tokens
        tokens = await self._create_session(
            user,
            ip_address=ip_address,
            user_agent=user_agent
        )

        logger.info(f"User registered: {user.email} in org {org.name}")

        return user, org, tokens

    async def login(
        self,
        email: str,
        password: str,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None
    ) -> Tuple[User, TokenResponse]:
        """
        Authenticate user and create session.

        Args:
            email: User email
            password: User password
            ip_address: Client IP address
            user_agent: Client user agent

        Returns:
            Tuple of (User, TokenResponse)
        """
        # Get user by email
        user = await self._get_user_by_email(email)

        if not user:
            logger.warning(f"Login attempt for non-existent user: {email}")
            raise InvalidCredentialsException()

        # Check if user is active
        if not user.is_active:
            logger.warning(f"Login attempt for inactive user: {email}")
            raise InactiveUserException()

        # Check if account is locked
        if user.lockout_until and user.lockout_until > datetime.utcnow():
            logger.warning(f"Login attempt for locked account: {email}")
            raise AccountLockedException()

        # Verify password
        if not user.password_hash or not verify_password(password, user.password_hash):
            # Track failed attempt
            await self._record_failed_login(user)
            logger.warning(f"Failed login attempt for user: {email}")
            raise InvalidCredentialsException()

        # Reset failed attempts and lockout on successful login
        user.failed_login_attempts = "0"
        user.lockout_until = None
        user.last_login = datetime.utcnow()

        # Create session and tokens
        tokens = await self._create_session(
            user,
            ip_address=ip_address,
            user_agent=user_agent
        )

        logger.info(f"User logged in: {user.email}")

        return user, tokens

    async def refresh_tokens(
        self,
        refresh_token: str,
        ip_address: Optional[str] = None
    ) -> TokenResponse:
        """
        Refresh access token using refresh token.

        Args:
            refresh_token: JWT refresh token
            ip_address: Client IP address

        Returns:
            New TokenResponse
        """
        # Verify refresh token
        payload = verify_token(refresh_token, token_type="refresh")
        if not payload:
            raise InvalidTokenException("Invalid refresh token")

        user_id = payload.get("sub")
        if not user_id:
            raise InvalidTokenException("Invalid token payload")

        # Get user
        user = await self._get_user_by_id(user_id)
        if not user:
            raise InvalidTokenException("User not found")

        if not user.is_active:
            raise InactiveUserException()

        # Verify session exists
        token_hash = hash_token(refresh_token)
        session = await self._get_session_by_refresh_token(token_hash)
        if not session or not session.is_valid:
            raise InvalidTokenException("Session expired or invalid")

        # Create new tokens
        tokens = self._generate_tokens(user)

        # Update session
        session.token_hash = hash_token(tokens.access_token)
        session.refresh_token_hash = hash_token(tokens.refresh_token)
        session.last_activity = datetime.utcnow()
        session.expires_at = datetime.utcnow() + timedelta(
            minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES
        )
        session.refresh_expires_at = datetime.utcnow() + timedelta(
            days=settings.REFRESH_TOKEN_EXPIRE_DAYS
        )

        logger.info(f"Tokens refreshed for user: {user.email}")

        return tokens

    async def logout(self, user_id: str, token: str) -> None:
        """
        Logout user by invalidating session.

        Args:
            user_id: User ID
            token: Current access token
        """
        token_hash = hash_token(token)
        session = await self._get_session_by_token(token_hash)

        if session:
            session.is_active = False
            logger.info(f"User logged out: {user_id}")

    async def logout_all(self, user_id: str) -> int:
        """
        Logout user from all sessions.

        Args:
            user_id: User ID

        Returns:
            Number of sessions invalidated
        """
        result = await self.db.execute(
            select(Session).where(
                and_(
                    Session.user_id == user_id,
                    Session.is_active == True
                )
            )
        )
        sessions = result.scalars().all()

        count = 0
        for session in sessions:
            session.is_active = False
            count += 1

        logger.info(f"Logged out user {user_id} from {count} sessions")
        return count

    async def request_password_reset(self, email: str) -> str:
        """
        Generate password reset token.

        Args:
            email: User email

        Returns:
            Password reset token
        """
        user = await self._get_user_by_email(email)

        # Always return success to prevent email enumeration
        if not user:
            logger.info(f"Password reset requested for non-existent email: {email}")
            return generate_password_reset_token(email)

        token = generate_password_reset_token(email)
        logger.info(f"Password reset requested for user: {email}")

        # In production, send email here
        return token

    async def reset_password(self, token: str, new_password: str) -> User:
        """
        Reset user password using reset token.

        Args:
            token: Password reset token
            new_password: New password

        Returns:
            Updated User
        """
        email = verify_password_reset_token(token)
        if not email:
            raise InvalidTokenException("Invalid or expired reset token")

        user = await self._get_user_by_email(email)
        if not user:
            raise NotFoundException("User")

        # Update password
        user.password_hash = hash_password(new_password)
        user.failed_login_attempts = "0"

        # Invalidate all sessions
        await self.logout_all(user.id)

        logger.info(f"Password reset for user: {email}")

        return user

    async def change_password(
        self,
        user_id: str,
        current_password: str,
        new_password: str
    ) -> User:
        """
        Change user password.

        Args:
            user_id: User ID
            current_password: Current password
            new_password: New password

        Returns:
            Updated User
        """
        user = await self._get_user_by_id(user_id)
        if not user:
            raise NotFoundException("User", user_id)

        # Verify current password
        if not verify_password(current_password, user.password_hash):
            raise InvalidCredentialsException("Current password is incorrect")

        # Update password
        user.password_hash = hash_password(new_password)

        logger.info(f"Password changed for user: {user.email}")

        return user

    async def update_consent(
        self,
        user_id: str,
        consent_data: ConsentUpdate
    ) -> User:
        """
        Update user consent settings.

        Args:
            user_id: User ID
            consent_data: Consent update data

        Returns:
            Updated User
        """
        user = await self._get_user_by_id(user_id)
        if not user:
            raise NotFoundException("User", user_id)

        consent_dict = consent_data.model_dump(exclude_unset=True)
        for key, value in consent_dict.items():
            if value is not None:
                user.update_consent(key, value)

        logger.info(f"Consent updated for user: {user.email}")

        return user

    async def get_user_sessions(
        self,
        user_id: str,
        current_token: str
    ) -> list[Session]:
        """
        Get all active sessions for a user.

        Args:
            user_id: User ID
            current_token: Current access token (to mark current session)

        Returns:
            List of Sessions
        """
        result = await self.db.execute(
            select(Session).where(
                and_(
                    Session.user_id == user_id,
                    Session.is_active == True,
                    Session.expires_at > datetime.utcnow()
                )
            ).order_by(Session.last_activity.desc())
        )
        return list(result.scalars().all())

    # ==================== Private Helper Methods ====================

    async def _get_user_by_email(self, email: str) -> Optional[User]:
        """Get user by email."""
        result = await self.db.execute(
            select(User).where(User.email == email.lower())
        )
        return result.scalar_one_or_none()

    async def _get_user_by_id(self, user_id: str) -> Optional[User]:
        """Get user by ID."""
        result = await self.db.execute(
            select(User).where(User.id == user_id)
        )
        return result.scalar_one_or_none()

    async def _get_organization_by_id(self, org_id: str) -> Optional[Organization]:
        """Get organization by ID."""
        result = await self.db.execute(
            select(Organization).where(Organization.id == org_id)
        )
        return result.scalar_one_or_none()

    async def _create_organization(self, name: str) -> Organization:
        """Create a new organization."""
        # Generate unique slug
        base_slug = slugify(name)
        slug = base_slug
        counter = 1

        while True:
            existing = await self.db.execute(
                select(Organization).where(Organization.slug == slug)
            )
            if not existing.scalar_one_or_none():
                break
            slug = f"{base_slug}-{counter}"
            counter += 1

        org = Organization(
            id=generate_uuid(),
            name=name,
            slug=slug,
            plan=PlanTier.STARTER,
            is_active=True
        )

        self.db.add(org)
        await self.db.flush()

        logger.info(f"Organization created: {name} ({slug})")

        return org

    async def _create_session(
        self,
        user: User,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None
    ) -> TokenResponse:
        """Create a new session for user."""
        tokens = self._generate_tokens(user)

        session = Session(
            id=generate_uuid(),
            user_id=user.id,
            token_hash=hash_token(tokens.access_token),
            refresh_token_hash=hash_token(tokens.refresh_token),
            ip_address=ip_address,
            user_agent=user_agent,
            expires_at=datetime.utcnow() + timedelta(
                minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES
            ),
            refresh_expires_at=datetime.utcnow() + timedelta(
                days=settings.REFRESH_TOKEN_EXPIRE_DAYS
            ),
            is_active=True
        )

        self.db.add(session)
        await self.db.flush()

        return tokens

    def _generate_tokens(self, user: User) -> TokenResponse:
        """Generate access and refresh tokens for user."""
        token_data = {
            "sub": user.id,
            "email": user.email,
            "org_id": user.org_id,
            "role": user.role.value
        }

        access_token = create_access_token(token_data)
        refresh_token = create_refresh_token(token_data)

        return TokenResponse(
            access_token=access_token,
            refresh_token=refresh_token,
            token_type="bearer",
            expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60
        )

    async def _get_session_by_token(self, token_hash: str) -> Optional[Session]:
        """Get session by access token hash."""
        result = await self.db.execute(
            select(Session).where(Session.token_hash == token_hash)
        )
        return result.scalar_one_or_none()

    async def _get_session_by_refresh_token(
        self,
        refresh_token_hash: str
    ) -> Optional[Session]:
        """Get session by refresh token hash."""
        result = await self.db.execute(
            select(Session).where(Session.refresh_token_hash == refresh_token_hash)
        )
        return result.scalar_one_or_none()

    async def _record_failed_login(self, user: User) -> None:
        """Record failed login attempt and implement account lockout."""
        try:
            attempts = int(user.failed_login_attempts or "0")
        except ValueError:
            attempts = 0

        attempts += 1
        user.failed_login_attempts = str(attempts)

        # Implement progressive lockout after 5 failed attempts
        if attempts >= 5:
            # Lock account for 15 minutes
            lockout_duration = timedelta(minutes=15)
            user.lockout_until = datetime.utcnow() + lockout_duration
            logger.warning(
                f"Account locked for user {user.email} after {attempts} failed attempts. "
                f"Locked until {user.lockout_until}"
            )

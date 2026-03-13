"""
TaskPulse - AI Assistant - Authentication Service
Business logic for user authentication via Supabase Auth
"""

import asyncio
from datetime import datetime, timezone
from typing import Optional, Tuple
import logging

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import (
    AlreadyExistsException,
    NotFoundException,
    InactiveUserException,
    InvalidCredentialsException,
    ValidationException,
)
from app.models.user import User, UserRole
from app.models.organization import Organization, PlanTier
from app.schemas.user import (
    UserRegister,
    ConsentUpdate,
)
from app.supabase_client import get_supabase_client
from app.utils.helpers import generate_uuid, slugify

logger = logging.getLogger(__name__)


class AuthService:
    """Service for authentication operations via Supabase Auth."""

    def __init__(self, db: AsyncSession):
        self.db = db
        self.supabase = get_supabase_client()

    # ==================== Public Methods ====================

    async def register(
        self,
        user_data: UserRegister,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
    ) -> Tuple[User, Organization]:
        """
        Register a new user via Supabase Auth and create local records.

        Args:
            user_data: Registration data
            ip_address: Client IP address
            user_agent: Client user agent

        Returns:
            Tuple of (User, Organization)
        """
        # Check if email already exists locally
        existing_user = await self._get_user_by_email(user_data.email)
        if existing_user:
            raise AlreadyExistsException("User", "email", user_data.email)

        # Create user in Supabase Auth
        try:
            supabase_response = await asyncio.to_thread(
                self.supabase.auth.admin.create_user,
                {
                    "email": user_data.email,
                    "password": user_data.password,
                    "email_confirm": True,
                },
            )
        except Exception as e:
            logger.error(f"Supabase user creation failed: {e}")
            raise ValidationException(f"Failed to create auth account: {e}")

        supabase_auth_id = supabase_response.user.id

        # Determine organization
        if user_data.org_id:
            # Join existing organization
            org = await self._get_organization_by_id(user_data.org_id)
            if not org:
                raise NotFoundException("Organization", user_data.org_id)
            role = user_data.role or UserRole.EMPLOYEE
        elif user_data.org_name:
            # Create new organization
            org = await self._create_organization(user_data.org_name)
            role = user_data.role or UserRole.ORG_ADMIN
        else:
            raise ValidationException(
                "Either org_name (for new org) or org_id (to join) is required"
            )

        # Create local user record (no password_hash — Supabase handles auth)
        user = User(
            id=generate_uuid(),
            org_id=org.id,
            email=user_data.email.lower(),
            supabase_auth_id=str(supabase_auth_id),
            first_name=user_data.first_name,
            last_name=user_data.last_name,
            role=role,
            is_active=True,
            is_email_verified=True,  # Supabase confirmed the email
        )

        self.db.add(user)
        await self.db.commit()

        logger.info(f"User registered: {user.email} in org {org.name}")

        return user, org

    async def login(
        self,
        email: str,
        password: str,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
    ) -> Tuple[User, dict]:
        """
        Authenticate user via Supabase Auth. Used for API/mobile clients.
        Frontend authenticates directly with Supabase; this is the backend fallback.

        Args:
            email: User email
            password: User password
            ip_address: Client IP address
            user_agent: Client user agent

        Returns:
            Tuple of (User, supabase_session_dict)
        """
        # Authenticate with Supabase
        try:
            supabase_response = await asyncio.to_thread(
                self.supabase.auth.sign_in_with_password,
                {"email": email, "password": password},
            )
        except Exception as e:
            logger.warning(f"Supabase login failed for {email}: {e}")
            raise InvalidCredentialsException()

        # Look up local user
        user = await self._get_user_by_email(email)
        if not user:
            logger.warning(f"Login: no local user for {email}")
            raise InvalidCredentialsException()

        if not user.is_active:
            logger.warning(f"Login attempt for inactive user: {email}")
            raise InactiveUserException()

        # Update last_login
        user.last_login = datetime.now(timezone.utc)
        await self.db.commit()

        logger.info(f"User logged in: {user.email}")

        # Build session dict from Supabase response
        session = supabase_response.session
        supabase_session = {
            "access_token": session.access_token,
            "refresh_token": session.refresh_token,
            "token_type": "bearer",
            "expires_in": session.expires_in,
        }

        return user, supabase_session

    async def refresh_tokens(self, refresh_token: str) -> dict:
        """
        Refresh Supabase session tokens.

        Args:
            refresh_token: Supabase refresh token

        Returns:
            Dict with new access_token, refresh_token, token_type, expires_in
        """
        try:
            supabase_response = await asyncio.to_thread(
                self.supabase.auth.refresh_session,
                refresh_token,
            )
        except Exception as e:
            logger.warning(f"Token refresh failed: {e}")
            raise InvalidCredentialsException("Invalid or expired refresh token")

        session = supabase_response.session
        return {
            "access_token": session.access_token,
            "refresh_token": session.refresh_token,
            "token_type": "bearer",
            "expires_in": session.expires_in,
        }

    async def logout(self, user_id: str) -> None:
        """
        Log the logout event. Frontend calls supabase.auth.signOut() directly.

        Args:
            user_id: User ID
        """
        logger.info(f"User logged out: {user_id}")

    async def request_password_reset(self, email: str) -> None:
        """
        Request password reset via Supabase (sends email).

        Args:
            email: User email
        """
        try:
            await asyncio.to_thread(
                self.supabase.auth.reset_password_for_email,
                email,
            )
        except Exception as e:
            # Log but don't reveal whether email exists
            logger.info(f"Password reset requested for {email}: {e}")

        logger.info(f"Password reset requested for: {email}")

    async def change_password(
        self,
        user_id: str,
        new_password: str,
    ) -> User:
        """
        Change user password via Supabase admin API.

        Args:
            user_id: Local user ID
            new_password: New password

        Returns:
            Updated User
        """
        user = await self._get_user_by_id(user_id)
        if not user:
            raise NotFoundException("User", user_id)

        if not user.supabase_auth_id:
            raise ValidationException("User does not have a Supabase auth account")

        try:
            await asyncio.to_thread(
                self.supabase.auth.admin.update_user_by_id,
                str(user.supabase_auth_id),
                {"password": new_password},
            )
        except Exception as e:
            logger.error(f"Supabase password change failed: {e}")
            raise ValidationException(f"Failed to change password: {e}")

        logger.info(f"Password changed for user: {user.email}")

        return user

    async def update_consent(
        self,
        user_id: str,
        consent_data: ConsentUpdate,
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

    async def _get_user_by_supabase_id(self, supabase_id: str) -> Optional[User]:
        """Get user by Supabase auth ID."""
        result = await self.db.execute(
            select(User).where(User.supabase_auth_id == supabase_id)
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
            is_active=True,
        )

        self.db.add(org)
        await self.db.flush()

        logger.info(f"Organization created: {name} ({slug})")

        return org

"""
TaskPulse - AI Assistant - Permissions System
Granular role-based access control (RBAC) implementation
"""

from enum import Enum
from typing import Optional, Set
from functools import wraps

from fastapi import HTTPException, status

from app.models.user import UserRole


class Permission(str, Enum):
    """All available permissions in the system."""

    # User Management
    USERS_CREATE = "users:create"
    USERS_READ = "users:read"
    USERS_READ_OWN = "users:read_own"
    USERS_UPDATE = "users:update"
    USERS_UPDATE_OWN = "users:update_own"
    USERS_DELETE = "users:delete"
    USERS_ASSIGN_ROLES = "users:assign_roles"

    # Organization Management
    ORGS_READ = "organizations:read"
    ORGS_UPDATE = "organizations:update"
    ORGS_MANAGE_BILLING = "organizations:manage_billing"
    ORGS_MANAGE_SETTINGS = "organizations:manage_settings"

    # Task Management
    TASKS_CREATE = "tasks:create"
    TASKS_READ = "tasks:read"
    TASKS_READ_OWN = "tasks:read_own"
    TASKS_READ_TEAM = "tasks:read_team"
    TASKS_UPDATE = "tasks:update"
    TASKS_UPDATE_OWN = "tasks:update_own"
    TASKS_DELETE = "tasks:delete"
    TASKS_ASSIGN = "tasks:assign"
    TASKS_APPROVE_AI = "tasks:approve_ai_subtasks"

    # Check-in Management
    CHECKINS_READ = "checkins:read"
    CHECKINS_READ_OWN = "checkins:read_own"
    CHECKINS_READ_TEAM = "checkins:read_team"
    CHECKINS_RESPOND = "checkins:respond"
    CHECKINS_CONFIGURE = "checkins:configure"

    # AI Features
    AI_USE_ASSISTANT = "ai:use_assistant"
    AI_MANAGE_KNOWLEDGE_BASE = "ai:manage_knowledge_base"
    AI_CONFIGURE = "ai:configure"

    # Skills
    SKILLS_READ = "skills:read"
    SKILLS_READ_OWN = "skills:read_own"
    SKILLS_READ_TEAM = "skills:read_team"
    SKILLS_CONFIGURE_PATHS = "skills:configure_paths"

    # Dashboard & Analytics
    DASHBOARD_VIEW = "dashboard:view"
    DASHBOARD_EXECUTIVE = "dashboard:executive"
    ANALYTICS_VIEW = "analytics:view"

    # Reports
    REPORTS_READ = "reports:read"
    REPORTS_READ_OWN = "reports:read_own"
    REPORTS_CREATE = "reports:create"
    REPORTS_EXPORT = "reports:export"
    REPORTS_GENERATE = "reports:generate"
    REPORTS_VIEW_EXECUTIVE = "reports:view_executive"
    REPORTS_SCHEDULE = "reports:schedule"

    # Predictions
    PREDICTIONS_READ = "predictions:read"
    PREDICTIONS_READ_TEAM = "predictions:read_team"

    # Automation
    AUTOMATION_VIEW = "automation:view"
    AUTOMATION_APPROVE = "automation:approve"
    AUTOMATION_CREATE_AGENTS = "automation:create_agents"
    AUTOMATION_MANAGE_AGENTS = "automation:manage_agents"
    AUTOMATION_MARKETPLACE = "automation:marketplace"

    # Workforce Intelligence
    WORKFORCE_VIEW_SCORES = "workforce:view_scores"
    WORKFORCE_VIEW_MANAGERS = "workforce:view_managers"
    WORKFORCE_VIEW_ORG_HEALTH = "workforce:view_org_health"
    WORKFORCE_SIMULATE = "workforce:simulate"
    WORKFORCE_VIEW_ATTRITION = "workforce:view_attrition"
    WORKFORCE_VIEW_HIRING = "workforce:view_hiring"
    WORKFORCE_REDUCTION_PLANS = "workforce:reduction_plans"
    WORKFORCE_EXPORT = "workforce:export"

    # Integrations
    INTEGRATIONS_VIEW = "integrations:view"
    INTEGRATIONS_MANAGE = "integrations:manage"
    WEBHOOKS_VIEW = "webhooks:view"
    WEBHOOKS_MANAGE = "webhooks:manage"
    API_KEYS_MANAGE = "api_keys:manage"

    # Admin
    ADMIN_ACCESS = "admin:access"
    ADMIN_AUDIT_LOGS = "admin:audit_logs"
    ADMIN_SYSTEM_HEALTH = "admin:system_health"
    ADMIN_GDPR = "admin:gdpr"
    ADMIN_AI_GOVERNANCE = "admin:ai_governance"


# Role to Permissions mapping based on the RBAC matrix from spec
ROLE_PERMISSIONS: dict[UserRole, Set[Permission]] = {
    UserRole.SUPER_ADMIN: {
        # Full access to everything
        Permission.USERS_CREATE, Permission.USERS_READ, Permission.USERS_UPDATE,
        Permission.USERS_DELETE, Permission.USERS_ASSIGN_ROLES,
        Permission.ORGS_READ, Permission.ORGS_UPDATE, Permission.ORGS_MANAGE_BILLING,
        Permission.ORGS_MANAGE_SETTINGS,
        Permission.TASKS_CREATE, Permission.TASKS_READ, Permission.TASKS_UPDATE,
        Permission.TASKS_DELETE, Permission.TASKS_ASSIGN, Permission.TASKS_APPROVE_AI,
        Permission.CHECKINS_READ, Permission.CHECKINS_RESPOND, Permission.CHECKINS_CONFIGURE,
        Permission.AI_USE_ASSISTANT, Permission.AI_MANAGE_KNOWLEDGE_BASE, Permission.AI_CONFIGURE,
        Permission.SKILLS_READ, Permission.SKILLS_CONFIGURE_PATHS,
        Permission.DASHBOARD_VIEW, Permission.DASHBOARD_EXECUTIVE, Permission.ANALYTICS_VIEW,
        Permission.REPORTS_READ, Permission.REPORTS_CREATE, Permission.REPORTS_EXPORT,
        Permission.REPORTS_GENERATE, Permission.REPORTS_VIEW_EXECUTIVE, Permission.REPORTS_SCHEDULE,
        Permission.PREDICTIONS_READ,
        Permission.AUTOMATION_VIEW, Permission.AUTOMATION_APPROVE,
        Permission.AUTOMATION_CREATE_AGENTS, Permission.AUTOMATION_MANAGE_AGENTS,
        Permission.AUTOMATION_MARKETPLACE,
        Permission.WORKFORCE_VIEW_SCORES, Permission.WORKFORCE_VIEW_MANAGERS,
        Permission.WORKFORCE_VIEW_ORG_HEALTH, Permission.WORKFORCE_SIMULATE,
        Permission.WORKFORCE_VIEW_ATTRITION, Permission.WORKFORCE_VIEW_HIRING,
        Permission.WORKFORCE_REDUCTION_PLANS, Permission.WORKFORCE_EXPORT,
        Permission.INTEGRATIONS_VIEW, Permission.INTEGRATIONS_MANAGE,
        Permission.WEBHOOKS_VIEW, Permission.WEBHOOKS_MANAGE, Permission.API_KEYS_MANAGE,
        Permission.ADMIN_ACCESS, Permission.ADMIN_AUDIT_LOGS,
        Permission.ADMIN_SYSTEM_HEALTH, Permission.ADMIN_GDPR, Permission.ADMIN_AI_GOVERNANCE,
    },

    UserRole.ORG_ADMIN: {
        Permission.USERS_CREATE, Permission.USERS_READ, Permission.USERS_UPDATE,
        Permission.USERS_DELETE, Permission.USERS_ASSIGN_ROLES,
        Permission.ORGS_READ, Permission.ORGS_UPDATE, Permission.ORGS_MANAGE_BILLING,
        Permission.ORGS_MANAGE_SETTINGS,
        Permission.TASKS_CREATE, Permission.TASKS_READ, Permission.TASKS_UPDATE,
        Permission.TASKS_DELETE, Permission.TASKS_ASSIGN, Permission.TASKS_APPROVE_AI,
        Permission.CHECKINS_READ, Permission.CHECKINS_CONFIGURE,
        Permission.AI_USE_ASSISTANT, Permission.AI_MANAGE_KNOWLEDGE_BASE, Permission.AI_CONFIGURE,
        Permission.SKILLS_READ, Permission.SKILLS_CONFIGURE_PATHS,
        Permission.DASHBOARD_VIEW, Permission.DASHBOARD_EXECUTIVE, Permission.ANALYTICS_VIEW,
        Permission.REPORTS_READ, Permission.REPORTS_CREATE, Permission.REPORTS_EXPORT,
        Permission.REPORTS_GENERATE, Permission.REPORTS_VIEW_EXECUTIVE, Permission.REPORTS_SCHEDULE,
        Permission.PREDICTIONS_READ,
        Permission.AUTOMATION_VIEW, Permission.AUTOMATION_APPROVE,
        Permission.AUTOMATION_CREATE_AGENTS, Permission.AUTOMATION_MANAGE_AGENTS,
        Permission.AUTOMATION_MARKETPLACE,
        Permission.WORKFORCE_VIEW_SCORES, Permission.WORKFORCE_VIEW_MANAGERS,
        Permission.WORKFORCE_VIEW_ORG_HEALTH, Permission.WORKFORCE_VIEW_ATTRITION,
        Permission.WORKFORCE_VIEW_HIRING, Permission.WORKFORCE_EXPORT,
        Permission.INTEGRATIONS_VIEW, Permission.INTEGRATIONS_MANAGE,
        Permission.WEBHOOKS_VIEW, Permission.WEBHOOKS_MANAGE, Permission.API_KEYS_MANAGE,
        Permission.ADMIN_ACCESS, Permission.ADMIN_AUDIT_LOGS, Permission.ADMIN_GDPR,
    },

    UserRole.MANAGER: {
        Permission.USERS_READ,
        Permission.ORGS_READ,
        Permission.TASKS_CREATE, Permission.TASKS_READ, Permission.TASKS_READ_TEAM,
        Permission.TASKS_UPDATE, Permission.TASKS_ASSIGN, Permission.TASKS_APPROVE_AI,
        Permission.CHECKINS_READ, Permission.CHECKINS_READ_TEAM,
        Permission.AI_USE_ASSISTANT,
        Permission.SKILLS_READ, Permission.SKILLS_READ_TEAM,
        Permission.DASHBOARD_VIEW, Permission.ANALYTICS_VIEW,
        Permission.REPORTS_READ, Permission.REPORTS_CREATE, Permission.REPORTS_EXPORT,
        Permission.REPORTS_GENERATE,
        Permission.PREDICTIONS_READ, Permission.PREDICTIONS_READ_TEAM,
        Permission.AUTOMATION_VIEW, Permission.AUTOMATION_APPROVE,
        Permission.AUTOMATION_CREATE_AGENTS, Permission.AUTOMATION_MANAGE_AGENTS,
        Permission.AUTOMATION_MARKETPLACE,
        Permission.INTEGRATIONS_VIEW,
    },

    UserRole.TEAM_LEAD: {
        Permission.USERS_READ,
        Permission.ORGS_READ,
        Permission.TASKS_CREATE, Permission.TASKS_READ, Permission.TASKS_READ_TEAM,
        Permission.TASKS_UPDATE, Permission.TASKS_ASSIGN, Permission.TASKS_APPROVE_AI,
        Permission.CHECKINS_READ_OWN, Permission.CHECKINS_READ_TEAM, Permission.CHECKINS_RESPOND,
        Permission.AI_USE_ASSISTANT,
        Permission.SKILLS_READ_OWN, Permission.SKILLS_READ_TEAM,
        Permission.DASHBOARD_VIEW,
        Permission.REPORTS_READ, Permission.REPORTS_EXPORT,
        Permission.PREDICTIONS_READ, Permission.PREDICTIONS_READ_TEAM,
        Permission.AUTOMATION_VIEW, Permission.AUTOMATION_MARKETPLACE,
    },

    UserRole.EMPLOYEE: {
        Permission.USERS_READ_OWN,
        Permission.TASKS_READ_OWN, Permission.TASKS_UPDATE_OWN,
        Permission.CHECKINS_READ_OWN, Permission.CHECKINS_RESPOND,
        Permission.AI_USE_ASSISTANT,
        Permission.SKILLS_READ_OWN,
        Permission.REPORTS_READ_OWN,
        Permission.AUTOMATION_VIEW, Permission.AUTOMATION_MARKETPLACE,
    },

    UserRole.VIEWER: {
        Permission.TASKS_READ,
        Permission.REPORTS_READ,
    },
}


def get_user_permissions(role: UserRole) -> Set[Permission]:
    """Get all permissions for a role."""
    return ROLE_PERMISSIONS.get(role, set())


def has_permission(role: UserRole, permission: Permission) -> bool:
    """Check if a role has a specific permission."""
    return permission in get_user_permissions(role)


def has_any_permission(role: UserRole, permissions: Set[Permission]) -> bool:
    """Check if a role has any of the specified permissions."""
    user_perms = get_user_permissions(role)
    return bool(user_perms & permissions)


def has_all_permissions(role: UserRole, permissions: Set[Permission]) -> bool:
    """Check if a role has all of the specified permissions."""
    user_perms = get_user_permissions(role)
    return permissions.issubset(user_perms)


class PermissionChecker:
    """
    Dependency class for checking permissions.

    Usage:
        @router.get("/admin")
        async def admin_endpoint(
            user: User = Depends(PermissionChecker(Permission.ADMIN_ACCESS))
        ):
            ...
    """

    def __init__(self, *required_permissions: Permission, require_all: bool = True):
        self.required_permissions = set(required_permissions)
        self.require_all = require_all

    async def __call__(self, current_user=None) -> None:
        from app.api.v1.dependencies import get_current_active_user
        from fastapi import Depends

        if current_user is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Authentication required"
            )

        user_perms = get_user_permissions(current_user.role)

        if self.require_all:
            if not self.required_permissions.issubset(user_perms):
                missing = self.required_permissions - user_perms
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=f"Missing required permissions: {[p.value for p in missing]}"
                )
        else:
            if not (self.required_permissions & user_perms):
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=f"Requires one of: {[p.value for p in self.required_permissions]}"
                )


def require_permission(*permissions: Permission, require_all: bool = True):
    """
    Decorator factory for permission checking.

    Usage:
        @router.get("/admin")
        @require_permission(Permission.ADMIN_ACCESS)
        async def admin_endpoint(current_user: User = Depends(get_current_active_user)):
            ...
    """
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # Get current_user from kwargs
            current_user = kwargs.get('current_user')
            if current_user is None:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Authentication required"
                )

            user_perms = get_user_permissions(current_user.role)
            required = set(permissions)

            if require_all:
                if not required.issubset(user_perms):
                    missing = required - user_perms
                    raise HTTPException(
                        status_code=status.HTTP_403_FORBIDDEN,
                        detail=f"Missing permissions: {[p.value for p in missing]}"
                    )
            else:
                if not (required & user_perms):
                    raise HTTPException(
                        status_code=status.HTTP_403_FORBIDDEN,
                        detail=f"Requires one of: {[p.value for p in required]}"
                    )

            return await func(*args, **kwargs)
        return wrapper
    return decorator


def get_permissions_list(role: UserRole) -> list[str]:
    """Get permissions as list of strings for API responses."""
    return [p.value for p in get_user_permissions(role)]

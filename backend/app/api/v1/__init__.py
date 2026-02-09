"""
TaskPulse - AI Assistant - API v1 Routes
Version 1 of the API endpoints
"""

from fastapi import APIRouter

# Main v1 router
router = APIRouter()

# Import all routers
from app.api.v1 import (
    auth,
    users,
    organizations,
    tasks,
    checkins,
    ai_unblock,
    skills,
    predictions,
    automation,
    workforce,
    notifications,
    integrations,
    reports,
    admin
)

__all__ = [
    "router",
    "auth",
    "users",
    "organizations",
    "tasks",
    "checkins",
    "ai_unblock",
    "skills",
    "predictions",
    "automation",
    "workforce",
    "notifications",
    "integrations",
    "reports",
    "admin"
]

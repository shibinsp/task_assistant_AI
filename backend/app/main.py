"""
TaskPulse - AI Assistant - Main Application Entry Point
The Intelligent Task Completion Engine
"""

import logging
from contextlib import asynccontextmanager
from datetime import datetime

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.config import settings
from app.database import init_db, close_db
from app.core.middleware import setup_middleware, setup_exception_handlers

# Configure logging
logging.basicConfig(
    level=getattr(logging, settings.LOG_LEVEL),
    format=settings.LOG_FORMAT
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Lifespan context manager for startup and shutdown events.
    """
    # Startup
    logger.info(f"Starting {settings.APP_NAME} v{settings.APP_VERSION}")
    logger.info(f"Environment: {settings.ENVIRONMENT}")
    logger.info(f"Debug mode: {settings.DEBUG}")

    # Validate production settings
    settings.validate_production_settings()

    # Initialize database
    logger.info("Initializing database...")
    await init_db()
    logger.info("Database initialized successfully")

    # Initialize agent orchestrator
    logger.info("Initializing agent orchestrator...")
    try:
        from app.agents.orchestrator import init_orchestrator
        await init_orchestrator()
        logger.info("Agent orchestrator initialized with default agents")
    except Exception as e:
        logger.warning(f"Agent orchestrator initialization failed: {e}")

    yield

    # Shutdown
    logger.info("Shutting down...")

    # Shutdown agent orchestrator
    try:
        from app.agents.orchestrator import shutdown_orchestrator
        await shutdown_orchestrator()
        logger.info("Agent orchestrator shut down")
    except Exception as e:
        logger.warning(f"Agent orchestrator shutdown failed: {e}")

    await close_db()
    logger.info("Database connections closed")
    logger.info("Shutdown complete")


# Create FastAPI application
app = FastAPI(
    title=settings.APP_NAME,
    description=f"""
## {settings.APP_DESCRIPTION}

TaskPulse - AI Assistant is an AI-native workforce productivity platform that transforms
task management from passive tracking to active task completion intelligence.

### Key Features:
- **Smart Check-In Engine**: Proactive 3-hour check-in loops with friction detection
- **AI Unblock Engine**: RAG-powered contextual help with 0% hallucination
- **Prediction Engine**: ML-powered delivery forecasting and risk assessment
- **Skill Graph**: Automatic skill inference and learning velocity tracking
- **Workforce Intelligence**: Executive-level decision intelligence
- **Automation Detection**: Identify and automate repetitive work patterns

### Core Philosophy:
> "No employee should stay stuck for more than 3 hours without intelligent intervention."

### API Version: v1
    """,
    version=settings.APP_VERSION,
    docs_url="/docs" if settings.is_development else None,
    redoc_url="/redoc" if settings.is_development else None,
    openapi_url="/openapi.json" if settings.is_development else None,
    lifespan=lifespan
)

# Setup CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=settings.CORS_ALLOW_CREDENTIALS,
    allow_methods=settings.CORS_ALLOW_METHODS,
    allow_headers=settings.CORS_ALLOW_HEADERS,
)

# Setup custom middleware
setup_middleware(app)

# Setup exception handlers
setup_exception_handlers(app)


# ==================== Health Check Endpoints ====================

@app.get(
    "/",
    tags=["Health"],
    summary="Root endpoint",
    description="Returns basic application information"
)
async def root():
    """Root endpoint returning application info."""
    return {
        "name": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "description": settings.APP_DESCRIPTION,
        "status": "running",
        "docs": "/docs" if settings.is_development else "disabled",
        "timestamp": datetime.utcnow().isoformat()
    }


@app.get(
    "/health",
    tags=["Health"],
    summary="Health check",
    description="Returns detailed health status of the application"
)
async def health_check():
    """
    Health check endpoint for monitoring and load balancers.
    Returns detailed status of all application components.
    """
    from app.database import engine

    # Check database connection
    from sqlalchemy import text
    db_status = "healthy"
    db_error = None
    try:
        async with engine.connect() as conn:
            await conn.execute(text("SELECT 1"))
    except Exception as e:
        db_status = "unhealthy"
        db_error = str(e)

    # Overall health
    is_healthy = db_status == "healthy"

    return JSONResponse(
        status_code=200 if is_healthy else 503,
        content={
            "status": "healthy" if is_healthy else "unhealthy",
            "timestamp": datetime.utcnow().isoformat(),
            "version": settings.APP_VERSION,
            "environment": settings.ENVIRONMENT,
            "components": {
                "database": {
                    "status": db_status,
                    "error": db_error
                },
                "ai_provider": {
                    "status": "configured" if settings.AI_PROVIDER != "mock" else "mock",
                    "provider": settings.AI_PROVIDER
                }
            }
        }
    )


@app.get(
    "/ready",
    tags=["Health"],
    summary="Readiness check",
    description="Returns whether the application is ready to accept requests"
)
async def readiness_check():
    """
    Readiness check for Kubernetes/container orchestration.
    Returns 200 only if the application is fully ready.
    """
    return {"status": "ready", "timestamp": datetime.utcnow().isoformat()}


# ==================== API Version Info ====================

@app.get(
    "/api/v1",
    tags=["API Info"],
    summary="API v1 information",
    description="Returns information about API version 1"
)
async def api_v1_info():
    """API version 1 information."""
    return {
        "version": "1.0.0",
        "status": "active",
        "documentation": "/docs",
        "endpoints": {
            "auth": "/api/v1/auth",
            "users": "/api/v1/users",
            "organizations": "/api/v1/organizations",
            "tasks": "/api/v1/tasks",
            "checkins": "/api/v1/checkins",
            "ai": "/api/v1/ai",
            "skills": "/api/v1/skills",
            "predictions": "/api/v1/predictions",
            "automation": "/api/v1/automation",
            "workforce": "/api/v1/workforce",
            "notifications": "/api/v1/notifications",
            "integrations": "/api/v1/integrations",
            "reports": "/api/v1/reports",
            "admin": "/api/v1/admin",
            "agents": "/api/v1/agents",
            "chat": "/api/v1/chat"
        }
    }


# ==================== Include API Routers ====================

# Phase 2 - Authentication
from app.api.v1 import auth
app.include_router(auth.router, prefix="/api/v1/auth", tags=["Authentication"])

# Phase 3 - Users & Organizations
from app.api.v1 import users, organizations
app.include_router(users.router, prefix="/api/v1/users", tags=["Users"])
app.include_router(organizations.router, prefix="/api/v1/organizations", tags=["Organizations"])

# Phase 4 - Tasks
from app.api.v1 import tasks
app.include_router(tasks.router, prefix="/api/v1/tasks", tags=["Tasks"])

# Phase 6 - Check-ins
from app.api.v1 import checkins
app.include_router(checkins.router, prefix="/api/v1/checkins", tags=["Check-ins"])

# Phase 7 - AI Unblock
from app.api.v1 import ai_unblock
app.include_router(ai_unblock.router, prefix="/api/v1/ai", tags=["AI"])

# Phase 8 - Skills
from app.api.v1 import skills
app.include_router(skills.router, prefix="/api/v1/skills", tags=["Skills"])

# Phase 10 - Predictions
from app.api.v1 import predictions
app.include_router(predictions.router, prefix="/api/v1/predictions", tags=["Predictions"])

# Phase 11 - Automation
from app.api.v1 import automation
app.include_router(automation.router, prefix="/api/v1/automation", tags=["Automation"])

# Phase 12 - Workforce Intelligence
from app.api.v1 import workforce
app.include_router(workforce.router, prefix="/api/v1/workforce", tags=["Workforce"])

# Phase 13 - Notifications & Integrations
from app.api.v1 import notifications, integrations, reports
app.include_router(notifications.router, prefix="/api/v1/notifications", tags=["Notifications"])
app.include_router(integrations.router, prefix="/api/v1/integrations", tags=["Integrations"])
app.include_router(reports.router, prefix="/api/v1/reports", tags=["Reports"])

# Phase 14 - Admin & Security
from app.api.v1 import admin
app.include_router(admin.router, prefix="/api/v1/admin", tags=["Admin"])

# Multi-Agent System
# Temporarily disabled due to import errors
# from app.api.v1 import agents, chat
# app.include_router(agents.router, prefix="/api/v1", tags=["Agents"])
# app.include_router(chat.router, prefix="/api/v1", tags=["Chat"])


# ==================== Run Application ====================

if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "app.main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=settings.RELOAD,
        workers=settings.WORKERS,
        log_level=settings.LOG_LEVEL.lower()
    )

"""
TaskPulse - AI Assistant - SQLAlchemy Models
Database models for all entities
"""

# Phase 2 - Authentication & User Management
from app.models.organization import Organization, PlanTier
from app.models.user import User, Session, UserRole, SkillLevel

# Phase 4 - Tasks
from app.models.task import (
    Task, TaskDependency, TaskHistory, TaskComment,
    TaskStatus, TaskPriority, BlockerType
)

# Phase 6 - Check-ins
from app.models.checkin import (
    CheckIn, CheckInConfig, CheckInReminder,
    CheckInTrigger, CheckInStatus, ProgressIndicator
)

# Phase 7 - Knowledge Base / AI Unblock
from app.models.knowledge_base import (
    Document, DocumentChunk, UnblockSession,
    DocumentSource, DocumentStatus, DocumentType
)

# Phase 8 - Skills
from app.models.skill import (
    Skill, UserSkill, SkillGap, SkillMetrics, LearningPath,
    SkillCategory, SkillTrend, GapType
)

# Phase 10 - Predictions
from app.models.prediction import (
    Prediction, VelocitySnapshot, PredictionType
)

# Phase 11 - Automation
from app.models.automation import (
    AutomationPattern, AIAgent, AgentRun,
    PatternStatus, AgentStatus
)

# Phase 12 - Workforce Intelligence
from app.models.workforce import (
    WorkforceScore, ManagerEffectiveness, OrgHealthSnapshot,
    RestructuringScenario
)

# Phase 13 - Notifications & Integrations
from app.models.notification import (
    Notification, NotificationPreference, Integration, Webhook, WebhookDelivery,
    NotificationType, NotificationChannel, IntegrationType
)

# Phase 14 - Admin & Security
from app.models.audit import (
    AuditLog, GDPRRequest, APIKey, SystemHealth,
    ActorType, AuditAction
)

# Phase 15 - Agent Orchestration
from app.models.agent import (
    Agent, AgentExecution, AgentConversation, AgentSchedule,
    AgentType, AgentStatusDB, ExecutionStatus
)

# Export all models
__all__ = [
    # Organization
    "Organization", "PlanTier",
    # User
    "User", "Session", "UserRole", "SkillLevel",
    # Task
    "Task", "TaskDependency", "TaskHistory", "TaskComment",
    "TaskStatus", "TaskPriority", "BlockerType",
    # Check-in
    "CheckIn", "CheckInConfig", "CheckInReminder",
    "CheckInTrigger", "CheckInStatus", "ProgressIndicator",
    # Knowledge Base / AI Unblock
    "Document", "DocumentChunk", "UnblockSession",
    "DocumentSource", "DocumentStatus", "DocumentType",
    # Skills
    "Skill", "UserSkill", "SkillGap", "SkillMetrics", "LearningPath",
    "SkillCategory", "SkillTrend", "GapType",
    # Predictions
    "Prediction", "VelocitySnapshot", "PredictionType",
    # Automation
    "AutomationPattern", "AIAgent", "AgentRun",
    "PatternStatus", "AgentStatus",
    # Workforce
    "WorkforceScore", "ManagerEffectiveness", "OrgHealthSnapshot",
    "RestructuringScenario",
    # Notifications
    "Notification", "NotificationPreference", "Integration", "Webhook", "WebhookDelivery",
    "NotificationType", "NotificationChannel", "IntegrationType",
    # Admin
    "AuditLog", "GDPRRequest", "APIKey", "SystemHealth",
    "ActorType", "AuditAction",
    # Agent Orchestration
    "Agent", "AgentExecution", "AgentConversation", "AgentSchedule",
    "AgentType", "AgentStatusDB", "ExecutionStatus",
]

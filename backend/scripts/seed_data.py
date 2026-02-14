"""
TaskPulse - AI Assistant - Comprehensive Seed Data Script
Populates the database with realistic demo data for testing all features
"""

import asyncio
import json
import random
from datetime import datetime, timedelta

from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker

from app.config import settings
from app.database import Base
from app.models.user import User, UserRole
from app.models.organization import Organization
from app.models.task import Task, TaskStatus, TaskPriority, TaskComment, TaskDependency, TaskHistory
from app.models.checkin import (
    CheckIn, CheckInConfig, CheckInStatus, CheckInTrigger, ProgressIndicator,
)
from app.models.skill import (
    Skill, UserSkill, SkillCategory, SkillTrend, SkillGap, GapType, SkillMetrics, LearningPath,
)
from app.models.workforce import (
    WorkforceScore, ManagerEffectiveness, OrgHealthSnapshot, RestructuringScenario,
)
from app.models.prediction import Prediction, PredictionType, VelocitySnapshot
from app.models.automation import AutomationPattern, PatternStatus, AIAgent, AgentStatus, AgentRun
from app.models.knowledge_base import (
    Document, DocumentChunk, DocumentSource, DocumentStatus, DocumentType,
)
from app.models.notification import (
    Notification, NotificationType, NotificationChannel, IntegrationType, Integration,
)
from app.models.audit import AuditLog, ActorType, AuditAction
from app.models.agent import Agent, AgentExecution, AgentType, AgentStatusDB, ExecutionStatus
from app.core.security import hash_password
from app.utils.helpers import generate_uuid


NOW = datetime.utcnow()


def days_ago(d: int, h: int = 0) -> datetime:
    return NOW - timedelta(days=d, hours=h)


def days_from_now(d: int) -> datetime:
    return NOW + timedelta(days=d)


# ─── Data definitions ────────────────────────────────────────────────

DEMO_USERS = [
    {"email": "admin@acme.com", "first_name": "Sarah", "last_name": "Johnson",
     "role": UserRole.ORG_ADMIN, "team": None, "skill_level": "senior"},
    {"email": "manager@acme.com", "first_name": "Michael", "last_name": "Chen",
     "role": UserRole.MANAGER, "team": None, "skill_level": "lead"},
    {"email": "lead@acme.com", "first_name": "Emily", "last_name": "Rodriguez",
     "role": UserRole.TEAM_LEAD, "team": "team-alpha", "skill_level": "senior"},
    {"email": "dev1@acme.com", "first_name": "James", "last_name": "Wilson",
     "role": UserRole.EMPLOYEE, "team": "team-alpha", "skill_level": "mid"},
    {"email": "dev2@acme.com", "first_name": "Lisa", "last_name": "Thompson",
     "role": UserRole.EMPLOYEE, "team": "team-alpha", "skill_level": "mid"},
    {"email": "dev3@acme.com", "first_name": "David", "last_name": "Brown",
     "role": UserRole.EMPLOYEE, "team": "team-beta", "skill_level": "junior"},
    {"email": "viewer@acme.com", "first_name": "Alex", "last_name": "Garcia",
     "role": UserRole.VIEWER, "team": None, "skill_level": "mid"},
    {"email": "dev4@acme.com", "first_name": "Rachel", "last_name": "Kim",
     "role": UserRole.EMPLOYEE, "team": "team-beta", "skill_level": "mid"},
    {"email": "dev5@acme.com", "first_name": "Marcus", "last_name": "Rivera",
     "role": UserRole.EMPLOYEE, "team": "team-beta", "skill_level": "senior"},
    {"email": "lead2@acme.com", "first_name": "Priya", "last_name": "Patel",
     "role": UserRole.TEAM_LEAD, "team": "team-beta", "skill_level": "senior"},
]

DEMO_SKILLS = [
    # TECHNICAL
    {"name": "Python", "cat": SkillCategory.TECHNICAL, "org_avg": 6.5, "ind_avg": 6.0,
     "related": ["FastAPI", "Machine Learning"]},
    {"name": "JavaScript", "cat": SkillCategory.TECHNICAL, "org_avg": 6.0, "ind_avg": 6.2,
     "related": ["TypeScript", "React"]},
    {"name": "TypeScript", "cat": SkillCategory.TECHNICAL, "org_avg": 5.8, "ind_avg": 5.5,
     "related": ["JavaScript", "React"]},
    {"name": "React", "cat": SkillCategory.TECHNICAL, "org_avg": 5.5, "ind_avg": 5.8,
     "related": ["TypeScript", "JavaScript"]},
    {"name": "FastAPI", "cat": SkillCategory.TECHNICAL, "org_avg": 5.0, "ind_avg": 4.5,
     "related": ["Python", "PostgreSQL"]},
    {"name": "PostgreSQL", "cat": SkillCategory.TECHNICAL, "org_avg": 5.2, "ind_avg": 5.5,
     "related": ["FastAPI", "Python"]},
    {"name": "Docker", "cat": SkillCategory.TECHNICAL, "org_avg": 4.8, "ind_avg": 5.0,
     "related": ["Kubernetes", "CI/CD"]},
    # PROCESS
    {"name": "Git", "cat": SkillCategory.PROCESS, "org_avg": 7.0, "ind_avg": 6.5,
     "related": ["Code Review", "CI/CD"]},
    {"name": "Agile", "cat": SkillCategory.PROCESS, "org_avg": 5.5, "ind_avg": 5.8,
     "related": ["Communication", "Teamwork"]},
    {"name": "Code Review", "cat": SkillCategory.PROCESS, "org_avg": 5.0, "ind_avg": 5.2,
     "related": ["Git", "Problem Solving"]},
    {"name": "CI/CD", "cat": SkillCategory.PROCESS, "org_avg": 4.5, "ind_avg": 4.8,
     "related": ["Docker", "Git"]},
    # SOFT
    {"name": "Communication", "cat": SkillCategory.SOFT, "org_avg": 6.0, "ind_avg": 5.5,
     "related": ["Teamwork", "Leadership"]},
    {"name": "Problem Solving", "cat": SkillCategory.SOFT, "org_avg": 6.2, "ind_avg": 6.0,
     "related": ["Communication", "Code Review"]},
    {"name": "Teamwork", "cat": SkillCategory.SOFT, "org_avg": 6.5, "ind_avg": 6.0,
     "related": ["Communication", "Agile"]},
    {"name": "Leadership", "cat": SkillCategory.SOFT, "org_avg": 4.5, "ind_avg": 5.0,
     "related": ["Communication", "Teamwork"]},
    # DOMAIN
    {"name": "Machine Learning", "cat": SkillCategory.DOMAIN, "org_avg": 3.5, "ind_avg": 4.2,
     "related": ["Python", "Cloud Architecture"]},
    {"name": "Cloud Architecture", "cat": SkillCategory.DOMAIN, "org_avg": 4.0, "ind_avg": 4.8,
     "related": ["AWS", "Kubernetes"]},
    # TOOL
    {"name": "Kubernetes", "cat": SkillCategory.TOOL, "org_avg": 3.8, "ind_avg": 4.5,
     "related": ["Docker", "Cloud Architecture"]},
    {"name": "AWS", "cat": SkillCategory.TOOL, "org_avg": 4.2, "ind_avg": 5.0,
     "related": ["Cloud Architecture", "Docker"]},
    {"name": "Redis", "cat": SkillCategory.TOOL, "org_avg": 4.0, "ind_avg": 4.5,
     "related": ["PostgreSQL", "Python"]},
]

# Tasks themed around "Building a SaaS Platform"
DEMO_TASKS = [
    # DONE (7)
    {"title": "Design database schema for multi-tenant SaaS",
     "desc": "Create the PostgreSQL schema supporting organizations, users, roles, and tenant isolation. Include migration scripts and seed data.",
     "priority": TaskPriority.CRITICAL, "hours": 8, "status": TaskStatus.DONE,
     "tags": ["backend", "database"], "skills": ["PostgreSQL", "Python"]},
    {"title": "Implement JWT authentication with refresh tokens",
     "desc": "Build secure auth flow with access/refresh token rotation, password hashing with bcrypt, and rate limiting on login attempts.",
     "priority": TaskPriority.HIGH, "hours": 16, "status": TaskStatus.DONE,
     "tags": ["backend", "security"], "skills": ["Python", "FastAPI"]},
    {"title": "Create user registration and onboarding flow",
     "desc": "Frontend multi-step signup wizard with email verification, organization setup, and initial preferences configuration.",
     "priority": TaskPriority.HIGH, "hours": 20, "status": TaskStatus.DONE,
     "tags": ["frontend"], "skills": ["React", "TypeScript"]},
    {"title": "Set up CI/CD pipeline with GitHub Actions",
     "desc": "Configure automated testing, linting, building, and deployment pipeline. Include staging and production environments.",
     "priority": TaskPriority.MEDIUM, "hours": 8, "status": TaskStatus.DONE,
     "tags": ["devops"], "skills": ["CI/CD", "Docker"]},
    {"title": "Write unit tests for authentication module",
     "desc": "Achieve 90%+ coverage on auth service including login, registration, token refresh, password reset, and edge cases.",
     "priority": TaskPriority.MEDIUM, "hours": 12, "status": TaskStatus.DONE,
     "tags": ["testing", "backend"], "skills": ["Python"]},
    {"title": "Implement role-based access control (RBAC)",
     "desc": "Create permission system with Super Admin, Org Admin, Manager, Team Lead, Employee, and Viewer roles.",
     "priority": TaskPriority.HIGH, "hours": 14, "status": TaskStatus.DONE,
     "tags": ["backend", "security"], "skills": ["Python", "FastAPI"]},
    {"title": "Build responsive navigation and sidebar",
     "desc": "Create the main application layout with collapsible sidebar, breadcrumbs, and mobile-responsive hamburger menu.",
     "priority": TaskPriority.MEDIUM, "hours": 10, "status": TaskStatus.DONE,
     "tags": ["frontend"], "skills": ["React", "TypeScript"]},

    # REVIEW (4)
    {"title": "Build analytics dashboard with Recharts",
     "desc": "Create the main dashboard page with task velocity chart, completion metrics, team workload distribution, and productivity heatmap.",
     "priority": TaskPriority.HIGH, "hours": 24, "status": TaskStatus.REVIEW,
     "tags": ["frontend"], "skills": ["React", "TypeScript"]},
    {"title": "Implement webhook system for external integrations",
     "desc": "Create webhook registration, payload signing, retry logic with exponential backoff, and delivery tracking.",
     "priority": TaskPriority.MEDIUM, "hours": 16, "status": TaskStatus.REVIEW,
     "tags": ["backend"], "skills": ["Python", "FastAPI"]},
    {"title": "Create API documentation with OpenAPI/Swagger",
     "desc": "Auto-generate API docs from FastAPI schemas. Add examples, authentication docs, and error code reference.",
     "priority": TaskPriority.LOW, "hours": 6, "status": TaskStatus.REVIEW,
     "tags": ["docs", "backend"], "skills": ["FastAPI"]},
    {"title": "Implement email notification service",
     "desc": "Build async email sending with templates for welcome, password reset, task assignment, and check-in reminders.",
     "priority": TaskPriority.MEDIUM, "hours": 10, "status": TaskStatus.REVIEW,
     "tags": ["backend"], "skills": ["Python"]},

    # IN_PROGRESS (6)
    {"title": "Build Stripe payment integration",
     "desc": "Implement subscription billing with Stripe: plan selection, checkout flow, invoice management, and webhook handlers for payment events.",
     "priority": TaskPriority.CRITICAL, "hours": 32, "status": TaskStatus.IN_PROGRESS,
     "tags": ["backend", "payments"], "skills": ["Python", "FastAPI"]},
    {"title": "Create team management UI",
     "desc": "Build team page with member list, invite flow, role assignment, and permission management interface.",
     "priority": TaskPriority.MEDIUM, "hours": 18, "status": TaskStatus.IN_PROGRESS,
     "tags": ["frontend"], "skills": ["React", "TypeScript"]},
    {"title": "Implement Redis caching layer",
     "desc": "Add Redis caching for frequently accessed data: user sessions, task lists, dashboard metrics. Include cache invalidation strategy.",
     "priority": TaskPriority.MEDIUM, "hours": 12, "status": TaskStatus.IN_PROGRESS,
     "tags": ["backend", "performance"], "skills": ["Redis", "Python"]},
    {"title": "Build real-time notification system with WebSocket",
     "desc": "Implement WebSocket connections for real-time push notifications, check-in prompts, and live task updates.",
     "priority": TaskPriority.HIGH, "hours": 20, "status": TaskStatus.IN_PROGRESS,
     "tags": ["backend", "frontend"], "skills": ["Python", "React"]},
    {"title": "Create settings and preferences page",
     "desc": "Build user settings page with profile editing, notification preferences, theme selection, and timezone configuration.",
     "priority": TaskPriority.LOW, "hours": 14, "status": TaskStatus.IN_PROGRESS,
     "tags": ["frontend"], "skills": ["React", "TypeScript"]},
    {"title": "Implement file upload and document processing",
     "desc": "Build file upload service supporting PDF, DOCX, TXT with text extraction, chunking for RAG, and storage management.",
     "priority": TaskPriority.HIGH, "hours": 16, "status": TaskStatus.IN_PROGRESS,
     "tags": ["backend"], "skills": ["Python"]},

    # BLOCKED (3)
    {"title": "Deploy to production on AWS",
     "desc": "Set up production infrastructure: ECS/Fargate containers, RDS PostgreSQL, ElastiCache Redis, S3 for files, CloudFront CDN.",
     "priority": TaskPriority.HIGH, "hours": 20, "status": TaskStatus.BLOCKED,
     "tags": ["devops"], "skills": ["AWS", "Docker", "Kubernetes"],
     "blocker": "Waiting for AWS account approval from finance team"},
    {"title": "Implement Google OAuth SSO",
     "desc": "Add Google Sign-In button and backend verification. Map Google profiles to user accounts with automatic org assignment.",
     "priority": TaskPriority.MEDIUM, "hours": 8, "status": TaskStatus.BLOCKED,
     "tags": ["backend", "security"], "skills": ["Python", "FastAPI"],
     "blocker": "OAuth consent screen pending Google verification"},
    {"title": "Set up monitoring with Datadog",
     "desc": "Configure APM, log aggregation, custom metrics, dashboards, and alerting for production health monitoring.",
     "priority": TaskPriority.MEDIUM, "hours": 10, "status": TaskStatus.BLOCKED,
     "tags": ["devops"], "skills": ["AWS", "Docker"],
     "blocker": "Datadog license procurement in progress"},

    # TODO (5)
    {"title": "Implement data export (CSV/Excel)",
     "desc": "Add export functionality for tasks, analytics, and reports in CSV and Excel formats with filtering options.",
     "priority": TaskPriority.LOW, "hours": 8, "status": TaskStatus.TODO,
     "tags": ["backend", "frontend"], "skills": ["Python", "React"]},
    {"title": "Build mobile-responsive task board",
     "desc": "Optimize Kanban board for mobile: touch-friendly drag-and-drop, swipe actions, and compact card layout.",
     "priority": TaskPriority.LOW, "hours": 12, "status": TaskStatus.TODO,
     "tags": ["frontend"], "skills": ["React", "TypeScript"]},
    {"title": "Write integration tests for payment flow",
     "desc": "End-to-end tests for subscription lifecycle: signup, upgrade, downgrade, cancellation, and failed payment handling.",
     "priority": TaskPriority.MEDIUM, "hours": 16, "status": TaskStatus.TODO,
     "tags": ["testing"], "skills": ["Python"]},
    {"title": "Create load testing suite with Locust",
     "desc": "Build load test scenarios for critical paths: auth, task CRUD, dashboard, and WebSocket connections. Target 1000 concurrent users.",
     "priority": TaskPriority.LOW, "hours": 10, "status": TaskStatus.TODO,
     "tags": ["testing", "performance"], "skills": ["Python"]},
    {"title": "Implement audit logging for compliance",
     "desc": "Log all data access, modifications, auth events, and admin actions. Include retention policy and GDPR export support.",
     "priority": TaskPriority.MEDIUM, "hours": 14, "status": TaskStatus.TODO,
     "tags": ["backend", "security"], "skills": ["Python", "PostgreSQL"]},
]

SUBTASKS_MAP = {
    "Design database schema for multi-tenant SaaS": [
        ("Create organization and user tables", TaskStatus.DONE),
        ("Design task and subtask relationships", TaskStatus.DONE),
        ("Add check-in and skill tables", TaskStatus.DONE),
        ("Write Alembic migration scripts", TaskStatus.DONE),
    ],
    "Implement JWT authentication with refresh tokens": [
        ("Set up JWT token generation and validation", TaskStatus.DONE),
        ("Create login and registration endpoints", TaskStatus.DONE),
        ("Add password hashing with bcrypt", TaskStatus.DONE),
        ("Implement token refresh rotation", TaskStatus.DONE),
        ("Add rate limiting on login attempts", TaskStatus.DONE),
    ],
    "Build Stripe payment integration": [
        ("Set up Stripe SDK and configuration", TaskStatus.DONE),
        ("Create subscription plan models", TaskStatus.IN_PROGRESS),
        ("Build checkout session flow", TaskStatus.IN_PROGRESS),
        ("Implement webhook handlers for payment events", TaskStatus.TODO),
        ("Add invoice management and history", TaskStatus.TODO),
    ],
    "Build analytics dashboard with Recharts": [
        ("Create task velocity area chart", TaskStatus.DONE),
        ("Build team workload bar chart", TaskStatus.REVIEW),
        ("Add productivity heatmap", TaskStatus.REVIEW),
        ("Implement date range filter", TaskStatus.TODO),
    ],
    "Create team management UI": [
        ("Build team members table with sorting", TaskStatus.DONE),
        ("Create invite member dialog", TaskStatus.IN_PROGRESS),
        ("Add role assignment dropdown", TaskStatus.TODO),
        ("Build permission matrix view", TaskStatus.TODO),
    ],
    "Implement Redis caching layer": [
        ("Set up Redis connection pool", TaskStatus.DONE),
        ("Cache user session data", TaskStatus.IN_PROGRESS),
        ("Cache dashboard metrics with TTL", TaskStatus.TODO),
    ],
    "Build real-time notification system with WebSocket": [
        ("Set up WebSocket server with FastAPI", TaskStatus.DONE),
        ("Create client-side connection manager", TaskStatus.IN_PROGRESS),
        ("Implement notification queue", TaskStatus.IN_PROGRESS),
        ("Add reconnection logic with backoff", TaskStatus.TODO),
    ],
    "Deploy to production on AWS": [
        ("Provision RDS PostgreSQL instance", TaskStatus.TODO),
        ("Configure ECS task definitions", TaskStatus.TODO),
        ("Set up CloudFront CDN", TaskStatus.TODO),
        ("Create deployment scripts", TaskStatus.TODO),
    ],
}

DOCUMENTS = [
    {"title": "API Design Guidelines", "type": DocumentType.DOCUMENTATION,
     "content": "# API Design Guidelines\n\n## Naming Conventions\n- Use kebab-case for URLs: `/api/v1/user-profiles`\n- Use camelCase for JSON fields: `firstName`, `lastName`\n- Use plural nouns for collections: `/tasks`, `/users`\n\n## Versioning\n- Always version APIs: `/api/v1/`, `/api/v2/`\n- Use header versioning as fallback\n\n## Error Handling\n- Return consistent error response format\n- Include error code, message, and details\n- Use HTTP status codes correctly\n\n## Pagination\n- Default page size: 20, max: 100\n- Return total count in response headers\n- Support cursor-based pagination for large datasets",
     "tags": ["api", "standards", "backend"]},
    {"title": "Deployment Runbook", "type": DocumentType.RUNBOOK,
     "content": "# Production Deployment Runbook\n\n## Pre-deployment Checklist\n1. All tests passing on CI\n2. Database migrations reviewed\n3. Environment variables configured\n4. Rollback plan documented\n\n## Deployment Steps\n1. Tag release: `git tag v1.x.x`\n2. Push to main branch\n3. GitHub Actions triggers deployment\n4. Monitor health checks\n5. Verify key flows\n\n## Rollback Procedure\n1. Revert to previous ECS task definition\n2. Run database rollback if needed\n3. Clear Redis cache\n4. Notify team via Slack",
     "tags": ["devops", "deployment", "production"]},
    {"title": "New Developer Onboarding FAQ", "type": DocumentType.FAQ,
     "content": "# Onboarding FAQ\n\n## Q: How do I set up my development environment?\nA: Clone the repo, run `docker-compose up`, then `npm install` in Frontend/ and `pip install -r requirements.txt` in backend/.\n\n## Q: What are the default login credentials?\nA: Use admin@acme.com / demo123 for development.\n\n## Q: How do I run tests?\nA: Backend: `pytest` in backend/. Frontend: `npm test` in Frontend/.\n\n## Q: Where are the API docs?\nA: Visit http://localhost:8000/docs for Swagger UI.\n\n## Q: How do I create a new API endpoint?\nA: Add route in api/v1/, create schema in schemas/, add service in services/.",
     "tags": ["onboarding", "faq", "development"]},
    {"title": "System Architecture Decision Records", "type": DocumentType.ARCHITECTURE,
     "content": "# Architecture Decision Records\n\n## ADR-001: Use FastAPI over Django\n- **Decision**: FastAPI for backend framework\n- **Rationale**: Async support, auto-generated OpenAPI docs, type safety with Pydantic\n- **Consequences**: Need to build admin panel separately\n\n## ADR-002: SQLite for Development, PostgreSQL for Production\n- **Decision**: Dual database strategy\n- **Rationale**: SQLite simplifies local development, PostgreSQL for production scale\n- **Consequences**: Must use compatible SQL subset\n\n## ADR-003: Multi-Provider AI Strategy\n- **Decision**: Support multiple AI providers (OpenAI, Anthropic, Ollama, Mistral)\n- **Rationale**: Avoid vendor lock-in, allow local development with Ollama\n- **Consequences**: Need abstraction layer for provider switching",
     "tags": ["architecture", "decisions", "technical"]},
    {"title": "Sprint 12 Retrospective Notes", "type": DocumentType.MEETING_NOTES,
     "content": "# Sprint 12 Retrospective - Jan 27, 2025\n\n## What Went Well\n- Completed auth module ahead of schedule\n- Code review turnaround improved to <4 hours\n- Zero production incidents this sprint\n\n## What Could Be Improved\n- Deployment process still has manual steps\n- Test coverage on frontend components is low\n- Check-in response rate dropped to 65%\n\n## Action Items\n1. Automate remaining deployment steps (James)\n2. Add Storybook for component testing (Lisa)\n3. Review check-in frequency settings (Emily)",
     "tags": ["retrospective", "sprint", "team"]},
    {"title": "Security Best Practices", "type": DocumentType.POLICY,
     "content": "# Security Best Practices\n\n## Authentication\n- Enforce minimum 8-character passwords with complexity\n- Use bcrypt with cost factor 12 for hashing\n- Implement token rotation on refresh\n- Lock accounts after 5 failed login attempts\n\n## Data Protection\n- Encrypt sensitive data at rest (AES-256)\n- Use TLS 1.3 for all communications\n- Never log PII or credentials\n- Implement GDPR data export and deletion\n\n## API Security\n- Rate limit all endpoints\n- Validate and sanitize all inputs\n- Use parameterized queries (no raw SQL)\n- Implement CORS with whitelist",
     "tags": ["security", "policy", "compliance"]},
]

HUMAN_COMMENTS = [
    "Looks solid! The error handling is clean. One small thing — can we add a retry mechanism for transient failures?",
    "I've tested this locally and it works well. The only edge case I noticed is when the session expires mid-request.",
    "Great work on the caching implementation. The TTL strategy makes sense for our access patterns.",
    "Could we add some inline documentation for the more complex business logic? The permission checks are hard to follow.",
    "I ran the load tests and we're handling 500 concurrent users without issues. Let's target 1000 next sprint.",
    "The migration script runs cleanly on a fresh database. I've verified both up and down migrations.",
    "Nice catch on the SQL injection vulnerability. The parameterized queries look correct now.",
    "The WebSocket reconnection logic handles network drops gracefully. Tested with Chrome DevTools throttling.",
    "Let's discuss the pagination approach in standup tomorrow. I think cursor-based would be more efficient here.",
    "Performance improvement is significant — dashboard load time went from 2.3s to 0.8s with the caching layer.",
]

AI_COMMENTS = [
    "I've analyzed the task dependencies and identified a potential bottleneck. The payment integration blocks 3 downstream tasks. Consider prioritizing it this sprint.",
    "Based on velocity trends, this task is likely to take 15% longer than estimated. The team's average overrun for similar complexity tasks is 2.4 hours.",
    "Suggestion: Consider breaking this into smaller subtasks. Tasks over 16 estimated hours have a 40% higher chance of being blocked.",
    "Risk assessment: This task has a 0.35 risk score due to external dependencies. Recommend adding a fallback approach in case the third-party API is delayed.",
    "The skill match for this assignment is 85%. James has strong Python skills but limited experience with Stripe. Consider pairing with Emily who has payment integration experience.",
]


async def seed_database():
    """Main function to seed the database with comprehensive demo data."""
    print("=" * 60)
    print("  TaskPulse - Comprehensive Database Seeder")
    print("=" * 60)

    engine = create_async_engine(settings.DATABASE_URL, echo=False)

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async_session = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    async with async_session() as session:
        # ─── 1. Organization ────────────────────────────────────────
        print("\n1/27  Creating organization...")
        org = Organization(
            id=generate_uuid(),
            name="Acme Corporation",
            slug="acme-corp",
            description="Leading SaaS platform company building the next generation of project management tools.",
            plan="professional",
            settings_json=json.dumps({
                "timezone": "America/New_York",
                "working_hours_start": 9,
                "working_hours_end": 18,
                "working_days": [1, 2, 3, 4, 5],
                "checkin_interval_hours": 3,
                "notifications_enabled": True,
            }),
            is_active=True,
        )
        session.add(org)
        await session.flush()

        # ─── 2. Users ───────────────────────────────────────────────
        print("2/27  Creating 10 users...")
        pw_hash = hash_password("demo123")
        users = []
        for ud in DEMO_USERS:
            user = User(
                id=generate_uuid(),
                org_id=org.id,
                email=ud["email"],
                password_hash=pw_hash,
                first_name=ud["first_name"],
                last_name=ud["last_name"],
                role=ud["role"],
                skill_level=ud["skill_level"],
                is_active=True,
                is_email_verified=True,
                team_id=ud["team"],
                timezone="America/New_York",
                last_login=days_ago(random.randint(0, 3)),
            )
            session.add(user)
            users.append(user)
        await session.flush()

        # Name lookups
        user_by_email = {u.email: u for u in users}
        manager = user_by_email["manager@acme.com"]
        admin = user_by_email["admin@acme.com"]
        employees = [u for u in users if u.role in [UserRole.EMPLOYEE, UserRole.TEAM_LEAD]]
        alpha_team = [u for u in users if u.team_id == "team-alpha"]
        beta_team = [u for u in users if u.team_id == "team-beta"]

        # Manager relationships
        for u in users:
            if u.role in [UserRole.EMPLOYEE, UserRole.TEAM_LEAD]:
                u.manager_id = manager.id
        await session.flush()

        # ─── 3. Skills ──────────────────────────────────────────────
        print("3/27  Creating 20 skills...")
        skills = []
        skill_by_name = {}
        for sd in DEMO_SKILLS:
            skill = Skill(
                id=generate_uuid(),
                org_id=org.id,
                name=sd["name"],
                category=sd["cat"],
                description=f"Proficiency in {sd['name']}",
                org_average_level=sd["org_avg"],
                industry_average_level=sd["ind_avg"],
                related_skills_json=json.dumps(sd.get("related", [])),
            )
            session.add(skill)
            skills.append(skill)
            skill_by_name[sd["name"]] = skill
        await session.flush()

        # ─── 4. UserSkill assignments ────────────────────────────────
        print("4/27  Assigning skills to users...")
        # Define per-user skill profiles for realism
        user_skill_profiles = {
            "lead@acme.com": {"Python": 8, "FastAPI": 7, "PostgreSQL": 7, "React": 5, "TypeScript": 5, "Git": 8, "Agile": 7, "Code Review": 8, "Communication": 7, "Leadership": 6, "Docker": 6, "AWS": 5},
            "dev1@acme.com": {"Python": 7, "FastAPI": 6, "PostgreSQL": 5, "JavaScript": 6, "Git": 7, "Agile": 5, "Problem Solving": 7, "Teamwork": 6, "Docker": 4, "Redis": 5},
            "dev2@acme.com": {"React": 7, "TypeScript": 7, "JavaScript": 8, "Git": 7, "Communication": 6, "Teamwork": 7, "Agile": 5, "Problem Solving": 6, "Python": 4},
            "dev3@acme.com": {"Python": 4, "JavaScript": 5, "React": 4, "Git": 5, "Teamwork": 5, "Problem Solving": 4, "Docker": 3, "CI/CD": 3},
            "dev4@acme.com": {"React": 6, "TypeScript": 6, "JavaScript": 7, "Git": 6, "Communication": 5, "Agile": 6, "Teamwork": 6, "Problem Solving": 5, "AWS": 4},
            "dev5@acme.com": {"Python": 8, "FastAPI": 7, "PostgreSQL": 7, "Docker": 7, "Kubernetes": 5, "AWS": 6, "Git": 8, "CI/CD": 7, "Cloud Architecture": 5, "Code Review": 7, "Problem Solving": 8},
            "lead2@acme.com": {"Python": 7, "React": 6, "TypeScript": 6, "PostgreSQL": 6, "Git": 8, "Agile": 8, "Leadership": 7, "Communication": 8, "Code Review": 7, "Teamwork": 8, "Machine Learning": 4},
        }

        for email, skill_map in user_skill_profiles.items():
            user = user_by_email[email]
            for skill_name, level in skill_map.items():
                if skill_name not in skill_by_name:
                    continue
                skill = skill_by_name[skill_name]
                # Generate history entries
                history = []
                for m in range(5, 0, -1):
                    history.append({
                        "date": (NOW - timedelta(days=30 * m)).isoformat(),
                        "level": max(1, level - random.uniform(0, 1.5) * (m / 5)),
                    })
                trend = random.choice([SkillTrend.IMPROVING, SkillTrend.STABLE, SkillTrend.STABLE])
                if level <= 4:
                    trend = SkillTrend.IMPROVING
                us = UserSkill(
                    id=generate_uuid(),
                    org_id=org.id,
                    user_id=user.id,
                    skill_id=skill.id,
                    level=level,
                    confidence=round(random.uniform(0.6, 0.95), 2),
                    trend=trend,
                    last_demonstrated=days_ago(random.randint(1, 30)),
                    demonstration_count=random.randint(5, 50),
                    source=random.choice(["inferred", "self_reported", "manager_assessed"]),
                    level_history_json=json.dumps(history),
                    is_certified=random.random() > 0.8,
                )
                session.add(us)
        await session.flush()

        # ─── 5. Tasks ───────────────────────────────────────────────
        print("5/27  Creating 25 tasks...")
        tasks = []
        task_by_title = {}

        for td in DEMO_TASKS:
            status = td["status"]
            assignee = random.choice(employees)
            created = days_ago(random.randint(5, 35))
            started = None
            completed = None

            if status in [TaskStatus.IN_PROGRESS, TaskStatus.REVIEW, TaskStatus.DONE, TaskStatus.BLOCKED]:
                started = created + timedelta(hours=random.randint(2, 48))
            if status == TaskStatus.DONE:
                completed = started + timedelta(hours=td["hours"] * random.uniform(0.8, 1.3))

            # Some tasks overdue
            if status in [TaskStatus.IN_PROGRESS, TaskStatus.BLOCKED]:
                deadline = days_from_now(random.choice([-2, -1, 3, 5, 7, 10]))
            elif status == TaskStatus.TODO:
                deadline = days_from_now(random.randint(5, 14))
            else:
                deadline = days_from_now(random.randint(1, 10))

            task = Task(
                id=generate_uuid(),
                org_id=org.id,
                title=td["title"],
                description=td["desc"],
                status=status,
                priority=td["priority"],
                estimated_hours=td["hours"],
                actual_hours=round(td["hours"] * random.uniform(0.7, 1.2), 1) if status == TaskStatus.DONE else round(random.uniform(0, td["hours"] * 0.6), 1),
                created_by=manager.id,
                assigned_to=assignee.id,
                team_id=assignee.team_id or "team-alpha",
                deadline=deadline,
                started_at=started,
                completed_at=completed,
                risk_score=round(random.uniform(0.1, 0.6), 2),
                complexity_score=round(random.uniform(0.3, 0.9), 2),
                confidence_score=round(random.uniform(0.5, 0.95), 2),
                tags_json=json.dumps(td.get("tags", [])),
                skills_required_json=json.dumps(td.get("skills", [])),
                blocker_description=td.get("blocker"),
                blocker_type="DEPENDENCY" if td.get("blocker") else None,
            )
            task.created_at = created
            session.add(task)
            tasks.append(task)
            task_by_title[td["title"]] = task
        await session.flush()

        # ─── 6. Subtasks ────────────────────────────────────────────
        print("6/27  Creating subtasks...")
        subtask_count = 0
        for parent_title, subs in SUBTASKS_MAP.items():
            parent = task_by_title.get(parent_title)
            if not parent:
                continue
            for i, (sub_title, sub_status) in enumerate(subs):
                sub = Task(
                    id=generate_uuid(),
                    org_id=org.id,
                    title=sub_title,
                    status=sub_status,
                    priority=parent.priority,
                    estimated_hours=random.randint(2, 6),
                    created_by=manager.id,
                    assigned_to=parent.assigned_to,
                    parent_task_id=parent.id,
                    sort_order=i,
                    team_id=parent.team_id,
                )
                session.add(sub)
                subtask_count += 1
        await session.flush()
        print(f"       {subtask_count} subtasks created")

        # ─── 7. Task Dependencies ───────────────────────────────────
        print("7/27  Creating task dependencies...")
        deps_config = [
            ("Create REST API endpoints", "Design database schema for multi-tenant SaaS"),
            ("Build analytics dashboard with Recharts", "Implement JWT authentication with refresh tokens"),
            ("Build Stripe payment integration", "Implement JWT authentication with refresh tokens"),
            ("Deploy to production on AWS", "Set up CI/CD pipeline with GitHub Actions"),
            ("Write integration tests for payment flow", "Build Stripe payment integration"),
            ("Implement audit logging for compliance", "Implement role-based access control (RBAC)"),
        ]
        for task_title, dep_title in deps_config:
            t = task_by_title.get(task_title)
            d = task_by_title.get(dep_title)
            if t and d:
                session.add(TaskDependency(
                    id=generate_uuid(), task_id=t.id, depends_on_id=d.id, is_blocking=True,
                    description=f"{dep_title} must be completed first",
                ))
        await session.flush()

        # ─── 8. Task History ────────────────────────────────────────
        print("8/27  Creating task history...")
        for task in tasks:
            session.add(TaskHistory(
                id=generate_uuid(), task_id=task.id, user_id=manager.id,
                action="created", created_at=task.created_at,
            ))
            if task.status != TaskStatus.TODO:
                session.add(TaskHistory(
                    id=generate_uuid(), task_id=task.id, user_id=task.assigned_to,
                    action="status_changed", field_name="status",
                    old_value="TODO", new_value=task.status.value,
                    created_at=task.started_at or days_ago(5),
                ))
        await session.flush()

        # ─── 9. Task Comments ───────────────────────────────────────
        print("9/27  Creating task comments...")
        for task in tasks:
            # 1-3 human comments per task
            for _ in range(random.randint(1, 3)):
                commenter = random.choice(users[:7])
                session.add(TaskComment(
                    id=generate_uuid(), task_id=task.id, user_id=commenter.id,
                    content=random.choice(HUMAN_COMMENTS),
                    created_at=task.created_at + timedelta(hours=random.randint(1, 72)),
                ))
            # 30% chance of AI comment
            if random.random() > 0.7:
                session.add(TaskComment(
                    id=generate_uuid(), task_id=task.id, user_id=None,
                    content=random.choice(AI_COMMENTS), is_ai_generated=True,
                    created_at=task.created_at + timedelta(hours=random.randint(2, 48)),
                ))
        await session.flush()

        # ─── 10. Check-ins ──────────────────────────────────────────
        print("10/27 Creating check-ins...")
        active_tasks = [t for t in tasks if t.status in [TaskStatus.IN_PROGRESS, TaskStatus.BLOCKED, TaskStatus.REVIEW]]
        checkin_count = 0
        for task in active_tasks:
            triggers = [CheckInTrigger.SCHEDULED, CheckInTrigger.SCHEDULED, CheckInTrigger.DEADLINE_APPROACHING]
            if task.status == TaskStatus.BLOCKED:
                triggers.append(CheckInTrigger.BLOCKER_DETECTED)
            for cycle in range(1, random.randint(3, 6)):
                status_pick = random.random()
                if status_pick < 0.6:
                    ci_status = CheckInStatus.RESPONDED
                elif status_pick < 0.75:
                    ci_status = CheckInStatus.PENDING
                elif status_pick < 0.85:
                    ci_status = CheckInStatus.SKIPPED
                elif status_pick < 0.93:
                    ci_status = CheckInStatus.EXPIRED
                else:
                    ci_status = CheckInStatus.ESCALATED

                scheduled = days_ago(0, 3 * cycle)
                responded = scheduled + timedelta(minutes=random.randint(5, 45)) if ci_status == CheckInStatus.RESPONDED else None
                progress = random.choice(list(ProgressIndicator)) if ci_status == CheckInStatus.RESPONDED else None

                progress_notes = None
                blockers = None
                if ci_status == CheckInStatus.RESPONDED:
                    progress_notes = random.choice([
                        "Making good progress. Finished the core logic, working on edge cases now.",
                        "Slower than expected due to a tricky bug in the middleware layer.",
                        "On track. Just wrapped up the database queries, moving to API layer.",
                        "Completed the main feature. Running tests before submitting for review.",
                        "Hit a minor issue with dependency versions but resolved it.",
                    ])
                if progress in [ProgressIndicator.BLOCKED, ProgressIndicator.SIGNIFICANTLY_BEHIND]:
                    blockers = random.choice([
                        "Waiting on API credentials from the third-party provider.",
                        "Database migration is causing conflicts with existing data.",
                        "Need code review approval before proceeding to next phase.",
                    ])

                ci = CheckIn(
                    id=generate_uuid(), org_id=org.id, task_id=task.id,
                    user_id=task.assigned_to, cycle_number=cycle,
                    trigger=random.choice(triggers), status=ci_status,
                    scheduled_at=scheduled, responded_at=responded,
                    progress_indicator=progress, progress_notes=progress_notes,
                    blockers_reported=blockers,
                    help_needed=random.random() > 0.8,
                    sentiment_score=round(random.uniform(-0.2, 0.8), 2),
                    friction_detected=random.random() > 0.85,
                    escalated=ci_status == CheckInStatus.ESCALATED,
                    escalated_to=manager.id if ci_status == CheckInStatus.ESCALATED else None,
                    escalated_at=scheduled + timedelta(hours=2) if ci_status == CheckInStatus.ESCALATED else None,
                )
                session.add(ci)
                checkin_count += 1
        await session.flush()
        print(f"       {checkin_count} check-ins created")

        # Check-in configs
        for team in ["team-alpha", "team-beta"]:
            session.add(CheckInConfig(
                id=generate_uuid(), org_id=org.id, team_id=team,
                interval_hours=3, max_daily_checkins=4,
                work_start_hour=9, work_end_hour=18,
                auto_escalate_after_missed=2, silent_mode_threshold=0.8,
            ))
        await session.flush()

        # ─── 11. Skill Gaps ─────────────────────────────────────────
        print("11/27 Creating skill gaps...")
        gaps_data = [
            ("dev1@acme.com", "Docker", GapType.CRITICAL, 4, 6, "Backend Developer"),
            ("dev1@acme.com", "Leadership", GapType.GROWTH, 3, 6, "Senior Developer"),
            ("dev2@acme.com", "Python", GapType.CRITICAL, 4, 6, "Full Stack Developer"),
            ("dev2@acme.com", "PostgreSQL", GapType.GROWTH, 3, 6, "Full Stack Developer"),
            ("dev3@acme.com", "React", GapType.CRITICAL, 4, 6, "Frontend Developer"),
            ("dev3@acme.com", "TypeScript", GapType.CRITICAL, 3, 6, "Frontend Developer"),
            ("dev3@acme.com", "Docker", GapType.GROWTH, 3, 5, "DevOps Awareness"),
            ("dev4@acme.com", "Machine Learning", GapType.STRETCH, 2, 5, "ML Engineer"),
            ("dev5@acme.com", "Leadership", GapType.GROWTH, 5, 7, "Tech Lead"),
            ("lead@acme.com", "Machine Learning", GapType.STRETCH, 3, 5, "Technical Director"),
        ]
        for email, skill_name, gap_type, current, required, role in gaps_data:
            user = user_by_email.get(email)
            skill = skill_by_name.get(skill_name)
            if user and skill:
                session.add(SkillGap(
                    id=generate_uuid(), org_id=org.id,
                    user_id=user.id, skill_id=skill.id,
                    gap_type=gap_type, current_level=current, required_level=required,
                    gap_size=required - current, for_role=role,
                    priority=random.randint(5, 9),
                    learning_resources_json=json.dumps([
                        {"title": f"Advanced {skill_name} Course", "url": f"https://learn.example.com/{skill_name.lower().replace(' ', '-')}"},
                        {"title": f"{skill_name} Best Practices Guide", "url": f"https://docs.example.com/{skill_name.lower().replace(' ', '-')}-guide"},
                    ]),
                ))
        await session.flush()

        # ─── 12. Skill Metrics ──────────────────────────────────────
        print("12/27 Creating skill metrics...")
        for user in employees:
            session.add(SkillMetrics(
                id=generate_uuid(), org_id=org.id, user_id=user.id,
                period_start=days_ago(90), period_end=NOW,
                task_completion_velocity=round(random.uniform(3, 8), 1),
                quality_score=round(random.uniform(0.7, 0.95), 2),
                self_sufficiency_index=round(random.uniform(0.5, 0.9), 2),
                learning_velocity=round(random.uniform(0.05, 0.15), 3),
                collaboration_score=round(random.uniform(0.6, 0.9), 2),
                help_given_count=random.randint(3, 20),
                help_received_count=random.randint(1, 15),
                blockers_encountered=random.randint(2, 12),
                blockers_self_resolved=random.randint(1, 8),
                avg_blocker_resolution_hours=round(random.uniform(2, 12), 1),
                velocity_percentile=round(random.uniform(30, 90), 1),
                quality_percentile=round(random.uniform(40, 95), 1),
                learning_percentile=round(random.uniform(25, 85), 1),
            ))
        await session.flush()

        # ─── 13. Learning Paths ─────────────────────────────────────
        print("13/27 Creating learning paths...")
        paths = [
            ("dev1@acme.com", "Senior Backend Engineer", "Advance from mid-level to senior backend role with focus on system design and DevOps.",
             "Senior Backend Developer", 45,
             [{"title": "Complete Docker certification", "done": True},
              {"title": "Lead a code review session", "done": True},
              {"title": "Design a microservice architecture", "done": False},
              {"title": "Mentor a junior developer", "done": False}]),
            ("dev2@acme.com", "Full Stack Development Mastery", "Build strong backend skills to complement frontend expertise.",
             "Full Stack Developer", 30,
             [{"title": "Complete Python intermediate course", "done": True},
              {"title": "Build a REST API from scratch", "done": False},
              {"title": "Contribute to backend codebase", "done": False}]),
            ("dev3@acme.com", "Frontend Developer Growth", "Strengthen core frontend skills and learn modern tooling.",
             "Mid-Level Frontend Developer", 20,
             [{"title": "Complete TypeScript fundamentals", "done": True},
              {"title": "Build a React component library", "done": False},
              {"title": "Learn testing with Jest and RTL", "done": False},
              {"title": "Contribute to design system", "done": False}]),
            ("lead2@acme.com", "Engineering Manager Track", "Transition from tech lead to engineering manager role.",
             "Engineering Manager", 55,
             [{"title": "Complete management fundamentals course", "done": True},
              {"title": "Lead sprint planning for 3 sprints", "done": True},
              {"title": "Conduct 1:1s with all team members", "done": True},
              {"title": "Create team development plan", "done": False},
              {"title": "Present quarterly team metrics", "done": False}]),
        ]
        for email, title, desc, target, progress, milestones in paths:
            user = user_by_email.get(email)
            if user:
                session.add(LearningPath(
                    id=generate_uuid(), org_id=org.id, user_id=user.id,
                    title=title, description=desc, target_role=target,
                    progress_percentage=progress,
                    milestones_json=json.dumps(milestones),
                    skills_json=json.dumps([]),
                    started_at=days_ago(60),
                    target_completion=days_from_now(90),
                    is_active=True, is_ai_generated=True,
                ))
        await session.flush()

        # ─── 14. Documents ──────────────────────────────────────────
        print("14/27 Creating knowledge base documents...")
        docs = []
        for dd in DOCUMENTS:
            doc = Document(
                id=generate_uuid(), org_id=org.id,
                title=dd["title"], description=f"Reference document: {dd['title']}",
                source=DocumentSource.MANUAL_UPLOAD,
                content=dd["content"],
                doc_type=dd["type"],
                status=DocumentStatus.INDEXED,
                file_type="md", language="en", is_public=True,
                tags_json=json.dumps(dd["tags"]),
                categories_json=json.dumps([dd["type"].value]),
                view_count=random.randint(5, 50),
                helpful_count=random.randint(2, 20),
                processed_at=days_ago(random.randint(3, 20)),
            )
            session.add(doc)
            docs.append(doc)
        await session.flush()

        # ─── 15. Document Chunks ─────────────────────────────────────
        print("15/27 Creating document chunks...")
        for doc in docs:
            content = doc.content
            # Split by sections
            sections = content.split("\n\n")
            for i, section in enumerate(sections):
                if len(section.strip()) < 20:
                    continue
                session.add(DocumentChunk(
                    id=generate_uuid(), document_id=doc.id,
                    content=section.strip(), chunk_index=i,
                    token_count=len(section.split()),
                    metadata_json=json.dumps({"section_index": i}),
                ))
        await session.flush()

        # ─── 16. Predictions ────────────────────────────────────────
        print("16/27 Creating predictions...")
        in_progress = [t for t in tasks if t.status == TaskStatus.IN_PROGRESS]
        for task in in_progress:
            base_days = task.estimated_hours / 6  # ~6 productive hours/day
            session.add(Prediction(
                id=generate_uuid(), org_id=org.id,
                prediction_type=PredictionType.TASK_COMPLETION,
                task_id=task.id, user_id=task.assigned_to,
                predicted_date_p25=days_from_now(int(base_days * 0.7)),
                predicted_date_p50=days_from_now(int(base_days)),
                predicted_date_p90=days_from_now(int(base_days * 1.5)),
                confidence=round(random.uniform(0.6, 0.9), 2),
                risk_score=round(random.uniform(0.1, 0.5), 2),
                risk_factors_json=json.dumps([
                    {"factor": "External dependency", "impact": round(random.uniform(0.1, 0.3), 2)},
                    {"factor": "Complexity score", "impact": round(random.uniform(0.05, 0.2), 2)},
                ]),
                model_version="v1.2",
            ))
        # Team velocity prediction
        session.add(Prediction(
            id=generate_uuid(), org_id=org.id,
            prediction_type=PredictionType.TEAM_VELOCITY,
            team_id="team-alpha",
            predicted_date_p50=days_from_now(14),
            confidence=0.78, risk_score=0.25,
            risk_factors_json=json.dumps([
                {"factor": "Sprint scope creep", "impact": 0.15},
                {"factor": "Team member PTO", "impact": 0.1},
            ]),
            model_version="v1.2",
        ))
        await session.flush()

        # ─── 17. Velocity Snapshots ──────────────────────────────────
        print("17/27 Creating velocity snapshots...")
        for week in range(12, 0, -1):
            for team_id in ["team-alpha", "team-beta"]:
                base_completed = 10 if team_id == "team-alpha" else 8
                session.add(VelocitySnapshot(
                    id=generate_uuid(), org_id=org.id, team_id=team_id,
                    period_start=days_ago(week * 7),
                    period_end=days_ago((week - 1) * 7),
                    tasks_completed=base_completed + random.randint(-3, 4),
                    story_points_completed=round((base_completed + random.randint(-2, 3)) * 2.5, 1),
                    velocity=round(random.uniform(0.7, 0.95), 2),
                    capacity_utilization=round(random.uniform(0.65, 0.92), 2),
                ))
        await session.flush()

        # ─── 18. Automation Patterns ─────────────────────────────────
        print("18/27 Creating automation patterns...")
        patterns_data = [
            ("Daily Standup Summary", "Automatically generates daily standup summary from check-in responses and task updates.",
             PatternStatus.IMPLEMENTED, 5.0, 0.92, 8, 2.5, 450, 3),
            ("Auto-assign Bug Tickets", "Automatically assigns incoming bug reports to the most suitable developer based on skills and workload.",
             PatternStatus.ACCEPTED, 3.2, 0.85, 6, 1.5, 280, 5),
            ("Sprint Report Generation", "Generates end-of-sprint reports with velocity metrics, completion rates, and risk analysis.",
             PatternStatus.DETECTED, 1.0, 0.88, 10, 3.0, 520, 4),
            ("Stale PR Reminder", "Sends reminders for pull requests that have been open without review for more than 24 hours.",
             PatternStatus.SUGGESTED, 4.0, 0.95, 7, 1.0, 180, 2),
            ("Test Failure Notification", "Notifies relevant developers when CI tests fail on their branches.",
             PatternStatus.REJECTED, 6.0, 0.78, 10, 0.5, 90, 1),
        ]
        patterns = []
        for name, desc, status, freq, consistency, affected, hours_saved, cost_saved, complexity in patterns_data:
            p = AutomationPattern(
                id=generate_uuid(), org_id=org.id,
                name=name, description=desc, status=status,
                pattern_type="workflow_automation",
                frequency_per_week=freq, consistency_score=consistency,
                users_affected=affected, estimated_hours_saved_weekly=hours_saved,
                estimated_cost_savings_monthly=cost_saved,
                implementation_complexity=complexity,
                accepted_by=admin.id if status in [PatternStatus.ACCEPTED, PatternStatus.IMPLEMENTED] else None,
                accepted_at=days_ago(15) if status in [PatternStatus.ACCEPTED, PatternStatus.IMPLEMENTED] else None,
                rejection_reason="Already covered by GitHub Actions notifications" if status == PatternStatus.REJECTED else None,
            )
            session.add(p)
            patterns.append(p)
        await session.flush()

        # ─── 19. AI Agents (automation) ──────────────────────────────
        print("19/27 Creating AI agents...")
        agents_data = [
            ("Standup Bot", "Collects and summarizes daily standup responses", AgentStatus.LIVE, patterns[0].id, 45, 44, 120, days_ago(1)),
            ("Bug Triager", "Analyzes and assigns bug reports based on expertise", AgentStatus.SHADOW, patterns[1].id, 12, 10, 0, days_ago(2)),
            ("Report Generator", "Creates automated sprint and analytics reports", AgentStatus.SUPERVISED, patterns[2].id if len(patterns) > 2 else None, 8, 7, 35, days_ago(5)),
        ]
        ai_agents = []
        for name, desc, status, pat_id, total, success, hours, last_run in agents_data:
            ag = AIAgent(
                id=generate_uuid(), org_id=org.id,
                name=name, description=desc, status=status,
                pattern_id=pat_id,
                total_runs=total, successful_runs=success,
                hours_saved_total=hours, last_run_at=last_run,
                shadow_match_rate=round(random.uniform(0.8, 0.98), 2) if status == AgentStatus.SHADOW else None,
                shadow_runs=total if status == AgentStatus.SHADOW else 0,
                created_by=admin.id,
                approved_by=admin.id if status != AgentStatus.SHADOW else None,
            )
            session.add(ag)
            ai_agents.append(ag)
        await session.flush()

        # ─── 20. Agent Runs ─────────────────────────────────────────
        print("20/27 Creating agent runs...")
        for ag in ai_agents:
            for r in range(min(ag.total_runs, 5)):
                session.add(AgentRun(
                    id=generate_uuid(), org_id=org.id, agent_id=ag.id,
                    started_at=days_ago(r + 1),
                    completed_at=days_ago(r + 1) + timedelta(seconds=random.randint(5, 120)),
                    status="success" if random.random() > 0.1 else "failed",
                    execution_time_ms=random.randint(500, 15000),
                    is_shadow=ag.status == AgentStatus.SHADOW,
                    matched_human=random.random() > 0.15 if ag.status == AgentStatus.SHADOW else None,
                ))
        await session.flush()

        # ─── 21. Org Health Snapshots ────────────────────────────────
        print("21/27 Creating org health snapshots...")
        health_trend = [
            (28, 72, 68, 80, 55, 65, 71),
            (21, 75, 70, 82, 58, 67, 73),
            (14, 73, 71, 81, 60, 70, 74),
            (7, 78, 72, 83, 62, 72, 76),
        ]
        for days_back, prod, skill_cov, mgmt, auto, deliver, overall in health_trend:
            session.add(OrgHealthSnapshot(
                id=generate_uuid(), org_id=org.id,
                snapshot_date=days_ago(days_back),
                productivity_index=prod, skill_coverage_index=skill_cov,
                management_quality_index=mgmt, automation_maturity_index=auto,
                delivery_predictability_index=deliver, overall_health_score=overall,
                total_employees=len(employees), active_tasks=len([t for t in tasks if t.status != TaskStatus.DONE]),
                blocked_tasks=len([t for t in tasks if t.status == TaskStatus.BLOCKED]),
                overdue_tasks=3, high_attrition_risk_count=1, high_burnout_risk_count=1,
            ))
        await session.flush()

        # ─── 22. Manager Effectiveness ───────────────────────────────
        print("22/27 Creating manager effectiveness...")
        session.add(ManagerEffectiveness(
            id=generate_uuid(), org_id=org.id, manager_id=manager.id,
            snapshot_date=days_ago(1),
            team_size=len(employees), team_velocity_avg=82,
            team_quality_avg=85, escalation_response_time_hours=2.5,
            escalation_resolution_rate=0.88, team_attrition_rate=0.05,
            team_satisfaction_score=0.82, redundancy_score=0.15,
            assignment_quality_score=0.87, workload_distribution_score=0.78,
            effectiveness_score=85, org_percentile=72,
        ))
        await session.flush()

        # ─── 23. Restructuring Scenarios ─────────────────────────────
        print("23/27 Creating restructuring scenarios...")
        for name, stype, cost, prod, affected, risk in [
            ("Merge Alpha and Beta into unified platform team", "team_merge", -8.5, 12.0, 8, 0.35),
            ("Automate QA testing with AI agent", "automation_replace", -15.0, 8.0, 2, 0.45),
        ]:
            session.add(RestructuringScenario(
                id=generate_uuid(), org_id=org.id, created_by=admin.id,
                name=name, scenario_type=stype,
                description=f"Scenario analysis: {name}",
                projected_cost_change=cost, projected_productivity_change=prod,
                projected_skill_coverage_change=random.uniform(-5, 5),
                affected_employees=affected, overall_risk_score=risk,
                risk_factors_json=json.dumps([
                    {"factor": "Team culture disruption", "severity": "medium"},
                    {"factor": "Knowledge transfer gaps", "severity": "low"},
                ]),
                is_draft=True,
            ))
        await session.flush()

        # ─── 24. Workforce Scores ────────────────────────────────────
        print("24/27 Creating workforce scores...")
        score_profiles = {
            "lead@acme.com": (88, 85, 90, 82, 78, 86, 82, 0.08, 0.12, "stable"),
            "dev1@acme.com": (76, 78, 82, 68, 72, 74, 65, 0.12, 0.18, "improving"),
            "dev2@acme.com": (82, 80, 85, 70, 75, 80, 72, 0.10, 0.15, "stable"),
            "dev3@acme.com": (65, 62, 70, 55, 68, 65, 42, 0.25, 0.30, "improving"),
            "dev4@acme.com": (78, 75, 80, 72, 70, 76, 68, 0.15, 0.20, "stable"),
            "dev5@acme.com": (90, 88, 92, 85, 80, 88, 88, 0.05, 0.08, "improving"),
            "lead2@acme.com": (86, 84, 88, 80, 82, 85, 80, 0.07, 0.10, "stable"),
        }
        for email, (overall, vel, qual, suf, learn, collab, pct, attr, burn, trend) in score_profiles.items():
            user = user_by_email.get(email)
            if user:
                session.add(WorkforceScore(
                    id=generate_uuid(), org_id=org.id, user_id=user.id,
                    overall_score=overall, velocity_score=vel, quality_score=qual,
                    self_sufficiency_score=suf, learning_score=learn,
                    collaboration_score=collab, percentile_rank=pct,
                    attrition_risk_score=attr, burnout_risk_score=burn,
                    score_trend=trend,
                ))
        await session.flush()

        # ─── 25. Notifications ───────────────────────────────────────
        print("25/27 Creating notifications...")
        notifs = [
            (user_by_email["dev1@acme.com"], NotificationType.TASK_ASSIGNED, "New task assigned",
             "You've been assigned 'Build Stripe payment integration'", False),
            (user_by_email["dev1@acme.com"], NotificationType.CHECKIN_REMINDER, "Check-in due",
             "How's your progress on the payment integration?", False),
            (user_by_email["dev1@acme.com"], NotificationType.AI_SUGGESTION, "AI Insight",
             "Consider breaking the payment task into smaller subtasks for better tracking.", False),
            (user_by_email["dev2@acme.com"], NotificationType.DEADLINE_APPROACHING, "Deadline approaching",
             "Task 'Create team management UI' is due in 2 days.", False),
            (user_by_email["dev2@acme.com"], NotificationType.TASK_COMPLETED, "Task completed",
             "Emily marked 'Build responsive navigation' as done.", True),
            (user_by_email["lead@acme.com"], NotificationType.ESCALATION, "Escalation",
             "James reported a blocker on 'Deploy to production on AWS'.", False),
            (user_by_email["lead@acme.com"], NotificationType.TASK_BLOCKED, "Task blocked",
             "'Google OAuth SSO' is blocked: OAuth consent screen pending verification.", True),
            (manager, NotificationType.SYSTEM, "Weekly report ready",
             "Your team's weekly productivity report is now available.", False),
            (manager, NotificationType.AI_SUGGESTION, "Team insight",
             "David's learning velocity has increased 25% this month. Consider assigning more challenging tasks.", True),
            (admin, NotificationType.SYSTEM, "System update",
             "TaskPulse v2.1 is now available with improved AI predictions.", True),
            (user_by_email["dev3@acme.com"], NotificationType.TASK_ASSIGNED, "New task assigned",
             "You've been assigned 'Build mobile-responsive task board'.", False),
            (user_by_email["dev4@acme.com"], NotificationType.MENTION, "You were mentioned",
             "Emily mentioned you in a comment on 'Create settings page'.", False),
        ]
        for user, ntype, title, message, is_read in notifs:
            session.add(Notification(
                id=generate_uuid(), org_id=org.id, user_id=user.id,
                notification_type=ntype, title=title, message=message,
                channel=NotificationChannel.IN_APP,
                is_read=is_read, read_at=days_ago(1) if is_read else None,
                delivered=True, delivered_at=days_ago(random.randint(0, 3)),
                created_at=days_ago(random.randint(0, 5)),
            ))
        await session.flush()

        # ─── 26. Agents (new system) ────────────────────────────────
        print("26/27 Creating agent system records...")
        agent_defs = [
            ("chat_agent", "Chat Agent", "Conversational AI for user interactions", AgentType.CONVERSATION, ["chat", "task_creation"]),
            ("task_decomposer", "Task Decomposer", "Breaks complex tasks into subtasks", AgentType.AI, ["decompose", "estimate"]),
            ("skill_analyzer", "Skill Analyzer", "Infers and tracks user skills from task data", AgentType.AI, ["skill_graph", "gap_analysis"]),
            ("checkin_scheduler", "Check-in Scheduler", "Schedules and manages proactive check-ins", AgentType.INTEGRATION, ["schedule", "notify"]),
        ]
        new_agents = []
        for name, display, desc, atype, caps in agent_defs:
            ag = Agent(
                id=generate_uuid(), org_id=org.id,
                name=name, display_name=display, description=desc,
                agent_type=atype, status=AgentStatusDB.ACTIVE,
                capabilities=caps, is_enabled=True,
                execution_count=random.randint(10, 100),
                success_count=random.randint(8, 95),
                error_count=random.randint(0, 5),
                avg_duration_ms=round(random.uniform(200, 5000), 1),
                last_execution_at=days_ago(random.randint(0, 2)),
            )
            session.add(ag)
            new_agents.append(ag)
        await session.flush()

        # Agent executions
        for ag in new_agents:
            for i in range(min(3, ag.execution_count)):
                session.add(AgentExecution(
                    id=generate_uuid(), org_id=org.id, agent_id=ag.id,
                    event_type="user_request" if ag.agent_type == AgentType.CONVERSATION else "scheduled",
                    trigger_source="user" if ag.agent_type == AgentType.CONVERSATION else "system",
                    user_id=random.choice(employees).id,
                    status=ExecutionStatus.COMPLETED,
                    started_at=days_ago(i + 1),
                    completed_at=days_ago(i + 1) + timedelta(milliseconds=random.randint(200, 5000)),
                    duration_ms=random.randint(200, 5000),
                    success=True,
                    tokens_used=random.randint(100, 2000),
                    api_calls=random.randint(1, 5),
                ))
        await session.flush()

        # ─── 27. Audit Logs ──────────────────────────────────────────
        print("27/27 Creating audit logs...")
        audit_entries = [
            (ActorType.USER, admin, AuditAction.LOGIN, "user", "Logged in from Chrome/macOS", 3),
            (ActorType.USER, manager, AuditAction.LOGIN, "user", "Logged in from Firefox/Windows", 2),
            (ActorType.USER, admin, AuditAction.CREATE, "organization", "Created organization Acme Corporation", 30),
            (ActorType.ADMIN, admin, AuditAction.CONFIG_CHANGE, "organization", "Updated check-in interval to 3 hours", 15),
            (ActorType.USER, manager, AuditAction.CREATE, "task", "Created 25 tasks for SaaS platform project", 20),
            (ActorType.AI, None, AuditAction.CREATE, "prediction", "Generated delivery predictions for 6 tasks", 5),
            (ActorType.USER, user_by_email["lead@acme.com"], AuditAction.UPDATE, "task", "Updated task status from TODO to IN_PROGRESS", 4),
            (ActorType.SYSTEM, None, AuditAction.CREATE, "checkin", "Scheduled 18 check-ins for active tasks", 3),
            (ActorType.USER, user_by_email["dev1@acme.com"], AuditAction.UPDATE, "task", "Reported blocker on Deploy to production", 2),
            (ActorType.ADMIN, admin, AuditAction.ROLE_CHANGE, "user", "Promoted Priya Patel to Team Lead", 10),
            (ActorType.USER, manager, AuditAction.CREATE, "skill", "Added 20 skills to organization catalog", 25),
            (ActorType.AI, None, AuditAction.UPDATE, "skill", "Updated skill levels for 7 employees based on task analysis", 1),
            (ActorType.SYSTEM, None, AuditAction.CREATE, "notification", "Sent 12 notifications to team members", 1),
        ]
        for actor_type, user, action, resource, desc, days_back in audit_entries:
            session.add(AuditLog(
                id=generate_uuid(), org_id=org.id,
                actor_type=actor_type,
                actor_id=user.id if user else None,
                actor_name=f"{user.first_name} {user.last_name}" if user else ("AI Agent" if actor_type == ActorType.AI else "System"),
                action=action, resource_type=resource, description=desc,
                timestamp=days_ago(days_back),
                ip_address="192.168.1." + str(random.randint(10, 99)) if user else None,
            ))
        await session.flush()

        # ─── Integrations ───────────────────────────────────────────
        print("       Creating integrations...")
        integrations = [
            ("GitHub", IntegrationType.GITHUB, True, "Connected to acme-corp/taskpulse repo"),
            ("Slack", IntegrationType.SLACK, True, "Connected to #engineering channel"),
            ("Jira", IntegrationType.JIRA, False, "Pending configuration"),
            ("Confluence", IntegrationType.CONFLUENCE, False, None),
        ]
        for name, itype, active, desc in integrations:
            session.add(Integration(
                id=generate_uuid(), org_id=org.id,
                integration_type=itype, name=name,
                description=desc,
                is_active=active,
                connected_by=admin.id if active else None,
                connected_at=days_ago(20) if active else None,
                last_sync_at=days_ago(1) if active else None,
                last_sync_status="success" if active else None,
            ))
        await session.flush()

        # ─── Commit everything ───────────────────────────────────────
        await session.commit()

        # ─── Summary ────────────────────────────────────────────────
        print("\n" + "=" * 60)
        print("  Database seeding completed successfully!")
        print("=" * 60)
        print(f"""
  Organization:  Acme Corporation
  Users:         {len(users)} (across 2 teams)
  Skills:        {len(skills)} (6 categories)
  Tasks:         {len(tasks)} + {subtask_count} subtasks
  Dependencies:  {len(deps_config)}
  Check-ins:     {checkin_count}
  Skill Gaps:    {len(gaps_data)}
  Learning Paths: {len(paths)}
  Documents:     {len(DOCUMENTS)}
  Predictions:   {len(in_progress) + 1}
  Velocity:      {12 * 2} weekly snapshots
  Automation:    {len(patterns_data)} patterns, {len(agents_data)} agents
  Org Health:    {len(health_trend)} snapshots
  Notifications: {len(notifs)}
  Audit Logs:    {len(audit_entries)}
  Integrations:  {len(integrations)}

  Login Credentials (password: demo123):
    Admin:    admin@acme.com
    Manager:  manager@acme.com
    Lead:     lead@acme.com / lead2@acme.com
    Dev:      dev1-5@acme.com
    Viewer:   viewer@acme.com
""")
        print("=" * 60)

    await engine.dispose()


async def clear_database():
    """Clear all data from the database."""
    print("Clearing database...")
    engine = create_async_engine(settings.DATABASE_URL, echo=False)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)
    await engine.dispose()
    print("Database cleared!")


if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1 and sys.argv[1] == "--clear":
        asyncio.run(clear_database())
    else:
        asyncio.run(seed_database())

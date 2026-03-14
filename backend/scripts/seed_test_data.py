"""
Seed script for TaskPulse AI - Creates admin users, test users, and sample data.

Usage:
    cd backend
    python scripts/seed_test_data.py

Creates:
    - 1 Organization ("TaskPulse Demo")
    - 6 Users (one per role: super_admin, org_admin, manager, team_lead, employee, viewer)
    - 12 Tasks with various statuses and priorities
    - Check-in configs and sample check-ins
    - Task comments and history entries
"""

import asyncio
import os
import sys
import uuid
from datetime import datetime, timedelta, timezone

# Add backend to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dotenv import load_dotenv
load_dotenv()

from supabase import create_client


# ─── Config ──────────────────────────────────────────────────────────────────
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_SERVICE_ROLE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY")
DATABASE_URL = os.getenv("DATABASE_URL")

PASSWORD = "TestPass123"  # Password for all test users (meets validation: uppercase, lowercase, digit)

# ─── Test Users ──────────────────────────────────────────────────────────────
TEST_USERS = [
    {
        "email": "admin@taskpulse.demo",
        "first_name": "Super",
        "last_name": "Admin",
        "role": "super_admin",
        "skill_level": "lead",
    },
    {
        "email": "orgadmin@taskpulse.demo",
        "first_name": "Org",
        "last_name": "Admin",
        "role": "org_admin",
        "skill_level": "senior",
    },
    {
        "email": "manager@taskpulse.demo",
        "first_name": "Mike",
        "last_name": "Manager",
        "role": "manager",
        "skill_level": "senior",
    },
    {
        "email": "lead@taskpulse.demo",
        "first_name": "Lisa",
        "last_name": "Lead",
        "role": "team_lead",
        "skill_level": "senior",
    },
    {
        "email": "dev@taskpulse.demo",
        "first_name": "Dave",
        "last_name": "Developer",
        "role": "employee",
        "skill_level": "mid",
    },
    {
        "email": "viewer@taskpulse.demo",
        "first_name": "Vera",
        "last_name": "Viewer",
        "role": "viewer",
        "skill_level": "junior",
    },
]


async def main():
    import ssl
    from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
    from sqlalchemy import text

    print("=" * 60)
    print("TaskPulse AI - Seed Test Data")
    print("=" * 60)

    # ─── 1. Supabase client ──────────────────────────────────────────────
    sb = create_client(SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY)
    print("\n[1/6] Supabase client ready")

    # ─── 2. SQLAlchemy engine ────────────────────────────────────────────
    ssl_ctx = ssl.create_default_context()
    ssl_ctx.check_hostname = False
    ssl_ctx.verify_mode = ssl.CERT_NONE

    engine = create_async_engine(
        DATABASE_URL,
        pool_size=5,
        pool_pre_ping=True,
        connect_args={"ssl": ssl_ctx, "statement_cache_size": 0},
    )
    Session = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    print("[2/6] Database engine ready")

    # ─── 3. Create organization ──────────────────────────────────────────
    org_id = str(uuid.uuid4())
    now = datetime.now(timezone.utc)

    async with Session() as db:
        # Check if org already exists
        result = await db.execute(
            text("SELECT id FROM organizations WHERE slug = 'taskpulse-demo'")
        )
        existing = result.scalar_one_or_none()
        if existing:
            org_id = str(existing)
            print(f"[3/6] Organization already exists: {org_id}")
        else:
            await db.execute(
                text("""
                    INSERT INTO organizations (id, name, slug, description, plan, is_active, created_at, updated_at)
                    VALUES (:id, :name, :slug, :description, :plan, :is_active, :now, :now)
                """),
                {
                    "id": org_id,
                    "name": "TaskPulse Demo",
                    "slug": "taskpulse-demo",
                    "description": "Demo organization for testing TaskPulse AI",
                    "plan": "enterprise",
                    "is_active": True,
                    "now": now,
                },
            )
            await db.commit()
            print(f"[3/6] Organization created: TaskPulse Demo ({org_id})")

    # ─── 4. Create users in Supabase Auth + local DB ─────────────────────
    user_ids = {}  # email -> uuid
    auth_ids = {}  # email -> supabase_auth_id

    print("[4/6] Creating users...")
    for u in TEST_USERS:
        # Create in Supabase Auth (admin API auto-confirms email)
        try:
            auth_resp = sb.auth.admin.create_user({
                "email": u["email"],
                "password": PASSWORD,
                "email_confirm": True,
                "user_metadata": {
                    "first_name": u["first_name"],
                    "last_name": u["last_name"],
                },
            })
            auth_id = auth_resp.user.id
            auth_ids[u["email"]] = auth_id
            print(f"  Auth: {u['email']} -> {auth_id}")
        except Exception as e:
            err_str = str(e)
            if "already been registered" in err_str or "already exists" in err_str:
                # User exists — fetch their ID
                users_list = sb.auth.admin.list_users()
                for existing_user in users_list:
                    if existing_user.email == u["email"]:
                        auth_id = existing_user.id
                        auth_ids[u["email"]] = auth_id
                        print(f"  Auth: {u['email']} already exists -> {auth_id}")
                        break
            else:
                print(f"  ERROR creating auth user {u['email']}: {e}")
                continue

        # Create local DB user
        uid = str(uuid.uuid4())
        user_ids[u["email"]] = uid

        async with Session() as db:
            # Check if user already exists
            result = await db.execute(
                text("SELECT id FROM users WHERE email = :email AND org_id = :org_id"),
                {"email": u["email"], "org_id": org_id},
            )
            existing = result.scalar_one_or_none()
            if existing:
                user_ids[u["email"]] = str(existing)
                print(f"  DB:   {u['email']} already exists -> {existing}")
                continue

            await db.execute(
                text("""
                    INSERT INTO users (
                        id, org_id, email, first_name, last_name,
                        role, skill_level, is_active, is_email_verified,
                        supabase_auth_id, timezone, failed_login_attempts,
                        created_at, updated_at
                    ) VALUES (
                        :id, :org_id, :email, :first_name, :last_name,
                        :role, :skill_level, true, true,
                        :auth_id, 'UTC', 0,
                        :now, :now
                    )
                """),
                {
                    "id": uid,
                    "org_id": org_id,
                    "email": u["email"],
                    "first_name": u["first_name"],
                    "last_name": u["last_name"],
                    "role": u["role"],
                    "skill_level": u["skill_level"],
                    "auth_id": auth_ids.get(u["email"]),
                    "now": now,
                },
            )
            await db.commit()
            print(f"  DB:   {u['email']} -> {uid} (role={u['role']})")

    # Set manager relationships: dev and viewer report to lead, lead reports to manager
    async with Session() as db:
        manager_id = user_ids.get("manager@taskpulse.demo")
        lead_id = user_ids.get("lead@taskpulse.demo")
        if lead_id and manager_id:
            await db.execute(
                text("UPDATE users SET manager_id = :mgr WHERE id = :uid"),
                {"mgr": manager_id, "uid": lead_id},
            )
        dev_id = user_ids.get("dev@taskpulse.demo")
        viewer_id = user_ids.get("viewer@taskpulse.demo")
        if lead_id:
            for eid in [dev_id, viewer_id]:
                if eid:
                    await db.execute(
                        text("UPDATE users SET manager_id = :mgr WHERE id = :uid"),
                        {"mgr": lead_id, "uid": eid},
                    )
        await db.commit()
        print("  Manager relationships set")

    # ─── 5. Create tasks ─────────────────────────────────────────────────
    manager_id = user_ids.get("manager@taskpulse.demo")
    lead_id = user_ids.get("lead@taskpulse.demo")
    dev_id = user_ids.get("dev@taskpulse.demo")

    tasks = [
        {
            "title": "Design system architecture",
            "description": "Create the overall system architecture document including tech stack decisions, deployment strategy, and component diagram.",
            "status": "done",
            "priority": "critical",
            "assigned_to": lead_id,
            "created_by": manager_id,
            "estimated_hours": 16.0,
            "actual_hours": 14.0,
            "tags": '["architecture", "design"]',
            "skills_required": '["system-design", "documentation"]',
        },
        {
            "title": "Set up CI/CD pipeline",
            "description": "Configure GitHub Actions for automated testing, linting, and deployment to staging.",
            "status": "done",
            "priority": "high",
            "assigned_to": dev_id,
            "created_by": lead_id,
            "estimated_hours": 8.0,
            "actual_hours": 10.0,
            "tags": '["devops", "ci-cd"]',
            "skills_required": '["github-actions", "docker"]',
        },
        {
            "title": "Implement user authentication",
            "description": "Build login, registration, password reset, and OAuth flows using Supabase Auth.",
            "status": "done",
            "priority": "critical",
            "assigned_to": dev_id,
            "created_by": manager_id,
            "estimated_hours": 24.0,
            "actual_hours": 20.0,
            "tags": '["auth", "security"]',
            "skills_required": '["supabase", "jwt", "oauth"]',
        },
        {
            "title": "Build task management API",
            "description": "Create CRUD endpoints for tasks with filtering, pagination, subtasks, and status transitions.",
            "status": "in_progress",
            "priority": "high",
            "assigned_to": dev_id,
            "created_by": manager_id,
            "estimated_hours": 20.0,
            "actual_hours": 8.0,
            "tags": '["api", "backend"]',
            "skills_required": '["fastapi", "sqlalchemy"]',
        },
        {
            "title": "Design dashboard UI mockups",
            "description": "Create Figma mockups for the main dashboard, task board, and analytics views.",
            "status": "review",
            "priority": "high",
            "assigned_to": lead_id,
            "created_by": manager_id,
            "estimated_hours": 12.0,
            "actual_hours": 11.0,
            "tags": '["design", "ui"]',
            "skills_required": '["figma", "ui-design"]',
        },
        {
            "title": "Implement AI task decomposition",
            "description": "Build the AI engine that breaks down complex tasks into subtasks with estimates and dependencies.",
            "status": "in_progress",
            "priority": "critical",
            "assigned_to": dev_id,
            "created_by": manager_id,
            "estimated_hours": 32.0,
            "actual_hours": 5.0,
            "tags": '["ai", "core-feature"]',
            "skills_required": '["llm", "prompt-engineering"]',
        },
        {
            "title": "Set up monitoring and alerting",
            "description": "Configure application monitoring with health checks, error tracking, and performance metrics.",
            "status": "todo",
            "priority": "medium",
            "assigned_to": dev_id,
            "created_by": lead_id,
            "estimated_hours": 6.0,
            "tags": '["devops", "monitoring"]',
            "skills_required": '["observability"]',
        },
        {
            "title": "Write API documentation",
            "description": "Document all REST API endpoints with request/response examples, auth requirements, and error codes.",
            "status": "todo",
            "priority": "medium",
            "assigned_to": lead_id,
            "created_by": manager_id,
            "estimated_hours": 8.0,
            "tags": '["docs", "api"]',
            "skills_required": '["technical-writing"]',
        },
        {
            "title": "Build notification system",
            "description": "Create real-time notification delivery via WebSocket, email, and in-app channels.",
            "status": "todo",
            "priority": "medium",
            "assigned_to": None,
            "created_by": manager_id,
            "estimated_hours": 16.0,
            "tags": '["notifications", "realtime"]',
            "skills_required": '["websocket", "email"]',
        },
        {
            "title": "Performance optimization sprint",
            "description": "Profile and optimize database queries, API response times, and frontend bundle size.",
            "status": "blocked",
            "priority": "high",
            "assigned_to": dev_id,
            "created_by": lead_id,
            "estimated_hours": 12.0,
            "actual_hours": 2.0,
            "tags": '["performance", "optimization"]',
            "skills_required": '["profiling", "sql-optimization"]',
            "blocker_type": "dependency",
            "blocker_description": "Waiting for task management API to be completed before profiling queries.",
        },
        {
            "title": "Security audit and penetration testing",
            "description": "Conduct security review of auth flows, API endpoints, file uploads, and data access patterns.",
            "status": "todo",
            "priority": "critical",
            "assigned_to": None,
            "created_by": manager_id,
            "estimated_hours": 24.0,
            "tags": '["security", "audit"]',
            "skills_required": '["security", "penetration-testing"]',
        },
        {
            "title": "Mobile responsive design",
            "description": "Ensure all UI components work correctly on mobile and tablet screen sizes.",
            "status": "todo",
            "priority": "low",
            "assigned_to": lead_id,
            "created_by": manager_id,
            "estimated_hours": 10.0,
            "tags": '["ui", "mobile"]',
            "skills_required": '["css", "responsive-design"]',
        },
    ]

    task_ids = []
    print("\n[5/6] Creating tasks...")
    async with Session() as db:
        for i, t in enumerate(tasks):
            tid = str(uuid.uuid4())
            task_ids.append(tid)

            deadline = now + timedelta(days=(i + 1) * 3)
            started = now - timedelta(days=max(0, 10 - i)) if t["status"] in ("in_progress", "done", "review", "blocked") else None
            completed = now - timedelta(days=max(1, 5 - i)) if t["status"] == "done" else None

            await db.execute(
                text("""
                    INSERT INTO tasks (
                        id, org_id, title, description, status, priority,
                        assigned_to, created_by, deadline,
                        estimated_hours, actual_hours,
                        started_at, completed_at,
                        risk_score, complexity_score, confidence_score,
                        blocker_type, blocker_description,
                        tags, skills_required, tools,
                        sort_order, is_draft,
                        created_at, updated_at
                    ) VALUES (
                        :id, :org_id, :title, :description, :status, :priority,
                        :assigned_to, :created_by, :deadline,
                        :estimated_hours, :actual_hours,
                        :started_at, :completed_at,
                        :risk_score, :complexity_score, :confidence_score,
                        :blocker_type, :blocker_description,
                        CAST(:tags AS jsonb), CAST(:skills_required AS jsonb), CAST('[]' AS jsonb),
                        :sort_order, false,
                        :now, :now
                    )
                """),
                {
                    "id": tid,
                    "org_id": org_id,
                    "title": t["title"],
                    "description": t["description"],
                    "status": t["status"],
                    "priority": t["priority"],
                    "assigned_to": t["assigned_to"],
                    "created_by": t["created_by"],
                    "deadline": deadline,
                    "estimated_hours": t.get("estimated_hours"),
                    "actual_hours": t.get("actual_hours", 0.0),
                    "started_at": started,
                    "completed_at": completed,
                    "risk_score": 0.3 if t["status"] == "blocked" else 0.1,
                    "complexity_score": 0.7 if t.get("estimated_hours", 0) > 16 else 0.4,
                    "confidence_score": 0.9 if t["status"] == "done" else 0.6,
                    "blocker_type": t.get("blocker_type"),
                    "blocker_description": t.get("blocker_description"),
                    "tags": t.get("tags", "[]"),
                    "skills_required": t.get("skills_required", "[]"),
                    "sort_order": i,
                    "now": now,
                },
            )
            print(f"  Task: {t['title'][:40]:<40} [{t['status']:<12}] {t['priority']}")

        await db.commit()

    # Create 2 subtasks for "Build task management API"
    parent_task_id = task_ids[3]  # "Build task management API"
    subtask_titles = [
        ("Implement task CRUD endpoints", "in_progress"),
        ("Add task filtering and pagination", "todo"),
    ]

    async with Session() as db:
        for j, (st_title, st_status) in enumerate(subtask_titles):
            st_id = str(uuid.uuid4())
            await db.execute(
                text("""
                    INSERT INTO tasks (
                        id, org_id, title, description, status, priority,
                        assigned_to, created_by, parent_task_id,
                        estimated_hours, sort_order, is_draft,
                        tags, skills_required, tools,
                        created_at, updated_at
                    ) VALUES (
                        :id, :org_id, :title, '', :status, 'high',
                        :assigned_to, :created_by, :parent_id,
                        :hours, :sort, false,
                        CAST('[]' AS jsonb), CAST('[]' AS jsonb), CAST('[]' AS jsonb),
                        :now, :now
                    )
                """),
                {
                    "id": st_id,
                    "org_id": org_id,
                    "title": st_title,
                    "status": st_status,
                    "assigned_to": dev_id,
                    "created_by": lead_id,
                    "parent_id": parent_task_id,
                    "hours": 6.0 + j * 4,
                    "sort": j,
                    "now": now,
                },
            )
            print(f"  Subtask: {st_title}")
        await db.commit()

    # ─── 6. Create check-in config + sample check-ins ────────────────────
    print("\n[6/6] Creating check-in configs and sample data...")
    async with Session() as db:
        # Org-level check-in config
        await db.execute(
            text("""
                INSERT INTO checkin_configs (
                    id, org_id, interval_hours, enabled,
                    max_daily_checkins, work_start_hour, work_end_hour,
                    ai_suggestions_enabled, ai_sentiment_analysis,
                    created_at, updated_at
                ) VALUES (
                    :id, :org_id, 3.0, true,
                    4, 9, 18,
                    true, true,
                    :now, :now
                )
            """),
            {"id": str(uuid.uuid4()), "org_id": org_id, "now": now},
        )

        # Sample check-ins for the in-progress tasks
        checkin_data = [
            {
                "task_id": task_ids[3],  # Build task management API
                "user_id": dev_id,
                "progress": "on_track",
                "notes": "CRUD endpoints for tasks are mostly done. Working on status transitions now.",
                "completed": "Implemented create, read, update, delete endpoints. Added input validation.",
                "sentiment": 0.7,
            },
            {
                "task_id": task_ids[5],  # AI task decomposition
                "user_id": dev_id,
                "progress": "slightly_behind",
                "notes": "LLM integration is trickier than expected. Prompt engineering needs more iteration.",
                "completed": "Set up multi-provider AI client. Basic prompt template done.",
                "sentiment": 0.3,
            },
            {
                "task_id": task_ids[9],  # Performance optimization (blocked)
                "user_id": dev_id,
                "progress": "blocked",
                "notes": "Cannot profile database queries until the task API is complete.",
                "completed": "Set up profiling tools and baseline metrics.",
                "blockers": "Task management API must be completed first.",
                "sentiment": -0.2,
            },
        ]

        for ci in checkin_data:
            await db.execute(
                text("""
                    INSERT INTO checkins (
                        id, task_id, user_id, org_id,
                        cycle_number, trigger, status,
                        scheduled_at, responded_at,
                        progress_indicator, progress_notes,
                        completed_since_last, blockers_reported,
                        sentiment_score, friction_detected,
                        created_at, updated_at
                    ) VALUES (
                        :id, :task_id, :user_id, :org_id,
                        1, 'scheduled', 'responded',
                        :scheduled, :responded,
                        :progress, :notes,
                        :completed, :blockers,
                        :sentiment, :friction,
                        :now, :now
                    )
                """),
                {
                    "id": str(uuid.uuid4()),
                    "task_id": ci["task_id"],
                    "user_id": ci["user_id"],
                    "org_id": org_id,
                    "scheduled": now - timedelta(hours=4),
                    "responded": now - timedelta(hours=3),
                    "progress": ci["progress"],
                    "notes": ci["notes"],
                    "completed": ci["completed"],
                    "blockers": ci.get("blockers"),
                    "sentiment": ci["sentiment"],
                    "friction": ci["progress"] in ("blocked", "significantly_behind"),
                    "now": now,
                },
            )

        # Task comments
        comments = [
            (task_ids[0], manager_id, "Great architecture doc. Let's review in the next standup."),
            (task_ids[0], lead_id, "Updated the diagram to include the new AI microservice."),
            (task_ids[3], lead_id, "Don't forget to add soft-delete support for tasks."),
            (task_ids[3], dev_id, "Good point. I'll add an is_archived flag and filter it in queries."),
            (task_ids[5], manager_id, "This is our differentiator. Take the time to get it right."),
            (task_ids[9], dev_id, "Blocked on task API. Moving to docs in the meantime."),
        ]

        for task_id, user_id, content in comments:
            await db.execute(
                text("""
                    INSERT INTO task_comments (
                        id, task_id, user_id, content, is_ai_generated, is_edited,
                        created_at, updated_at
                    ) VALUES (
                        :id, :task_id, :user_id, :content, false, false,
                        :now, :now
                    )
                """),
                {
                    "id": str(uuid.uuid4()),
                    "task_id": task_id,
                    "user_id": user_id,
                    "content": content,
                    "now": now,
                },
            )

        # Task history entries
        history_entries = [
            (task_ids[0], lead_id, "status_change", "status", "in_progress", "done"),
            (task_ids[1], dev_id, "status_change", "status", "in_progress", "done"),
            (task_ids[2], dev_id, "status_change", "status", "in_progress", "done"),
            (task_ids[3], dev_id, "status_change", "status", "todo", "in_progress"),
            (task_ids[4], lead_id, "status_change", "status", "in_progress", "review"),
            (task_ids[9], dev_id, "status_change", "status", "todo", "blocked"),
        ]

        for task_id, user_id, action, field, old_val, new_val in history_entries:
            await db.execute(
                text("""
                    INSERT INTO task_history (
                        id, task_id, user_id, action, field_name, old_value, new_value,
                        created_at, updated_at
                    ) VALUES (
                        :id, :task_id, :user_id, :action, :field, :old_val, :new_val,
                        :now, :now
                    )
                """),
                {
                    "id": str(uuid.uuid4()),
                    "task_id": task_id,
                    "user_id": user_id,
                    "action": action,
                    "field": field,
                    "old_val": old_val,
                    "new_val": new_val,
                    "now": now,
                },
            )

        await db.commit()

    # ─── Summary ─────────────────────────────────────────────────────────
    await engine.dispose()

    print("\n" + "=" * 60)
    print("SEED COMPLETE!")
    print("=" * 60)
    print(f"\nOrganization: TaskPulse Demo ({org_id})")
    print(f"\nTest Users (password for all: {PASSWORD}):")
    print(f"  {'Email':<30} {'Role':<15} {'Name'}")
    print(f"  {'-'*30} {'-'*15} {'-'*20}")
    for u in TEST_USERS:
        print(f"  {u['email']:<30} {u['role']:<15} {u['first_name']} {u['last_name']}")
    print(f"\nTasks created: {len(tasks)} + 2 subtasks")
    print(f"Check-ins: 3 sample responses")
    print(f"Comments: {len(comments)}")
    print(f"History entries: {len(history_entries)}")
    print()


if __name__ == "__main__":
    asyncio.run(main())

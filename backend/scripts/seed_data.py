"""
TaskPulse - AI Assistant - Seed Data Script
Populates the database with demo data for testing and development
"""

import asyncio
import random
from datetime import datetime, timedelta

from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker

from app.config import settings
from app.database import Base
from app.models.user import User, UserRole
from app.models.organization import Organization
from app.models.task import Task, TaskStatus, TaskPriority, TaskComment
from app.models.checkin import CheckIn, CheckInConfig
from app.models.skill import Skill, UserSkill, SkillCategory
from app.models.workforce import WorkforceScore
from app.core.security import hash_password
from app.utils.helpers import generate_uuid


# Demo data configuration
DEMO_ORG = {
    "name": "Acme Corporation",
    "slug": "acme-corp",
    "plan_tier": "professional"
}

DEMO_USERS = [
    {"email": "admin@acme.com", "first_name": "Sarah", "last_name": "Johnson", "role": UserRole.ORG_ADMIN},
    {"email": "manager@acme.com", "first_name": "Michael", "last_name": "Chen", "role": UserRole.MANAGER},
    {"email": "lead@acme.com", "first_name": "Emily", "last_name": "Rodriguez", "role": UserRole.TEAM_LEAD},
    {"email": "dev1@acme.com", "first_name": "James", "last_name": "Wilson", "role": UserRole.EMPLOYEE},
    {"email": "dev2@acme.com", "first_name": "Lisa", "last_name": "Thompson", "role": UserRole.EMPLOYEE},
    {"email": "dev3@acme.com", "first_name": "David", "last_name": "Brown", "role": UserRole.EMPLOYEE},
    {"email": "viewer@acme.com", "first_name": "Alex", "last_name": "Garcia", "role": UserRole.VIEWER},
]

DEMO_TASKS = [
    {"title": "Implement user authentication", "priority": TaskPriority.HIGH, "estimated_hours": 16},
    {"title": "Design database schema", "priority": TaskPriority.CRITICAL, "estimated_hours": 8},
    {"title": "Create REST API endpoints", "priority": TaskPriority.HIGH, "estimated_hours": 24},
    {"title": "Build frontend dashboard", "priority": TaskPriority.MEDIUM, "estimated_hours": 32},
    {"title": "Write unit tests", "priority": TaskPriority.MEDIUM, "estimated_hours": 16},
    {"title": "Setup CI/CD pipeline", "priority": TaskPriority.LOW, "estimated_hours": 8},
    {"title": "Documentation", "priority": TaskPriority.LOW, "estimated_hours": 8},
    {"title": "Performance optimization", "priority": TaskPriority.MEDIUM, "estimated_hours": 12},
    {"title": "Security audit", "priority": TaskPriority.HIGH, "estimated_hours": 16},
    {"title": "Code review", "priority": TaskPriority.MEDIUM, "estimated_hours": 8},
]

DEMO_SKILLS = [
    {"name": "Python", "category": SkillCategory.TECHNICAL},
    {"name": "JavaScript", "category": SkillCategory.TECHNICAL},
    {"name": "TypeScript", "category": SkillCategory.TECHNICAL},
    {"name": "React", "category": SkillCategory.TECHNICAL},
    {"name": "FastAPI", "category": SkillCategory.TECHNICAL},
    {"name": "PostgreSQL", "category": SkillCategory.TECHNICAL},
    {"name": "Docker", "category": SkillCategory.TECHNICAL},
    {"name": "Git", "category": SkillCategory.PROCESS},
    {"name": "Agile", "category": SkillCategory.PROCESS},
    {"name": "Communication", "category": SkillCategory.SOFT},
    {"name": "Problem Solving", "category": SkillCategory.SOFT},
    {"name": "Teamwork", "category": SkillCategory.SOFT},
]


async def seed_database():
    """Main function to seed the database."""
    print("🌱 Starting database seed...")

    # Create engine
    engine = create_async_engine(settings.DATABASE_URL, echo=False)

    # Create tables
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    # Create session
    async_session = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    async with async_session() as session:
        # Create organization
        print("📁 Creating organization...")
        org = Organization(
            id=generate_uuid(),
            name=DEMO_ORG["name"],
            slug=DEMO_ORG["slug"],
            plan_tier=DEMO_ORG["plan_tier"],
            is_active=True
        )
        session.add(org)
        await session.flush()
        print(f"   Created: {org.name} ({org.id})")

        # Create users
        print("\n👥 Creating users...")
        users = []
        for user_data in DEMO_USERS:
            user = User(
                id=generate_uuid(),
                org_id=org.id,
                email=user_data["email"],
                password_hash=hash_password("demo123"),  # Default password for all demo users
                first_name=user_data["first_name"],
                last_name=user_data["last_name"],
                role=user_data["role"],
                is_active=True,
                email_verified=True,
                team_id="team-alpha" if user_data["role"] in [UserRole.EMPLOYEE, UserRole.TEAM_LEAD] else None
            )
            session.add(user)
            users.append(user)
            print(f"   Created: {user.first_name} {user.last_name} ({user.role.value})")

        await session.flush()

        # Set manager relationships
        manager = next(u for u in users if u.role == UserRole.MANAGER)
        for user in users:
            if user.role in [UserRole.EMPLOYEE, UserRole.TEAM_LEAD]:
                user.manager_id = manager.id

        await session.flush()

        # Create skills
        print("\n🎯 Creating skills...")
        skills = []
        for skill_data in DEMO_SKILLS:
            skill = Skill(
                id=generate_uuid(),
                org_id=org.id,
                name=skill_data["name"],
                category=skill_data["category"]
            )
            session.add(skill)
            skills.append(skill)
            print(f"   Created: {skill.name} ({skill.category.value})")

        await session.flush()

        # Assign skills to users
        print("\n🔗 Assigning skills to users...")
        employees = [u for u in users if u.role in [UserRole.EMPLOYEE, UserRole.TEAM_LEAD]]
        for user in employees:
            # Each employee gets 5-8 random skills
            user_skills = random.sample(skills, random.randint(5, 8))
            for skill in user_skills:
                user_skill = UserSkill(
                    id=generate_uuid(),
                    org_id=org.id,
                    user_id=user.id,
                    skill_id=skill.id,
                    proficiency_level=random.randint(4, 9),
                    confidence_score=random.uniform(0.6, 0.95)
                )
                session.add(user_skill)
            print(f"   Assigned {len(user_skills)} skills to {user.first_name}")

        await session.flush()

        # Create tasks
        print("\n📋 Creating tasks...")
        tasks = []
        statuses = [TaskStatus.TODO, TaskStatus.IN_PROGRESS, TaskStatus.REVIEW, TaskStatus.DONE]

        for i, task_data in enumerate(DEMO_TASKS):
            status = random.choice(statuses)
            assignee = random.choice(employees)

            # Calculate dates based on status
            created_at = datetime.utcnow() - timedelta(days=random.randint(1, 30))
            started_at = None
            completed_at = None

            if status in [TaskStatus.IN_PROGRESS, TaskStatus.REVIEW, TaskStatus.DONE]:
                started_at = created_at + timedelta(hours=random.randint(1, 24))
            if status == TaskStatus.DONE:
                completed_at = started_at + timedelta(hours=task_data["estimated_hours"] * random.uniform(0.8, 1.3))

            task = Task(
                id=generate_uuid(),
                org_id=org.id,
                title=task_data["title"],
                description=f"Detailed description for: {task_data['title']}",
                status=status,
                priority=task_data["priority"],
                estimated_hours=task_data["estimated_hours"],
                actual_hours=task_data["estimated_hours"] * random.uniform(0.7, 1.2) if status == TaskStatus.DONE else 0,
                created_by=manager.id,
                assigned_to=assignee.id,
                team_id="team-alpha",
                deadline=datetime.utcnow() + timedelta(days=random.randint(3, 14)),
                started_at=started_at,
                completed_at=completed_at,
                risk_score=random.uniform(0.1, 0.5),
                complexity_score=random.uniform(0.3, 0.8)
            )
            task.created_at = created_at
            session.add(task)
            tasks.append(task)
            print(f"   Created: {task.title} ({status.value})")

        await session.flush()

        # Create subtasks for some tasks
        print("\n📝 Creating subtasks...")
        for task in tasks[:3]:  # First 3 tasks get subtasks
            for j in range(random.randint(2, 4)):
                subtask = Task(
                    id=generate_uuid(),
                    org_id=org.id,
                    title=f"Subtask {j+1} for {task.title[:20]}...",
                    status=random.choice([TaskStatus.TODO, TaskStatus.DONE]),
                    priority=TaskPriority.MEDIUM,
                    estimated_hours=random.randint(2, 6),
                    created_by=manager.id,
                    parent_task_id=task.id,
                    sort_order=j
                )
                session.add(subtask)
            print(f"   Created subtasks for: {task.title[:30]}...")

        await session.flush()

        # Create check-ins
        print("\n✅ Creating check-ins...")
        in_progress_tasks = [t for t in tasks if t.status == TaskStatus.IN_PROGRESS]
        for task in in_progress_tasks:
            for cycle in range(1, random.randint(2, 4)):
                checkin = CheckIn(
                    id=generate_uuid(),
                    org_id=org.id,
                    task_id=task.id,
                    user_id=task.assigned_to,
                    cycle_number=cycle,
                    scheduled_at=datetime.utcnow() - timedelta(hours=3 * cycle),
                    response_status="responded" if random.random() > 0.2 else "pending",
                    progress_percentage=min(100, cycle * 25 + random.randint(-10, 10)),
                    has_blocker=random.random() > 0.8
                )
                session.add(checkin)
            print(f"   Created check-ins for: {task.title[:30]}...")

        await session.flush()

        # Create check-in config
        print("\n⚙️ Creating check-in configuration...")
        config = CheckInConfig(
            id=generate_uuid(),
            org_id=org.id,
            default_interval_hours=3,
            auto_escalate_after_missed=2,
            silent_when_on_track=True
        )
        session.add(config)

        # Create workforce scores
        print("\n📊 Creating workforce scores...")
        for user in employees:
            score = WorkforceScore(
                id=generate_uuid(),
                org_id=org.id,
                user_id=user.id,
                overall_score=random.uniform(65, 95),
                velocity_score=random.uniform(60, 95),
                quality_score=random.uniform(70, 95),
                self_sufficiency_score=random.uniform(55, 90),
                learning_score=random.uniform(60, 90),
                collaboration_score=random.uniform(65, 95),
                percentile_rank=random.uniform(40, 90),
                attrition_risk_score=random.uniform(0.05, 0.35),
                burnout_risk_score=random.uniform(0.1, 0.4),
                score_trend=random.choice(["improving", "stable", "declining"])
            )
            session.add(score)
            print(f"   Created score for: {user.first_name} ({score.overall_score:.1f})")

        # Create task comments
        print("\n💬 Creating task comments...")
        for task in tasks[:5]:
            for _ in range(random.randint(1, 3)):
                commenter = random.choice(users)
                comment = TaskComment(
                    id=generate_uuid(),
                    task_id=task.id,
                    user_id=commenter.id,
                    content=random.choice([
                        "Looking good! Keep up the great work.",
                        "Could you add more details here?",
                        "I've reviewed this and it looks fine.",
                        "There might be an issue with this approach.",
                        "Great progress on this task!",
                        "Let's discuss this in our next standup."
                    ])
                )
                session.add(comment)

        await session.commit()

        print("\n" + "=" * 50)
        print("✨ Database seeding completed successfully!")
        print("=" * 50)
        print("\n📋 Summary:")
        print(f"   - Organization: {org.name}")
        print(f"   - Users: {len(users)}")
        print(f"   - Skills: {len(skills)}")
        print(f"   - Tasks: {len(tasks)}")
        print("\n🔑 Login Credentials:")
        print("   All demo users use password: demo123")
        print("\n   Admin:   admin@acme.com")
        print("   Manager: manager@acme.com")
        print("   Lead:    lead@acme.com")
        print("   Dev:     dev1@acme.com, dev2@acme.com, dev3@acme.com")
        print("   Viewer:  viewer@acme.com")
        print("=" * 50)

    await engine.dispose()


async def clear_database():
    """Clear all data from the database."""
    print("🗑️ Clearing database...")

    engine = create_async_engine(settings.DATABASE_URL, echo=False)

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)

    await engine.dispose()
    print("✅ Database cleared!")


if __name__ == "__main__":
    import sys

    if len(sys.argv) > 1 and sys.argv[1] == "--clear":
        asyncio.run(clear_database())
    else:
        asyncio.run(seed_database())

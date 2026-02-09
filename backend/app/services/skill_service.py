"""
TaskPulse - AI Assistant - Skill Service
Business logic for employee skill tracking
"""

from typing import Optional, List, Tuple
from datetime import datetime, timedelta
from sqlalchemy import select, func, and_, or_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.skill import (
    Skill, UserSkill, SkillGap, SkillMetrics, LearningPath,
    SkillCategory, SkillTrend, GapType
)
from app.models.user import User
from app.models.task import Task, TaskStatus
from app.schemas.skill import (
    SkillCreate, SkillUpdate, UserSkillCreate, UserSkillUpdate,
    LearningPathCreate
)
from app.utils.helpers import generate_uuid
from app.core.exceptions import NotFoundException, AlreadyExistsException
from app.services.ai_service import get_ai_service


class SkillService:
    """Service for skill management."""

    def __init__(self, db: AsyncSession):
        self.db = db
        self.ai_service = get_ai_service()

    # ==================== Skill Catalog ====================

    async def create_skill(
        self,
        org_id: str,
        skill_data: SkillCreate
    ) -> Skill:
        """Create a new skill in the catalog."""
        # Check for duplicate
        existing = await self.db.execute(
            select(Skill).where(
                and_(Skill.org_id == org_id, Skill.name == skill_data.name)
            )
        )
        if existing.scalar_one_or_none():
            raise AlreadyExistsException("Skill", "name", skill_data.name)

        skill = Skill(
            id=generate_uuid(),
            org_id=org_id,
            name=skill_data.name,
            description=skill_data.description,
            category=skill_data.category
        )
        skill.aliases = skill_data.aliases
        skill.related_skills = skill_data.related_skills

        self.db.add(skill)
        await self.db.flush()
        await self.db.refresh(skill)
        return skill

    async def get_skill(self, skill_id: str, org_id: str) -> Optional[Skill]:
        """Get a skill by ID."""
        result = await self.db.execute(
            select(Skill).where(
                and_(Skill.id == skill_id, Skill.org_id == org_id)
            )
        )
        return result.scalar_one_or_none()

    async def get_skills(
        self,
        org_id: str,
        category: Optional[SkillCategory] = None,
        search: Optional[str] = None,
        skip: int = 0,
        limit: int = 100
    ) -> Tuple[List[Skill], int]:
        """Get skills with filters."""
        query = select(Skill).where(
            and_(Skill.org_id == org_id, Skill.is_active == True)
        )

        if category:
            query = query.where(Skill.category == category)
        if search:
            query = query.where(
                or_(
                    Skill.name.ilike(f"%{search}%"),
                    Skill.description.ilike(f"%{search}%")
                )
            )

        count_query = select(func.count()).select_from(query.subquery())
        total = (await self.db.execute(count_query)).scalar() or 0

        query = query.offset(skip).limit(limit)
        query = query.order_by(Skill.name)

        result = await self.db.execute(query)
        return list(result.scalars().all()), total

    async def update_skill(
        self,
        skill_id: str,
        org_id: str,
        skill_data: SkillUpdate
    ) -> Skill:
        """Update a skill."""
        skill = await self.get_skill(skill_id, org_id)
        if not skill:
            raise NotFoundException("Skill", skill_id)

        update_dict = skill_data.model_dump(exclude_unset=True)
        for field, value in update_dict.items():
            if field in ('aliases', 'related_skills'):
                setattr(skill, field, value)
            else:
                setattr(skill, field, value)

        await self.db.flush()
        await self.db.refresh(skill)
        return skill

    # ==================== User Skills ====================

    async def add_user_skill(
        self,
        user_id: str,
        org_id: str,
        skill_data: UserSkillCreate
    ) -> UserSkill:
        """Add a skill to a user's profile."""
        # Verify skill exists
        skill = await self.get_skill(skill_data.skill_id, org_id)
        if not skill:
            raise NotFoundException("Skill", skill_data.skill_id)

        # Check if already exists
        existing = await self.db.execute(
            select(UserSkill).where(
                and_(
                    UserSkill.user_id == user_id,
                    UserSkill.skill_id == skill_data.skill_id
                )
            )
        )
        if existing.scalar_one_or_none():
            raise AlreadyExistsException("UserSkill", "skill", skill_data.skill_id)

        user_skill = UserSkill(
            id=generate_uuid(),
            user_id=user_id,
            skill_id=skill_data.skill_id,
            org_id=org_id,
            level=skill_data.level,
            confidence=skill_data.confidence,
            source=skill_data.source,
            notes=skill_data.notes,
            last_demonstrated=datetime.utcnow()
        )

        self.db.add(user_skill)
        await self.db.flush()
        await self.db.refresh(user_skill)
        return user_skill

    async def get_user_skills(
        self,
        user_id: str,
        org_id: str
    ) -> List[UserSkill]:
        """Get all skills for a user."""
        result = await self.db.execute(
            select(UserSkill).where(
                and_(UserSkill.user_id == user_id, UserSkill.org_id == org_id)
            ).options(selectinload(UserSkill.skill))
            .order_by(UserSkill.level.desc())
        )
        return list(result.scalars().all())

    async def update_user_skill(
        self,
        user_skill_id: str,
        org_id: str,
        skill_data: UserSkillUpdate
    ) -> UserSkill:
        """Update a user's skill."""
        result = await self.db.execute(
            select(UserSkill).where(
                and_(UserSkill.id == user_skill_id, UserSkill.org_id == org_id)
            )
        )
        user_skill = result.scalar_one_or_none()
        if not user_skill:
            raise NotFoundException("UserSkill", user_skill_id)

        update_dict = skill_data.model_dump(exclude_unset=True)

        if 'level' in update_dict:
            old_level = user_skill.level
            new_level = update_dict['level']
            user_skill.add_level_snapshot(new_level)

            # Update trend
            if new_level > old_level:
                user_skill.trend = SkillTrend.IMPROVING
            elif new_level < old_level:
                user_skill.trend = SkillTrend.DECLINING
            else:
                user_skill.trend = SkillTrend.STABLE
            del update_dict['level']

        for field, value in update_dict.items():
            setattr(user_skill, field, value)

        await self.db.flush()
        await self.db.refresh(user_skill)
        return user_skill

    # ==================== Skill Graph ====================

    async def get_skill_graph(
        self,
        user_id: str,
        org_id: str
    ) -> dict:
        """Get user's skill graph for visualization."""
        user_skills = await self.get_user_skills(user_id, org_id)

        nodes = []
        edges = []
        category_levels = {}

        for us in user_skills:
            skill = us.skill
            if skill:
                nodes.append({
                    "skill_id": skill.id,
                    "skill_name": skill.name,
                    "category": skill.category,
                    "level": us.level,
                    "trend": us.trend,
                    "confidence": us.confidence
                })

                # Track category levels
                cat = skill.category.value
                if cat not in category_levels:
                    category_levels[cat] = []
                category_levels[cat].append(us.level)

                # Add edges for related skills
                for related_id in skill.related_skills:
                    edges.append({
                        "from_skill": skill.id,
                        "to_skill": related_id,
                        "relationship": "related"
                    })

        # Calculate strongest category
        strongest = None
        highest_avg = 0
        for cat, levels in category_levels.items():
            avg = sum(levels) / len(levels) if levels else 0
            if avg > highest_avg:
                highest_avg = avg
                strongest = cat

        avg_level = sum(n["level"] for n in nodes) / len(nodes) if nodes else 0

        return {
            "user_id": user_id,
            "nodes": nodes,
            "edges": edges,
            "total_skills": len(nodes),
            "average_level": round(avg_level, 2),
            "strongest_category": strongest
        }

    # ==================== Skill Velocity ====================

    async def get_skill_velocity(
        self,
        user_id: str,
        org_id: str,
        days: int = 30
    ) -> dict:
        """Calculate skill velocity metrics."""
        since = datetime.utcnow() - timedelta(days=days)

        # Get completed tasks
        tasks_result = await self.db.execute(
            select(Task).where(
                and_(
                    Task.assigned_to == user_id,
                    Task.org_id == org_id,
                    Task.status == TaskStatus.DONE,
                    Task.completed_at >= since
                )
            )
        )
        completed_tasks = tasks_result.scalars().all()

        # Calculate velocity
        weeks = max(days / 7, 1)
        task_velocity = len(completed_tasks) / weeks

        # Get skill improvements
        user_skills = await self.get_user_skills(user_id, org_id)
        improving_count = sum(1 for us in user_skills if us.trend == SkillTrend.IMPROVING)

        # Get recent skill demonstrations
        demonstrated = sum(1 for us in user_skills
                         if us.last_demonstrated and us.last_demonstrated >= since)

        # Mock quality score (would calculate from task reviews in production)
        quality_score = 0.85

        # Mock self-sufficiency (would calculate from help requests)
        self_sufficiency = 0.75

        # Learning velocity (improvement rate)
        learning_velocity = improving_count / len(user_skills) if user_skills else 0

        return {
            "user_id": user_id,
            "period_days": days,
            "task_completion_velocity": round(task_velocity, 2),
            "quality_score": quality_score,
            "self_sufficiency_index": self_sufficiency,
            "learning_velocity": round(learning_velocity, 2),
            "skills_improved": improving_count,
            "skills_demonstrated": demonstrated,
            "velocity_percentile": None,  # Would calculate in production
            "quality_percentile": None
        }

    # ==================== Team Composition ====================

    async def get_team_composition(
        self,
        team_id: str,
        org_id: str
    ) -> dict:
        """Get team's skill composition."""
        # Get team members
        members_result = await self.db.execute(
            select(User).where(
                and_(User.team_id == team_id, User.org_id == org_id, User.is_active == True)
            )
        )
        members = members_result.scalars().all()
        member_ids = [m.id for m in members]

        if not member_ids:
            return {
                "team_id": team_id,
                "total_members": 0,
                "skills": [],
                "strongest_skills": [],
                "weakest_skills": [],
                "skill_coverage": 0
            }

        # Get all skills for team members
        skills_result = await self.db.execute(
            select(UserSkill).where(
                UserSkill.user_id.in_(member_ids)
            ).options(selectinload(UserSkill.skill))
        )
        user_skills = skills_result.scalars().all()

        # Aggregate by skill
        skill_data = {}
        for us in user_skills:
            if us.skill:
                sid = us.skill_id
                if sid not in skill_data:
                    skill_data[sid] = {
                        "skill_id": sid,
                        "skill_name": us.skill.name,
                        "category": us.skill.category,
                        "levels": [],
                        "member_count": 0
                    }
                skill_data[sid]["levels"].append(us.level)
                skill_data[sid]["member_count"] += 1

        # Calculate summaries
        skills_summary = []
        for data in skill_data.values():
            levels = data["levels"]
            avg = sum(levels) / len(levels) if levels else 0
            coverage = len(levels) / len(member_ids)
            experts = sum(1 for l in levels if l >= 7)
            novices = sum(1 for l in levels if l <= 3)

            skills_summary.append({
                "skill_id": data["skill_id"],
                "skill_name": data["skill_name"],
                "category": data["category"],
                "team_average_level": round(avg, 2),
                "coverage": round(coverage, 2),
                "experts": experts,
                "novices": novices
            })

        # Sort by average level
        skills_summary.sort(key=lambda x: x["team_average_level"], reverse=True)

        strongest = [s["skill_name"] for s in skills_summary[:3]]
        weakest = [s["skill_name"] for s in skills_summary[-3:] if skills_summary]

        total_coverage = sum(s["coverage"] for s in skills_summary) / len(skills_summary) if skills_summary else 0

        return {
            "team_id": team_id,
            "total_members": len(members),
            "skills": skills_summary,
            "strongest_skills": strongest,
            "weakest_skills": weakest,
            "skill_coverage": round(total_coverage, 2)
        }

    # ==================== Skill Gaps ====================

    async def identify_skill_gaps(
        self,
        user_id: str,
        org_id: str,
        target_role: Optional[str] = None
    ) -> List[SkillGap]:
        """Identify skill gaps for a user."""
        # Get user's current skills
        user_skills = await self.get_user_skills(user_id, org_id)
        user_skill_map = {us.skill_id: us.level for us in user_skills}

        # Get org's skill catalog
        all_skills, _ = await self.get_skills(org_id, limit=500)

        gaps = []
        for skill in all_skills:
            current_level = user_skill_map.get(skill.id, 0)
            required_level = skill.org_average_level or 5.0

            if current_level < required_level:
                gap_size = required_level - current_level

                # Determine gap type
                if gap_size >= 4:
                    gap_type = GapType.CRITICAL
                    priority = 9
                elif gap_size >= 2:
                    gap_type = GapType.GROWTH
                    priority = 6
                else:
                    gap_type = GapType.STRETCH
                    priority = 3

                gap = SkillGap(
                    id=generate_uuid(),
                    user_id=user_id,
                    skill_id=skill.id,
                    org_id=org_id,
                    gap_type=gap_type,
                    current_level=current_level if current_level > 0 else None,
                    required_level=required_level,
                    gap_size=round(gap_size, 1),
                    for_role=target_role,
                    priority=priority
                )
                gap.learning_resources = []  # Would populate with actual resources
                gaps.append(gap)
                self.db.add(gap)

        await self.db.flush()
        return gaps

    async def get_user_skill_gaps(
        self,
        user_id: str,
        org_id: str
    ) -> List[SkillGap]:
        """Get existing skill gaps for user."""
        result = await self.db.execute(
            select(SkillGap).where(
                and_(
                    SkillGap.user_id == user_id,
                    SkillGap.org_id == org_id,
                    SkillGap.is_resolved == False
                )
            ).options(selectinload(SkillGap.skill))
            .order_by(SkillGap.priority.desc())
        )
        return list(result.scalars().all())

    # ==================== Learning Path ====================

    async def create_learning_path(
        self,
        user_id: str,
        org_id: str,
        path_data: LearningPathCreate
    ) -> LearningPath:
        """Create a learning path."""
        path = LearningPath(
            id=generate_uuid(),
            user_id=user_id,
            org_id=org_id,
            title=path_data.title,
            description=path_data.description,
            target_role=path_data.target_role,
            target_completion=path_data.target_completion
        )
        path.skills = path_data.skills
        path.milestones = []

        self.db.add(path)
        await self.db.flush()
        await self.db.refresh(path)
        return path

    async def get_learning_paths(
        self,
        user_id: str,
        org_id: str,
        active_only: bool = True
    ) -> List[LearningPath]:
        """Get user's learning paths."""
        query = select(LearningPath).where(
            and_(LearningPath.user_id == user_id, LearningPath.org_id == org_id)
        )
        if active_only:
            query = query.where(LearningPath.is_active == True)

        result = await self.db.execute(query.order_by(LearningPath.created_at.desc()))
        return list(result.scalars().all())

    # ==================== Self-Sufficiency ====================

    async def get_self_sufficiency(
        self,
        user_id: str,
        org_id: str
    ) -> dict:
        """Calculate self-sufficiency metrics."""
        # Mock implementation - would calculate from check-ins and help requests
        return {
            "user_id": user_id,
            "overall_score": 0.75,
            "by_skill_category": {
                "technical": 0.8,
                "process": 0.7,
                "soft": 0.75
            },
            "blockers_self_resolved": 15,
            "blockers_total": 20,
            "help_requests_trend": "decreasing",
            "improvement_areas": ["API Design", "Testing"]
        }

    # ==================== Skill Inference ====================

    async def infer_skills_from_task(
        self,
        task_id: str,
        user_id: str,
        org_id: str
    ) -> List[str]:
        """Infer skills demonstrated from completed task."""
        task_result = await self.db.execute(
            select(Task).where(Task.id == task_id)
        )
        task = task_result.scalar_one_or_none()

        if not task or task.status != TaskStatus.DONE:
            return []

        # Use AI to infer skills
        inferred = await self.ai_service.infer_skills(
            task.title, task.description or ""
        )

        demonstrated_skills = []
        for skill_info in inferred:
            # Find or create skill
            skill_name = skill_info.get("skill", "")
            result = await self.db.execute(
                select(Skill).where(
                    and_(
                        Skill.org_id == org_id,
                        Skill.name.ilike(f"%{skill_name}%")
                    )
                )
            )
            skill = result.scalar_one_or_none()

            if skill:
                # Update user skill
                user_skill_result = await self.db.execute(
                    select(UserSkill).where(
                        and_(
                            UserSkill.user_id == user_id,
                            UserSkill.skill_id == skill.id
                        )
                    )
                )
                user_skill = user_skill_result.scalar_one_or_none()

                if user_skill:
                    user_skill.demonstration_count += 1
                    user_skill.last_demonstrated = datetime.utcnow()
                    demonstrated_skills.append(skill.id)

        await self.db.flush()
        return demonstrated_skills

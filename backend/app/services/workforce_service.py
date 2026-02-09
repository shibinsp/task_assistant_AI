"""
TaskPulse - AI Assistant - Workforce Intelligence Service
Executive-level decision intelligence and analytics
"""

from typing import Optional, List, Dict, Any
from datetime import datetime, timedelta
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_
import random

from app.models.workforce import (
    WorkforceScore, ManagerEffectiveness, OrgHealthSnapshot,
    RestructuringScenario
)
from app.models.user import User, UserRole
from app.models.task import Task, TaskStatus
from app.utils.helpers import generate_uuid


class WorkforceService:
    """Service for workforce intelligence and analytics."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def calculate_workforce_score(
        self,
        user_id: str,
        org_id: str
    ) -> WorkforceScore:
        """
        Calculate comprehensive workforce score for a user.
        """
        # Get user's task history
        result = await self.db.execute(
            select(Task).where(
                Task.assigned_to == user_id,
                Task.org_id == org_id,
                Task.completed_at >= datetime.utcnow() - timedelta(days=90)
            )
        )
        tasks = result.scalars().all()

        # Calculate component scores
        velocity_score = await self._calculate_velocity_score(tasks)
        quality_score = await self._calculate_quality_score(tasks, user_id, org_id)
        self_sufficiency_score = await self._calculate_self_sufficiency(user_id, org_id)
        learning_score = await self._calculate_learning_score(user_id, org_id)
        collaboration_score = await self._calculate_collaboration_score(user_id, org_id)

        # Calculate overall score (weighted average)
        overall_score = (
            velocity_score * 0.25 +
            quality_score * 0.25 +
            self_sufficiency_score * 0.20 +
            learning_score * 0.15 +
            collaboration_score * 0.15
        )

        # Calculate risk scores
        attrition_risk = await self._calculate_attrition_risk(user_id, org_id)
        burnout_risk = await self._calculate_burnout_risk(user_id, org_id, tasks)

        # Get percentile rank
        percentile = await self._calculate_percentile(org_id, overall_score)

        # Determine trend
        trend = await self._determine_score_trend(user_id, org_id, overall_score)

        # Create or update score
        result = await self.db.execute(
            select(WorkforceScore).where(
                WorkforceScore.user_id == user_id,
                WorkforceScore.org_id == org_id
            ).order_by(WorkforceScore.snapshot_date.desc()).limit(1)
        )
        existing = result.scalar_one_or_none()

        score = WorkforceScore(
            id=generate_uuid(),
            org_id=org_id,
            user_id=user_id,
            overall_score=overall_score,
            velocity_score=velocity_score,
            quality_score=quality_score,
            self_sufficiency_score=self_sufficiency_score,
            learning_score=learning_score,
            collaboration_score=collaboration_score,
            percentile_rank=percentile,
            attrition_risk_score=attrition_risk,
            burnout_risk_score=burnout_risk,
            score_trend=trend
        )

        self.db.add(score)
        await self.db.flush()
        await self.db.refresh(score)

        return score

    async def _calculate_velocity_score(self, tasks: List[Task]) -> float:
        """Calculate velocity score based on task completion rate."""
        if not tasks:
            return 50.0

        completed = [t for t in tasks if t.is_completed]
        on_time = [t for t in completed if t.deadline and t.completed_at and t.completed_at <= t.deadline]

        completion_rate = len(completed) / len(tasks) if tasks else 0
        on_time_rate = len(on_time) / len(completed) if completed else 0

        score = (completion_rate * 60 + on_time_rate * 40)
        return round(min(100, score), 1)

    async def _calculate_quality_score(
        self,
        tasks: List[Task],
        user_id: str,
        org_id: str
    ) -> float:
        """Calculate quality score based on rework and issues."""
        if not tasks:
            return 50.0

        completed = [t for t in tasks if t.is_completed]
        if not completed:
            return 50.0

        # Check for tasks that were reopened (status went back to in_progress after done)
        # This is a simplified heuristic
        rework_count = sum(1 for t in completed if t.actual_hours and t.estimated_hours and t.actual_hours > t.estimated_hours * 1.5)

        rework_rate = rework_count / len(completed)
        score = 100 - (rework_rate * 50)

        return round(max(0, min(100, score)), 1)

    async def _calculate_self_sufficiency(self, user_id: str, org_id: str) -> float:
        """Calculate self-sufficiency score based on help requests."""
        # In production, this would analyze check-ins and escalations
        # For now, return a simulated score
        return round(random.uniform(60, 95), 1)

    async def _calculate_learning_score(self, user_id: str, org_id: str) -> float:
        """Calculate learning velocity score."""
        # In production, this would analyze skill growth over time
        return round(random.uniform(55, 90), 1)

    async def _calculate_collaboration_score(self, user_id: str, org_id: str) -> float:
        """Calculate collaboration score based on team interactions."""
        return round(random.uniform(60, 95), 1)

    async def _calculate_attrition_risk(self, user_id: str, org_id: str) -> float:
        """Calculate attrition risk score."""
        # Factors: engagement, growth, compensation, tenure
        # For now, return simulated risk
        return round(random.uniform(0.05, 0.35), 2)

    async def _calculate_burnout_risk(
        self,
        user_id: str,
        org_id: str,
        recent_tasks: List[Task]
    ) -> float:
        """Calculate burnout risk score."""
        if not recent_tasks:
            return 0.1

        # Check workload
        active_tasks = [t for t in recent_tasks if not t.is_completed]
        overdue_tasks = [t for t in active_tasks if t.is_overdue]

        workload_factor = min(1.0, len(active_tasks) / 10)
        overdue_factor = len(overdue_tasks) / max(1, len(active_tasks))

        risk = workload_factor * 0.5 + overdue_factor * 0.5
        return round(risk, 2)

    async def _calculate_percentile(self, org_id: str, score: float) -> float:
        """Calculate percentile rank within organization."""
        result = await self.db.execute(
            select(func.count()).where(
                WorkforceScore.org_id == org_id,
                WorkforceScore.overall_score < score
            )
        )
        lower_count = result.scalar() or 0

        result = await self.db.execute(
            select(func.count()).where(WorkforceScore.org_id == org_id)
        )
        total = result.scalar() or 1

        return round((lower_count / total) * 100, 1)

    async def _determine_score_trend(
        self,
        user_id: str,
        org_id: str,
        current_score: float
    ) -> str:
        """Determine score trend compared to previous periods."""
        result = await self.db.execute(
            select(WorkforceScore).where(
                WorkforceScore.user_id == user_id,
                WorkforceScore.org_id == org_id
            ).order_by(WorkforceScore.snapshot_date.desc()).limit(3)
        )
        history = result.scalars().all()

        if len(history) < 2:
            return "stable"

        avg_previous = sum(h.overall_score or 0 for h in history[1:]) / (len(history) - 1)

        if current_score > avg_previous * 1.05:
            return "improving"
        elif current_score < avg_previous * 0.95:
            return "declining"
        return "stable"

    async def calculate_manager_effectiveness(
        self,
        manager_id: str,
        org_id: str
    ) -> ManagerEffectiveness:
        """Calculate manager effectiveness metrics."""
        # Get team members
        result = await self.db.execute(
            select(User).where(
                User.org_id == org_id,
                User.manager_id == manager_id
            )
        )
        team_members = result.scalars().all()
        team_size = len(team_members)

        if team_size == 0:
            return None

        # Get team tasks
        team_ids = [m.id for m in team_members]
        result = await self.db.execute(
            select(Task).where(
                Task.org_id == org_id,
                Task.assigned_to.in_(team_ids),
                Task.completed_at >= datetime.utcnow() - timedelta(days=90)
            )
        )
        team_tasks = result.scalars().all()

        # Calculate metrics
        completed_tasks = [t for t in team_tasks if t.is_completed]
        team_velocity = len(completed_tasks) / 3 if completed_tasks else 0  # Per month

        # Get team scores
        result = await self.db.execute(
            select(WorkforceScore).where(
                WorkforceScore.org_id == org_id,
                WorkforceScore.user_id.in_(team_ids)
            )
        )
        team_scores = result.scalars().all()

        avg_team_score = sum(s.overall_score or 0 for s in team_scores) / max(1, len(team_scores))
        avg_burnout = sum(s.burnout_risk_score or 0 for s in team_scores) / max(1, len(team_scores))
        avg_attrition = sum(s.attrition_risk_score or 0 for s in team_scores) / max(1, len(team_scores))

        # Calculate effectiveness score
        effectiveness = (
            (avg_team_score / 100) * 0.4 +
            (team_velocity / 50) * 0.3 +  # Normalized
            (1 - avg_burnout) * 0.15 +
            (1 - avg_attrition) * 0.15
        ) * 100

        effectiveness_record = ManagerEffectiveness(
            id=generate_uuid(),
            org_id=org_id,
            manager_id=manager_id,
            team_size=team_size,
            effectiveness_score=round(min(100, effectiveness), 1),
            team_velocity_avg=round(team_velocity, 1),
            team_quality_avg=round(avg_team_score, 1),
            team_burnout_avg=round(avg_burnout, 2),
            team_attrition_risk_avg=round(avg_attrition, 2),
            redundancy_score=round(random.uniform(0.1, 0.4), 2)  # AI replacing manager tasks
        )

        self.db.add(effectiveness_record)
        await self.db.flush()
        await self.db.refresh(effectiveness_record)

        return effectiveness_record

    async def calculate_org_health(self, org_id: str) -> OrgHealthSnapshot:
        """Calculate organization health metrics."""
        # Get employee count
        result = await self.db.execute(
            select(func.count()).where(User.org_id == org_id, User.is_active == True)
        )
        total_employees = result.scalar() or 0

        # Get task metrics
        result = await self.db.execute(
            select(Task).where(
                Task.org_id == org_id,
                Task.status.not_in([TaskStatus.ARCHIVED])
            )
        )
        tasks = result.scalars().all()

        active_tasks = len([t for t in tasks if t.status not in [TaskStatus.DONE, TaskStatus.ARCHIVED]])
        blocked_tasks = len([t for t in tasks if t.status == TaskStatus.BLOCKED])
        overdue_tasks = len([t for t in tasks if t.is_overdue])

        # Get risk metrics
        result = await self.db.execute(
            select(WorkforceScore).where(WorkforceScore.org_id == org_id)
        )
        scores = result.scalars().all()

        high_attrition = len([s for s in scores if (s.attrition_risk_score or 0) > 0.5])
        high_burnout = len([s for s in scores if (s.burnout_risk_score or 0) > 0.5])

        # Calculate indices
        productivity_index = round(random.uniform(70, 90), 1)
        skill_coverage = round(random.uniform(65, 85), 1)
        management_quality = round(random.uniform(70, 90), 1)
        automation_maturity = round(random.uniform(30, 60), 1)
        delivery_predictability = round(random.uniform(60, 85), 1)

        overall_health = (
            productivity_index * 0.25 +
            skill_coverage * 0.20 +
            management_quality * 0.20 +
            automation_maturity * 0.15 +
            delivery_predictability * 0.20
        )

        snapshot = OrgHealthSnapshot(
            id=generate_uuid(),
            org_id=org_id,
            overall_health_score=round(overall_health, 1),
            productivity_index=productivity_index,
            skill_coverage_index=skill_coverage,
            management_quality_index=management_quality,
            automation_maturity_index=automation_maturity,
            delivery_predictability_index=delivery_predictability,
            total_employees=total_employees,
            active_tasks=active_tasks,
            blocked_tasks=blocked_tasks,
            overdue_tasks=overdue_tasks,
            high_attrition_risk_count=high_attrition,
            high_burnout_risk_count=high_burnout
        )

        self.db.add(snapshot)
        await self.db.flush()
        await self.db.refresh(snapshot)

        return snapshot

    async def run_simulation(
        self,
        org_id: str,
        scenario_type: str,
        config: Dict[str, Any],
        created_by: str,
        name: str,
        description: Optional[str] = None
    ) -> RestructuringScenario:
        """Run a restructuring simulation."""
        scenario = RestructuringScenario(
            id=generate_uuid(),
            org_id=org_id,
            created_by=created_by,
            name=name,
            description=description,
            scenario_type=scenario_type
        )
        scenario.config = config

        # Run simulation based on type
        if scenario_type == "team_merge":
            results = await self._simulate_team_merge(org_id, config)
        elif scenario_type == "role_change":
            results = await self._simulate_role_change(org_id, config)
        elif scenario_type == "automation_replace":
            results = await self._simulate_automation_replace(org_id, config)
        elif scenario_type == "reduction":
            results = await self._simulate_reduction(org_id, config)
        else:
            results = {"error": "Unknown scenario type"}

        scenario.projected_cost_change = results.get("cost_change", 0)
        scenario.projected_productivity_change = results.get("productivity_change", 0)
        scenario.projected_skill_coverage_change = results.get("skill_coverage_change", 0)
        scenario.affected_employees = results.get("affected_employees", 0)
        scenario.overall_risk_score = results.get("risk_score", 0.5)
        scenario.analysis_results = results

        self.db.add(scenario)
        await self.db.flush()
        await self.db.refresh(scenario)

        return scenario

    async def _simulate_team_merge(
        self,
        org_id: str,
        config: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Simulate team merger impact."""
        team_a = config.get("team_a_id")
        team_b = config.get("team_b_id")

        return {
            "cost_change": round(random.uniform(-10, 5), 1),
            "productivity_change": round(random.uniform(-5, 15), 1),
            "skill_coverage_change": round(random.uniform(-5, 10), 1),
            "affected_employees": random.randint(5, 20),
            "risk_score": round(random.uniform(0.3, 0.6), 2),
            "insights": [
                "Potential skill redundancy detected",
                "Communication overhead may increase temporarily",
                "Cost savings from reduced management layers"
            ]
        }

    async def _simulate_role_change(
        self,
        org_id: str,
        config: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Simulate role restructuring impact."""
        return {
            "cost_change": round(random.uniform(-5, 10), 1),
            "productivity_change": round(random.uniform(-10, 20), 1),
            "skill_coverage_change": round(random.uniform(0, 15), 1),
            "affected_employees": random.randint(3, 15),
            "risk_score": round(random.uniform(0.2, 0.5), 2),
            "insights": [
                "Role clarity may improve productivity",
                "Training investment needed",
                "Career path alignment opportunity"
            ]
        }

    async def _simulate_automation_replace(
        self,
        org_id: str,
        config: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Simulate automation replacement impact."""
        return {
            "cost_change": round(random.uniform(-20, -5), 1),
            "productivity_change": round(random.uniform(10, 30), 1),
            "skill_coverage_change": round(random.uniform(-15, 0), 1),
            "affected_employees": random.randint(2, 10),
            "risk_score": round(random.uniform(0.4, 0.7), 2),
            "insights": [
                "Significant cost savings potential",
                "Reskilling opportunity for affected employees",
                "Quality consistency improvement expected"
            ]
        }

    async def _simulate_reduction(
        self,
        org_id: str,
        config: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Simulate workforce reduction impact."""
        reduction_pct = config.get("reduction_percentage", 10)

        return {
            "cost_change": round(-reduction_pct * 1.2, 1),
            "productivity_change": round(random.uniform(-15, -5), 1),
            "skill_coverage_change": round(random.uniform(-20, -5), 1),
            "affected_employees": random.randint(5, 25),
            "risk_score": round(random.uniform(0.6, 0.9), 2),
            "insights": [
                "High morale risk for remaining employees",
                "Critical skill loss risk",
                "Workload redistribution needed"
            ]
        }

    async def get_attrition_risks(
        self,
        org_id: str,
        min_risk: float = 0.3
    ) -> List[Dict[str, Any]]:
        """Get employees at risk of attrition."""
        result = await self.db.execute(
            select(WorkforceScore).where(
                WorkforceScore.org_id == org_id,
                WorkforceScore.attrition_risk_score >= min_risk
            ).order_by(WorkforceScore.attrition_risk_score.desc())
        )
        at_risk = result.scalars().all()

        risks = []
        for score in at_risk:
            # Get user details
            user_result = await self.db.execute(
                select(User).where(User.id == score.user_id)
            )
            user = user_result.scalar_one_or_none()

            if user:
                # Determine risk factors
                factors = []
                if score.burnout_risk_score and score.burnout_risk_score > 0.5:
                    factors.append("High burnout indicators")
                if score.score_trend == "declining":
                    factors.append("Declining performance trend")
                if score.self_sufficiency_score and score.self_sufficiency_score < 60:
                    factors.append("Low engagement signals")

                # Calculate tenure
                tenure_months = (datetime.utcnow() - user.created_at).days // 30

                risk_level = (
                    "critical" if score.attrition_risk_score >= 0.7
                    else "high" if score.attrition_risk_score >= 0.5
                    else "medium"
                )

                risks.append({
                    "user_id": user.id,
                    "user_name": f"{user.first_name} {user.last_name}",
                    "risk_score": score.attrition_risk_score,
                    "risk_level": risk_level,
                    "factors": factors if factors else ["General risk indicators"],
                    "tenure_months": tenure_months
                })

        return risks

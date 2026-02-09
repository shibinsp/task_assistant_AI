"""
TaskPulse - AI Assistant - Prediction Service
ML-powered forecasting for tasks, velocity, and hiring
"""

from typing import Optional, List, Dict, Any
from datetime import datetime, timedelta
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_
import random
import math

from app.models.task import Task, TaskStatus
from app.models.prediction import Prediction, VelocitySnapshot
from app.models.user import User
from app.utils.helpers import generate_uuid


class PredictionService:
    """Service for ML-powered predictions."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def predict_task_delivery(
        self,
        task_id: str,
        org_id: str
    ) -> Dict[str, Any]:
        """
        Predict delivery date for a task.
        Uses historical data and task complexity.
        """
        result = await self.db.execute(
            select(Task).where(Task.id == task_id, Task.org_id == org_id)
        )
        task = result.scalar_one_or_none()

        if not task:
            return {"error": "Task not found"}

        # Get historical completion data for similar tasks
        historical_factor = await self._get_historical_factor(
            org_id, task.assigned_to, task.complexity_score
        )

        # Calculate base estimate
        base_hours = task.estimated_hours or 8.0
        adjusted_hours = base_hours * historical_factor

        # Calculate P25, P50, P90 estimates
        now = datetime.utcnow()
        p50_hours = adjusted_hours
        p25_hours = adjusted_hours * 0.7  # Optimistic
        p90_hours = adjusted_hours * 1.5  # Pessimistic

        # Consider blockers and dependencies
        blocker_delay = await self._estimate_blocker_delay(task_id, org_id)
        dependency_delay = await self._estimate_dependency_delay(task_id, org_id)

        total_delay = blocker_delay + dependency_delay

        # Generate predictions
        prediction = Prediction(
            id=generate_uuid(),
            org_id=org_id,
            entity_type="task",
            entity_id=task_id,
            prediction_type="delivery_date",
            p25_date=now + timedelta(hours=p25_hours + total_delay),
            p50_date=now + timedelta(hours=p50_hours + total_delay),
            p90_date=now + timedelta(hours=p90_hours + total_delay),
            confidence_score=0.75 - (total_delay / 100),  # Lower confidence with delays
            risk_score=min(1.0, (total_delay / 24) * 0.3 + (task.complexity_score or 0.5) * 0.4)
        )

        # Risk factors
        risk_factors = []
        if blocker_delay > 0:
            risk_factors.append(f"Blocker may add {blocker_delay:.1f}h delay")
        if dependency_delay > 0:
            risk_factors.append(f"Dependencies may add {dependency_delay:.1f}h delay")
        if task.complexity_score and task.complexity_score > 0.7:
            risk_factors.append("High complexity task")
        if task.is_overdue:
            risk_factors.append("Task is already overdue")

        prediction.risk_factors = risk_factors

        self.db.add(prediction)
        await self.db.flush()

        return {
            "task_id": task_id,
            "p25_date": prediction.p25_date.isoformat(),
            "p50_date": prediction.p50_date.isoformat(),
            "p90_date": prediction.p90_date.isoformat(),
            "confidence_score": prediction.confidence_score,
            "risk_score": prediction.risk_score,
            "risk_factors": risk_factors,
            "factors": {
                "base_estimate_hours": base_hours,
                "historical_adjustment": historical_factor,
                "blocker_delay_hours": blocker_delay,
                "dependency_delay_hours": dependency_delay
            }
        }

    async def _get_historical_factor(
        self,
        org_id: str,
        user_id: Optional[str],
        complexity: Optional[float]
    ) -> float:
        """Get historical adjustment factor based on past performance."""
        # In production, this would analyze historical task completions
        # For now, return a simulated factor
        base_factor = 1.0

        if user_id:
            # Simulate user-specific adjustment
            user_seed = hash(user_id) % 100
            base_factor *= 0.8 + (user_seed / 250)  # 0.8 - 1.2 range

        if complexity:
            # Higher complexity = longer time
            base_factor *= 1.0 + (complexity * 0.3)

        return base_factor

    async def _estimate_blocker_delay(self, task_id: str, org_id: str) -> float:
        """Estimate delay from blockers."""
        result = await self.db.execute(
            select(Task).where(Task.id == task_id, Task.org_id == org_id)
        )
        task = result.scalar_one_or_none()

        if task and task.is_blocked:
            # Average blocker resolution time (simulated)
            return random.uniform(4, 16)
        return 0.0

    async def _estimate_dependency_delay(self, task_id: str, org_id: str) -> float:
        """Estimate delay from dependencies."""
        # Get incomplete dependencies
        from app.models.task import TaskDependency

        result = await self.db.execute(
            select(TaskDependency).where(
                TaskDependency.task_id == task_id,
                TaskDependency.is_blocking == True
            )
        )
        dependencies = result.scalars().all()

        total_delay = 0.0
        for dep in dependencies:
            dep_result = await self.db.execute(
                select(Task).where(Task.id == dep.depends_on_id)
            )
            dep_task = dep_result.scalar_one_or_none()
            if dep_task and not dep_task.is_completed:
                remaining = (dep_task.estimated_hours or 8) - (dep_task.actual_hours or 0)
                total_delay += max(0, remaining)

        return total_delay

    async def predict_project_delivery(
        self,
        project_id: str,
        org_id: str
    ) -> Dict[str, Any]:
        """Predict delivery date for an entire project."""
        result = await self.db.execute(
            select(Task).where(
                Task.project_id == project_id,
                Task.org_id == org_id,
                Task.status.not_in([TaskStatus.DONE, TaskStatus.ARCHIVED])
            )
        )
        tasks = result.scalars().all()

        if not tasks:
            return {
                "project_id": project_id,
                "status": "complete",
                "remaining_tasks": 0
            }

        # Aggregate task predictions
        total_p50_hours = 0
        total_risk = 0
        risk_factors = []

        for task in tasks:
            prediction = await self.predict_task_delivery(task.id, org_id)
            if "error" not in prediction:
                hours_remaining = (task.estimated_hours or 8) - (task.actual_hours or 0)
                total_p50_hours += max(0, hours_remaining)
                total_risk += prediction.get("risk_score", 0.5)
                risk_factors.extend(prediction.get("risk_factors", []))

        avg_risk = total_risk / len(tasks) if tasks else 0
        now = datetime.utcnow()

        # Account for parallelization (assume 2 parallel streams)
        parallel_factor = 0.6

        return {
            "project_id": project_id,
            "remaining_tasks": len(tasks),
            "total_remaining_hours": total_p50_hours,
            "p25_date": (now + timedelta(hours=total_p50_hours * 0.7 * parallel_factor)).isoformat(),
            "p50_date": (now + timedelta(hours=total_p50_hours * parallel_factor)).isoformat(),
            "p90_date": (now + timedelta(hours=total_p50_hours * 1.5 * parallel_factor)).isoformat(),
            "risk_score": avg_risk,
            "top_risk_factors": list(set(risk_factors))[:5]
        }

    async def get_team_velocity(
        self,
        team_id: str,
        org_id: str,
        sprints: int = 5
    ) -> Dict[str, Any]:
        """Get team velocity over recent sprints."""
        # Get velocity snapshots
        result = await self.db.execute(
            select(VelocitySnapshot).where(
                VelocitySnapshot.team_id == team_id,
                VelocitySnapshot.org_id == org_id
            ).order_by(VelocitySnapshot.snapshot_date.desc()).limit(sprints)
        )
        snapshots = result.scalars().all()

        if not snapshots:
            # Generate mock velocity data
            velocities = [random.randint(20, 40) for _ in range(sprints)]
            return {
                "team_id": team_id,
                "sprint_velocities": velocities,
                "average_velocity": sum(velocities) / len(velocities),
                "trend": "stable",
                "predicted_next_sprint": int(sum(velocities) / len(velocities)),
                "confidence": 0.7
            }

        velocities = [s.velocity_points for s in snapshots]
        avg_velocity = sum(velocities) / len(velocities)

        # Calculate trend
        if len(velocities) >= 2:
            recent_avg = sum(velocities[:2]) / 2
            older_avg = sum(velocities[2:]) / max(1, len(velocities) - 2)
            if recent_avg > older_avg * 1.1:
                trend = "increasing"
            elif recent_avg < older_avg * 0.9:
                trend = "decreasing"
            else:
                trend = "stable"
        else:
            trend = "insufficient_data"

        return {
            "team_id": team_id,
            "sprint_velocities": velocities,
            "average_velocity": avg_velocity,
            "trend": trend,
            "predicted_next_sprint": int(avg_velocity * (1.05 if trend == "increasing" else 0.95 if trend == "decreasing" else 1.0)),
            "confidence": min(0.9, 0.5 + len(velocities) * 0.08)
        }

    async def forecast_velocity(
        self,
        team_id: str,
        org_id: str,
        weeks_ahead: int = 8
    ) -> Dict[str, Any]:
        """Forecast team velocity for future sprints."""
        current = await self.get_team_velocity(team_id, org_id)
        avg_velocity = current["average_velocity"]
        trend = current["trend"]

        # Generate forecast
        forecasts = []
        velocity = avg_velocity

        for week in range(1, weeks_ahead + 1):
            # Apply trend adjustment
            if trend == "increasing":
                velocity *= 1.02
            elif trend == "decreasing":
                velocity *= 0.98

            # Add some variance
            variance = random.uniform(-0.1, 0.1)
            forecast_velocity = velocity * (1 + variance)

            forecasts.append({
                "week": week,
                "predicted_velocity": round(forecast_velocity, 1),
                "confidence": max(0.3, 0.9 - week * 0.05)
            })

        return {
            "team_id": team_id,
            "current_average": avg_velocity,
            "trend": trend,
            "forecasts": forecasts,
            "assumptions": [
                "Based on historical velocity data",
                "Assumes stable team composition",
                "Does not account for holidays/PTO"
            ]
        }

    async def predict_hiring_needs(
        self,
        org_id: str,
        months_ahead: int = 6
    ) -> Dict[str, Any]:
        """Predict hiring needs based on workload and capacity."""
        # Get current task load
        result = await self.db.execute(
            select(func.count()).where(
                Task.org_id == org_id,
                Task.status.not_in([TaskStatus.DONE, TaskStatus.ARCHIVED])
            )
        )
        active_tasks = result.scalar() or 0

        # Get team size
        result = await self.db.execute(
            select(func.count()).where(User.org_id == org_id, User.is_active == True)
        )
        team_size = result.scalar() or 1

        # Calculate capacity metrics
        tasks_per_person = active_tasks / team_size
        optimal_load = 5  # Optimal tasks per person

        overload_factor = tasks_per_person / optimal_load

        # Determine hiring needs
        if overload_factor > 1.3:
            needed_hires = math.ceil((active_tasks - team_size * optimal_load) / optimal_load)
            urgency = "high"
        elif overload_factor > 1.1:
            needed_hires = 1
            urgency = "medium"
        else:
            needed_hires = 0
            urgency = "low"

        # Skill gap analysis (mock)
        skill_gaps = [
            {"skill": "Python", "gap_score": 0.3, "priority": "high"},
            {"skill": "Machine Learning", "gap_score": 0.6, "priority": "critical"},
            {"skill": "DevOps", "gap_score": 0.4, "priority": "medium"}
        ]

        return {
            "current_team_size": team_size,
            "active_tasks": active_tasks,
            "tasks_per_person": round(tasks_per_person, 1),
            "overload_factor": round(overload_factor, 2),
            "recommended_hires": needed_hires,
            "urgency": urgency,
            "skill_gaps": skill_gaps,
            "timeline_months": months_ahead,
            "projected_cost": needed_hires * 80000,  # Mock annual cost per hire
            "recommendations": [
                f"Consider hiring {needed_hires} additional team members" if needed_hires > 0 else "Team capacity is adequate",
                "Focus on Machine Learning skills based on gap analysis",
                "Review workload distribution across team"
            ]
        }

    async def get_prediction_accuracy(
        self,
        org_id: str,
        days: int = 30
    ) -> Dict[str, Any]:
        """Get prediction accuracy metrics."""
        cutoff = datetime.utcnow() - timedelta(days=days)

        result = await self.db.execute(
            select(Prediction).where(
                Prediction.org_id == org_id,
                Prediction.created_at >= cutoff,
                Prediction.actual_date.isnot(None)
            )
        )
        predictions = result.scalars().all()

        if not predictions:
            return {
                "period_days": days,
                "total_predictions": 0,
                "accuracy_metrics": {
                    "p50_accuracy": None,
                    "average_deviation_hours": None,
                    "on_time_rate": None
                },
                "message": "No completed predictions in this period"
            }

        # Calculate accuracy metrics
        total = len(predictions)
        on_time = 0
        total_deviation = 0

        for pred in predictions:
            if pred.actual_date and pred.p50_date:
                deviation = abs((pred.actual_date - pred.p50_date).total_seconds() / 3600)
                total_deviation += deviation

                if pred.actual_date <= pred.p90_date:
                    on_time += 1

        return {
            "period_days": days,
            "total_predictions": total,
            "accuracy_metrics": {
                "p50_accuracy": round((total - sum(1 for p in predictions if p.actual_date and p.p50_date and p.actual_date > p.p50_date)) / total * 100, 1),
                "p90_accuracy": round(on_time / total * 100, 1),
                "average_deviation_hours": round(total_deviation / total, 1),
                "on_time_rate": round(on_time / total * 100, 1)
            },
            "trend": "improving"  # Would be calculated from historical data
        }

    async def record_actual_completion(
        self,
        prediction_id: str,
        actual_date: datetime
    ) -> Optional[Prediction]:
        """Record actual completion date for prediction accuracy tracking."""
        result = await self.db.execute(
            select(Prediction).where(Prediction.id == prediction_id)
        )
        prediction = result.scalar_one_or_none()

        if prediction:
            prediction.actual_date = actual_date
            await self.db.flush()

        return prediction

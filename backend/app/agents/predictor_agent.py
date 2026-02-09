"""
Predictor Agent

AI-powered agent that forecasts task delivery and identifies risks.
Provides P25/P50/P90 estimates, risk analysis, and mitigation suggestions.
"""

import logging
import random
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

from .base import (
    AgentCapability,
    AgentEvent,
    AgentResult,
    BaseAgent,
    EventType,
)
from .context import AgentContext, MessageRole

logger = logging.getLogger(__name__)


class PredictorAgent(BaseAgent):
    """
    Agent that predicts task delivery and identifies risks.

    Provides:
    - P25/P50/P90 completion estimates
    - Risk identification and scoring
    - Delay cascade analysis
    - Mitigation recommendations
    """

    name = "predictor_agent"
    description = "Forecasts delivery risks and provides completion estimates"
    version = "1.0.0"

    capabilities = [
        AgentCapability.PREDICTION,
    ]

    handled_events = [
        EventType.TASK_CREATED,
        EventType.TASK_UPDATED,
        EventType.SCHEDULED,
    ]

    priority = 60

    # Risk thresholds
    HIGH_RISK_THRESHOLD = 0.7
    MEDIUM_RISK_THRESHOLD = 0.4

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        super().__init__(config)
        self.confidence_model = config.get("confidence_model", "default") if config else "default"

    async def can_handle(self, event: AgentEvent) -> bool:
        """Check if prediction is needed"""
        if event.event_type == EventType.SCHEDULED:
            return event.payload.get("job_type") == "daily_prediction"

        if event.event_type in [EventType.TASK_CREATED, EventType.TASK_UPDATED]:
            # Only predict for tasks with deadlines or high priority
            payload = event.payload or {}
            return (
                payload.get("due_date") is not None or
                payload.get("priority") in ["high", "critical"]
            )

        return False

    async def execute(self, context: AgentContext) -> AgentResult:
        """Generate predictions and risk analysis"""
        result = AgentResult(
            success=True,
            agent_name=self.name,
            event_id=context.event.id if context.event else "direct"
        )

        try:
            if context.task:
                # Single task prediction
                prediction = await self._predict_task(context)
                risks = await self._analyze_risks(context)
                cascade = await self._analyze_cascade(context)

                result.output = {
                    "task_id": context.task.id,
                    "prediction": prediction,
                    "risks": risks,
                    "cascade_analysis": cascade,
                    "recommendations": self._generate_recommendations(prediction, risks),
                }

                result.message = self._format_prediction_message(prediction, risks)

            else:
                # Batch prediction (scheduled run)
                batch_results = await self._batch_predict(context)
                result.output = {
                    "batch_prediction": batch_results,
                    "summary": self._summarize_batch(batch_results),
                }
                result.message = f"Analyzed {len(batch_results)} tasks for delivery risks."

            context.add_message(
                result.message,
                role=MessageRole.AGENT,
                agent_name=self.name,
            )

            result.actions = [
                {"type": "prediction_generated", "confidence": result.output.get("prediction", {}).get("confidence", 0)},
            ]

            if result.output.get("risks", {}).get("overall_risk", 0) > self.HIGH_RISK_THRESHOLD:
                result.actions.append({"type": "high_risk_alert"})

        except Exception as e:
            logger.error(f"Predictor agent error: {e}")
            result.success = False
            result.error = str(e)

        return result

    async def _predict_task(self, context: AgentContext) -> Dict[str, Any]:
        """Generate completion prediction for a task"""
        task = context.task

        # Base estimate from task
        estimated_hours = task.estimated_hours or 8
        actual_hours = task.actual_hours or 0
        progress = self._calculate_progress(task)

        # Calculate remaining work
        remaining_hours = max(0, estimated_hours - actual_hours)

        # Apply historical adjustment factors
        velocity_factor = await self._get_velocity_factor(context)
        complexity_factor = self._estimate_complexity_factor(task)

        # Calculate P25/P50/P90
        adjusted_remaining = remaining_hours * velocity_factor * complexity_factor

        p50_hours = adjusted_remaining
        p25_hours = adjusted_remaining * 0.7  # Optimistic
        p90_hours = adjusted_remaining * 1.5  # Pessimistic

        # Convert to dates
        now = datetime.utcnow()
        work_hours_per_day = 6  # Assume 6 productive hours per day

        prediction = {
            "estimated_remaining_hours": round(adjusted_remaining, 1),
            "p25": {
                "hours": round(p25_hours, 1),
                "date": (now + timedelta(hours=p25_hours * (24/work_hours_per_day))).isoformat(),
                "label": "Best case"
            },
            "p50": {
                "hours": round(p50_hours, 1),
                "date": (now + timedelta(hours=p50_hours * (24/work_hours_per_day))).isoformat(),
                "label": "Most likely"
            },
            "p90": {
                "hours": round(p90_hours, 1),
                "date": (now + timedelta(hours=p90_hours * (24/work_hours_per_day))).isoformat(),
                "label": "Worst case"
            },
            "confidence": self._calculate_confidence(task, progress),
            "progress_percent": progress,
            "velocity_factor": round(velocity_factor, 2),
            "on_track": self._is_on_track(task, p50_hours),
        }

        # Check against due date
        if task.due_date:
            due_date = task.due_date if isinstance(task.due_date, datetime) else datetime.fromisoformat(str(task.due_date))
            hours_until_due = (due_date - now).total_seconds() / 3600

            prediction["due_date"] = due_date.isoformat()
            prediction["hours_until_due"] = round(hours_until_due, 1)
            prediction["will_meet_deadline"] = {
                "p25": p25_hours * (24/work_hours_per_day) <= hours_until_due,
                "p50": p50_hours * (24/work_hours_per_day) <= hours_until_due,
                "p90": p90_hours * (24/work_hours_per_day) <= hours_until_due,
            }

        return prediction

    def _calculate_progress(self, task: Any) -> float:
        """Calculate task progress percentage"""
        if task.status == "completed":
            return 100.0

        if task.estimated_hours and task.actual_hours:
            # Based on hours spent vs estimated
            return min(95, (task.actual_hours / task.estimated_hours) * 100)

        # Status-based estimate
        status_progress = {
            "pending": 0,
            "in_progress": 30,
            "in_review": 80,
            "blocked": 20,
        }

        return status_progress.get(task.status, 0)

    async def _get_velocity_factor(self, context: AgentContext) -> float:
        """Get velocity adjustment factor based on historical data"""
        # In production, this would analyze historical task completion times
        # For now, return a simulated factor

        # Factors that affect velocity
        user = context.user
        if user:
            skill_level = user.skill_level
            if skill_level == "senior":
                return 0.8  # Faster than average
            elif skill_level == "junior":
                return 1.3  # Slower than average

        return 1.0  # Average velocity

    def _estimate_complexity_factor(self, task: Any) -> float:
        """Estimate complexity factor from task attributes"""
        factor = 1.0

        # Priority impact
        if task.priority == "critical":
            factor *= 0.9  # Critical tasks get more focus
        elif task.priority == "low":
            factor *= 1.1  # Low priority may be delayed

        # Blockers impact
        if task.blockers:
            factor *= 1.0 + (len(task.blockers) * 0.2)

        return factor

    def _calculate_confidence(self, task: Any, progress: float) -> float:
        """Calculate prediction confidence"""
        confidence = 0.7  # Base confidence

        # More progress = higher confidence
        confidence += (progress / 100) * 0.2

        # Has estimate = higher confidence
        if task.estimated_hours:
            confidence += 0.05

        # Has actual hours logged = higher confidence
        if task.actual_hours:
            confidence += 0.05

        return min(0.95, round(confidence, 2))

    def _is_on_track(self, task: Any, p50_hours: float) -> bool:
        """Determine if task is on track for completion"""
        if not task.due_date:
            return True

        due = task.due_date if isinstance(task.due_date, datetime) else datetime.fromisoformat(str(task.due_date))
        hours_until_due = (due - datetime.utcnow()).total_seconds() / 3600
        work_hours = hours_until_due * (6/24)  # 6 productive hours per day

        return p50_hours <= work_hours

    async def _analyze_risks(self, context: AgentContext) -> Dict[str, Any]:
        """Analyze risks for the task"""
        task = context.task
        risks = []

        # Check various risk factors
        if task.blockers:
            risks.append({
                "type": "blockers",
                "severity": "high" if len(task.blockers) > 1 else "medium",
                "description": f"Task has {len(task.blockers)} active blocker(s)",
                "score": 0.3 * len(task.blockers),
            })

        if task.priority in ["critical", "high"] and task.status == "pending":
            risks.append({
                "type": "not_started",
                "severity": "high",
                "description": "High priority task not yet started",
                "score": 0.4,
            })

        if task.due_date:
            due = task.due_date if isinstance(task.due_date, datetime) else datetime.fromisoformat(str(task.due_date))
            days_until_due = (due - datetime.utcnow()).days

            if days_until_due < 0:
                risks.append({
                    "type": "overdue",
                    "severity": "critical",
                    "description": f"Task is {abs(days_until_due)} days overdue",
                    "score": 0.9,
                })
            elif days_until_due < 2:
                risks.append({
                    "type": "deadline_near",
                    "severity": "high",
                    "description": f"Deadline in {days_until_due} days",
                    "score": 0.6,
                })

        # Check if estimate might be too optimistic
        if task.estimated_hours and task.actual_hours:
            if task.actual_hours > task.estimated_hours * 0.8:
                progress = self._calculate_progress(task)
                if progress < 70:
                    risks.append({
                        "type": "estimate_exceeded",
                        "severity": "medium",
                        "description": "Actual hours approaching estimate but task not near completion",
                        "score": 0.5,
                    })

        # Calculate overall risk
        overall_risk = min(1.0, sum(r["score"] for r in risks))

        return {
            "risks": risks,
            "overall_risk": round(overall_risk, 2),
            "risk_level": (
                "critical" if overall_risk > 0.8 else
                "high" if overall_risk > self.HIGH_RISK_THRESHOLD else
                "medium" if overall_risk > self.MEDIUM_RISK_THRESHOLD else
                "low"
            ),
            "risk_count": len(risks),
        }

    async def _analyze_cascade(self, context: AgentContext) -> Dict[str, Any]:
        """Analyze how delays would cascade to dependent tasks"""
        task = context.task

        # In production, this would query dependent tasks
        # For now, return mock cascade analysis

        cascade = {
            "dependent_tasks": [],
            "total_impact_hours": 0,
            "affected_team_members": [],
            "critical_path_impact": False,
        }

        # Simulate finding dependent tasks
        if task.priority in ["critical", "high"]:
            cascade["dependent_tasks"] = [
                {
                    "id": "dep_1",
                    "title": "Dependent feature integration",
                    "delay_hours": 4,
                    "assignee": "team_member_1"
                }
            ]
            cascade["total_impact_hours"] = 4
            cascade["affected_team_members"] = ["team_member_1"]
            cascade["critical_path_impact"] = True

        return cascade

    def _generate_recommendations(
        self,
        prediction: Dict[str, Any],
        risks: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """Generate actionable recommendations"""
        recommendations = []

        # Check deadline risk
        if prediction.get("will_meet_deadline", {}).get("p50") is False:
            recommendations.append({
                "priority": "high",
                "type": "deadline_risk",
                "action": "Consider reducing scope or adding resources",
                "reason": "P50 estimate exceeds deadline",
            })

        # Check for blockers
        blocker_risk = next((r for r in risks.get("risks", []) if r["type"] == "blockers"), None)
        if blocker_risk:
            recommendations.append({
                "priority": "high",
                "type": "resolve_blockers",
                "action": "Focus on resolving blockers before continuing work",
                "reason": blocker_risk["description"],
            })

        # Check if not started
        if not prediction.get("on_track") and prediction.get("progress_percent", 0) < 10:
            recommendations.append({
                "priority": "medium",
                "type": "start_now",
                "action": "Begin work immediately to improve delivery confidence",
                "reason": "Task not yet started",
            })

        # Low confidence recommendation
        if prediction.get("confidence", 0) < 0.6:
            recommendations.append({
                "priority": "medium",
                "type": "improve_tracking",
                "action": "Log time and update progress more frequently",
                "reason": "Low prediction confidence due to limited data",
            })

        return recommendations

    def _format_prediction_message(
        self,
        prediction: Dict[str, Any],
        risks: Dict[str, Any]
    ) -> str:
        """Format a human-readable prediction message"""
        p50 = prediction["p50"]
        risk_level = risks["risk_level"]

        message = f"Predicted completion: {p50['hours']} hours (P50). "

        if prediction.get("on_track"):
            message += "Task is on track. "
        else:
            message += "Task is at risk of delay. "

        message += f"Risk level: {risk_level}."

        if risks["risks"]:
            message += f" Found {len(risks['risks'])} risk factor(s)."

        return message

    async def _batch_predict(self, context: AgentContext) -> List[Dict[str, Any]]:
        """Run predictions for multiple tasks (scheduled job)"""
        # In production, this would query pending/in-progress tasks
        # and run predictions for each

        batch_results = []

        # Mock batch results
        for i in range(5):
            batch_results.append({
                "task_id": f"task_{i}",
                "title": f"Sample Task {i}",
                "p50_hours": 4 + (i * 2),
                "risk_level": random.choice(["low", "medium", "high"]),
                "on_track": random.choice([True, True, False]),
            })

        return batch_results

    def _summarize_batch(self, batch_results: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Summarize batch prediction results"""
        at_risk = [r for r in batch_results if not r.get("on_track")]
        high_risk = [r for r in batch_results if r.get("risk_level") == "high"]

        return {
            "total_tasks": len(batch_results),
            "tasks_at_risk": len(at_risk),
            "high_risk_count": len(high_risk),
            "on_track_percentage": round(
                ((len(batch_results) - len(at_risk)) / len(batch_results)) * 100
                if batch_results else 0,
                1
            ),
        }

"""
TaskPulse - AI Assistant - Automation Service
Pattern detection and automation management
"""

from typing import Optional, List, Dict, Any
from datetime import datetime, timedelta
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_
import random
import hashlib

from app.models.automation import (
    AutomationPattern, AIAgent, AgentRun, AgentStatus,
    PatternStatus
)
from app.models.task import Task, TaskStatus
from app.utils.helpers import generate_uuid


class AutomationService:
    """Service for automation pattern detection and management."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect_patterns(
        self,
        org_id: str,
        min_occurrences: int = 3,
        time_window_days: int = 30
    ) -> List[Dict[str, Any]]:
        """
        Detect repetitive task patterns that could be automated.
        """
        cutoff = datetime.utcnow() - timedelta(days=time_window_days)

        # Get completed tasks in time window
        result = await self.db.execute(
            select(Task).where(
                Task.org_id == org_id,
                Task.status == TaskStatus.DONE,
                Task.completed_at >= cutoff
            )
        )
        tasks = result.scalars().all()

        # Group tasks by similarity (title patterns, tools, skills)
        pattern_groups = {}

        for task in tasks:
            # Create pattern signature
            signature = self._create_pattern_signature(task)

            if signature not in pattern_groups:
                pattern_groups[signature] = {
                    "tasks": [],
                    "tools": set(),
                    "skills": set()
                }

            pattern_groups[signature]["tasks"].append(task)
            pattern_groups[signature]["tools"].update(task.tools)
            pattern_groups[signature]["skills"].update(task.skills_required)

        # Filter patterns that meet minimum occurrences
        detected_patterns = []

        for signature, group in pattern_groups.items():
            if len(group["tasks"]) >= min_occurrences:
                # Calculate automation potential
                avg_hours = sum(t.actual_hours or 0 for t in group["tasks"]) / len(group["tasks"])
                consistency = self._calculate_consistency(group["tasks"])

                pattern = {
                    "signature": signature,
                    "occurrence_count": len(group["tasks"]),
                    "sample_titles": [t.title for t in group["tasks"][:3]],
                    "common_tools": list(group["tools"]),
                    "required_skills": list(group["skills"]),
                    "avg_completion_hours": round(avg_hours, 1),
                    "consistency_score": consistency,
                    "automation_potential": round(consistency * 0.7 + (1 - avg_hours/40) * 0.3, 2),
                    "estimated_savings_per_month": round(avg_hours * len(group["tasks"]) / time_window_days * 30 * 0.7, 1)
                }

                detected_patterns.append(pattern)

        # Sort by automation potential
        detected_patterns.sort(key=lambda x: x["automation_potential"], reverse=True)

        return detected_patterns

    def _create_pattern_signature(self, task: Task) -> str:
        """Create a signature for grouping similar tasks."""
        # Normalize title (remove numbers, specific IDs)
        normalized_title = ''.join(c.lower() for c in task.title if c.isalpha() or c.isspace())
        words = normalized_title.split()[:5]  # First 5 words

        # Combine with tools and create hash
        signature_parts = words + sorted(task.tools)
        signature_str = '|'.join(signature_parts)

        return hashlib.md5(signature_str.encode()).hexdigest()[:12]

    def _calculate_consistency(self, tasks: List[Task]) -> float:
        """Calculate how consistent the task execution is."""
        if len(tasks) < 2:
            return 0.5

        # Check time consistency
        hours = [t.actual_hours or 0 for t in tasks if t.actual_hours]
        if not hours:
            return 0.5

        avg = sum(hours) / len(hours)
        variance = sum((h - avg) ** 2 for h in hours) / len(hours)
        std_dev = variance ** 0.5

        # Lower variance = higher consistency
        consistency = max(0, 1 - (std_dev / avg)) if avg > 0 else 0.5

        return round(consistency, 2)

    async def create_pattern(
        self,
        org_id: str,
        name: str,
        description: str,
        trigger_conditions: Dict[str, Any],
        automation_steps: List[Dict[str, Any]],
        created_by: str
    ) -> AutomationPattern:
        """Create a new automation pattern."""
        pattern = AutomationPattern(
            id=generate_uuid(),
            org_id=org_id,
            name=name,
            description=description,
            created_by=created_by
        )
        pattern.trigger_conditions = trigger_conditions
        pattern.automation_steps = automation_steps

        # Calculate readiness score
        pattern.readiness_score = self._calculate_readiness(trigger_conditions, automation_steps)

        self.db.add(pattern)
        await self.db.flush()
        await self.db.refresh(pattern)

        return pattern

    def _calculate_readiness(
        self,
        trigger_conditions: Dict[str, Any],
        automation_steps: List[Dict[str, Any]]
    ) -> float:
        """Calculate automation readiness score."""
        score = 0.5

        # More specific triggers = higher readiness
        if trigger_conditions:
            score += min(0.2, len(trigger_conditions) * 0.05)

        # More defined steps = higher readiness
        if automation_steps:
            score += min(0.3, len(automation_steps) * 0.05)

        return round(min(1.0, score), 2)

    async def get_patterns(
        self,
        org_id: str,
        status: Optional[PatternStatus] = None,
        limit: int = 50,
        offset: int = 0
    ) -> tuple[List[AutomationPattern], int]:
        """Get automation patterns for an organization."""
        query = select(AutomationPattern).where(AutomationPattern.org_id == org_id)

        if status:
            query = query.where(AutomationPattern.status == status)

        count_query = select(func.count()).select_from(query.subquery())
        total = (await self.db.execute(count_query)).scalar() or 0

        result = await self.db.execute(
            query.order_by(AutomationPattern.created_at.desc())
            .offset(offset).limit(limit)
        )
        patterns = list(result.scalars().all())

        return patterns, total

    async def update_pattern_status(
        self,
        pattern_id: str,
        org_id: str,
        new_status: PatternStatus
    ) -> Optional[AutomationPattern]:
        """Update pattern status."""
        result = await self.db.execute(
            select(AutomationPattern).where(
                AutomationPattern.id == pattern_id,
                AutomationPattern.org_id == org_id
            )
        )
        pattern = result.scalar_one_or_none()

        if pattern:
            pattern.status = new_status
            await self.db.flush()

        return pattern

    # AI Agent Management

    async def create_agent(
        self,
        org_id: str,
        pattern_id: str,
        name: str,
        description: str,
        config: Dict[str, Any],
        created_by: str
    ) -> AIAgent:
        """Create a new AI agent."""
        agent = AIAgent(
            id=generate_uuid(),
            org_id=org_id,
            pattern_id=pattern_id,
            name=name,
            description=description,
            created_by=created_by,
            status=AgentStatus.CREATED
        )
        agent.config = config

        self.db.add(agent)
        await self.db.flush()
        await self.db.refresh(agent)

        return agent

    async def get_agent(
        self,
        agent_id: str,
        org_id: str
    ) -> Optional[AIAgent]:
        """Get an AI agent by ID."""
        result = await self.db.execute(
            select(AIAgent).where(
                AIAgent.id == agent_id,
                AIAgent.org_id == org_id
            )
        )
        return result.scalar_one_or_none()

    async def get_agents(
        self,
        org_id: str,
        status: Optional[AgentStatus] = None,
        limit: int = 50,
        offset: int = 0
    ) -> tuple[List[AIAgent], int]:
        """Get AI agents for an organization."""
        query = select(AIAgent).where(AIAgent.org_id == org_id)

        if status:
            query = query.where(AIAgent.status == status)

        count_query = select(func.count()).select_from(query.subquery())
        total = (await self.db.execute(count_query)).scalar() or 0

        result = await self.db.execute(
            query.order_by(AIAgent.created_at.desc())
            .offset(offset).limit(limit)
        )
        agents = list(result.scalars().all())

        return agents, total

    async def update_agent_status(
        self,
        agent_id: str,
        org_id: str,
        new_status: AgentStatus
    ) -> Optional[AIAgent]:
        """Update agent status with validation."""
        agent = await self.get_agent(agent_id, org_id)

        if not agent:
            return None

        # Validate status transitions
        valid_transitions = {
            AgentStatus.CREATED: [AgentStatus.SHADOW],
            AgentStatus.SHADOW: [AgentStatus.SUPERVISED, AgentStatus.PAUSED],
            AgentStatus.SUPERVISED: [AgentStatus.LIVE, AgentStatus.SHADOW, AgentStatus.PAUSED],
            AgentStatus.LIVE: [AgentStatus.SUPERVISED, AgentStatus.PAUSED],
            AgentStatus.PAUSED: [AgentStatus.SHADOW, AgentStatus.SUPERVISED, AgentStatus.LIVE]
        }

        if new_status not in valid_transitions.get(agent.status, []):
            return None

        agent.status = new_status

        # Update timestamps
        if new_status == AgentStatus.SHADOW:
            agent.shadow_started_at = datetime.utcnow()
        elif new_status == AgentStatus.LIVE:
            agent.live_started_at = datetime.utcnow()

        await self.db.flush()
        return agent

    async def record_agent_run(
        self,
        agent_id: str,
        org_id: str,
        trigger_data: Dict[str, Any],
        output_data: Dict[str, Any],
        success: bool,
        execution_time_ms: int,
        is_shadow: bool = False
    ) -> AgentRun:
        """Record an agent execution run."""
        run = AgentRun(
            id=generate_uuid(),
            org_id=org_id,
            agent_id=agent_id,
            success=success,
            execution_time_ms=execution_time_ms,
            is_shadow_run=is_shadow
        )
        run.trigger_data = trigger_data
        run.output_data = output_data

        self.db.add(run)
        await self.db.flush()

        # Update agent metrics
        agent = await self.get_agent(agent_id, org_id)
        if agent:
            agent.total_runs = (agent.total_runs or 0) + 1
            if success:
                agent.successful_runs = (agent.successful_runs or 0) + 1
            agent.last_run_at = datetime.utcnow()
            await self.db.flush()

        return run

    async def get_shadow_report(
        self,
        agent_id: str,
        org_id: str
    ) -> Dict[str, Any]:
        """Get shadow mode validation report for an agent."""
        agent = await self.get_agent(agent_id, org_id)

        if not agent:
            return {"error": "Agent not found"}

        # Get shadow runs
        result = await self.db.execute(
            select(AgentRun).where(
                AgentRun.agent_id == agent_id,
                AgentRun.is_shadow_run == True
            ).order_by(AgentRun.created_at.desc()).limit(100)
        )
        shadow_runs = result.scalars().all()

        if not shadow_runs:
            return {
                "agent_id": agent_id,
                "shadow_runs": 0,
                "status": "no_data",
                "recommendation": "Agent needs more shadow runs for validation"
            }

        total_runs = len(shadow_runs)
        successful = sum(1 for r in shadow_runs if r.success)
        match_rate = successful / total_runs if total_runs > 0 else 0

        # Calculate shadow period
        shadow_days = 0
        if agent.shadow_started_at:
            shadow_days = (datetime.utcnow() - agent.shadow_started_at).days

        # Determine readiness for live
        ready_for_live = match_rate >= 0.95 and shadow_days >= 14 and total_runs >= 20

        return {
            "agent_id": agent_id,
            "agent_name": agent.name,
            "shadow_runs": total_runs,
            "successful_runs": successful,
            "match_rate": round(match_rate * 100, 1),
            "shadow_days": shadow_days,
            "required_days": 14,
            "ready_for_live": ready_for_live,
            "recommendation": (
                "Agent is ready to go live" if ready_for_live
                else f"Continue shadow mode: {'need more runs' if total_runs < 20 else 'match rate too low' if match_rate < 0.95 else 'need more days'}"
            ),
            "recent_runs": [
                {
                    "id": r.id,
                    "success": r.success,
                    "execution_time_ms": r.execution_time_ms,
                    "created_at": r.created_at.isoformat()
                } for r in shadow_runs[:10]
            ]
        }

    async def get_automation_roi(
        self,
        org_id: str,
        period_days: int = 30
    ) -> Dict[str, Any]:
        """Calculate ROI from automation."""
        cutoff = datetime.utcnow() - timedelta(days=period_days)

        # Get live agents
        result = await self.db.execute(
            select(AIAgent).where(
                AIAgent.org_id == org_id,
                AIAgent.status == AgentStatus.LIVE
            )
        )
        live_agents = result.scalars().all()

        # Get runs in period
        result = await self.db.execute(
            select(AgentRun).where(
                AgentRun.org_id == org_id,
                AgentRun.created_at >= cutoff,
                AgentRun.is_shadow_run == False
            )
        )
        runs = result.scalars().all()

        # Calculate metrics
        total_runs = len(runs)
        successful_runs = sum(1 for r in runs if r.success)

        # Estimate time saved (assume 15 min per automated task)
        estimated_hours_saved = (successful_runs * 15) / 60

        # Estimate cost savings ($50/hour average)
        estimated_cost_savings = estimated_hours_saved * 50

        return {
            "period_days": period_days,
            "live_agents": len(live_agents),
            "total_runs": total_runs,
            "successful_runs": successful_runs,
            "success_rate": round(successful_runs / total_runs * 100, 1) if total_runs > 0 else 0,
            "estimated_hours_saved": round(estimated_hours_saved, 1),
            "estimated_cost_savings": round(estimated_cost_savings, 2),
            "agents_breakdown": [
                {
                    "id": a.id,
                    "name": a.name,
                    "runs": a.total_runs or 0,
                    "success_rate": round((a.successful_runs or 0) / (a.total_runs or 1) * 100, 1)
                } for a in live_agents
            ],
            "recommendations": [
                "Consider expanding automation to more patterns" if len(live_agents) < 5 else "Good automation coverage",
                "Review failed runs for improvement opportunities" if successful_runs < total_runs * 0.9 else "High success rate maintained"
            ]
        }

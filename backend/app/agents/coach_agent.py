"""
Coach Agent

AI-powered agent that provides personalized guidance and growth
recommendations based on performance patterns, skill gaps, and goals.
"""

import logging
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


class CoachAgent(BaseAgent):
    """
    Agent that provides personalized coaching and growth recommendations.

    Features:
    - Performance pattern analysis
    - Skill gap identification
    - Learning resource suggestions
    - Motivational feedback
    - Career development guidance
    """

    name = "coach_agent"
    description = "Provides personalized guidance, feedback, and growth recommendations"
    version = "1.0.0"

    capabilities = [
        AgentCapability.COACHING,
        AgentCapability.NATURAL_LANGUAGE,
    ]

    handled_events = [
        EventType.CHECKIN_RESPONSE,
        EventType.TASK_COMPLETED,
        EventType.USER_MESSAGE,
        EventType.SCHEDULED,
    ]

    priority = 70

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        super().__init__(config)
        self.feedback_style = config.get("feedback_style", "supportive") if config else "supportive"
        self.include_resources = config.get("include_resources", True) if config else True

    async def can_handle(self, event: AgentEvent) -> bool:
        """Check if coaching is needed"""
        if event.event_type == EventType.SCHEDULED:
            return event.payload.get("job_type") in ["weekly_feedback", "monthly_review"]

        if event.event_type == EventType.TASK_COMPLETED:
            # Provide feedback on completed tasks
            return True

        if event.event_type == EventType.CHECKIN_RESPONSE:
            # Coach based on check-in sentiment
            sentiment = event.payload.get("sentiment", "")
            return sentiment in ["negative", "frustrated", "struggling"]

        if event.event_type == EventType.USER_MESSAGE:
            message = event.payload.get("message", "").lower()
            coaching_triggers = [
                "how am i doing", "feedback", "improve", "learn",
                "career", "growth", "stuck", "struggling", "help me grow"
            ]
            return any(trigger in message for trigger in coaching_triggers)

        return False

    async def execute(self, context: AgentContext) -> AgentResult:
        """Provide coaching and guidance"""
        result = AgentResult(
            success=True,
            agent_name=self.name,
            event_id=context.event.id if context.event else "direct"
        )

        try:
            # Analyze performance
            performance = await self._analyze_performance(context)

            # Identify skill gaps
            skill_gaps = await self._identify_skill_gaps(context)

            # Generate personalized feedback
            feedback = await self._generate_feedback(context, performance, skill_gaps)

            # Suggest learning resources
            resources = []
            if self.include_resources and skill_gaps:
                resources = await self._suggest_resources(skill_gaps)

            # Generate action items
            action_items = self._generate_action_items(performance, skill_gaps)

            result.output = {
                "performance_summary": performance,
                "skill_gaps": skill_gaps,
                "feedback": feedback,
                "learning_resources": resources,
                "action_items": action_items,
                "encouragement": self._generate_encouragement(performance),
            }

            result.message = feedback["summary"]

            context.add_message(
                result.message,
                role=MessageRole.AGENT,
                agent_name=self.name,
                metadata={"type": "coaching_feedback"}
            )

            result.actions = [
                {"type": "feedback_provided", "style": self.feedback_style},
                {"type": "gaps_identified", "count": len(skill_gaps)},
                {"type": "resources_suggested", "count": len(resources)},
            ]

        except Exception as e:
            logger.error(f"Coach agent error: {e}")
            result.success = False
            result.error = str(e)

        return result

    async def _analyze_performance(self, context: AgentContext) -> Dict[str, Any]:
        """Analyze user's recent performance"""
        user = context.user

        # In production, this would query actual task history
        # For now, return mock performance data

        performance = {
            "period": "last_30_days",
            "tasks_completed": 12,
            "tasks_on_time": 10,
            "average_estimation_accuracy": 0.85,
            "productivity_trend": "improving",
            "streak_days": 5,
            "strengths": [],
            "areas_for_improvement": [],
        }

        # Analyze patterns
        if performance["tasks_on_time"] / max(performance["tasks_completed"], 1) > 0.8:
            performance["strengths"].append({
                "area": "time_management",
                "description": "Consistently meeting deadlines",
                "score": 0.9,
            })

        if performance["average_estimation_accuracy"] > 0.8:
            performance["strengths"].append({
                "area": "estimation",
                "description": "Accurate task estimation",
                "score": performance["average_estimation_accuracy"],
            })

        # Identify improvement areas
        if performance["productivity_trend"] == "declining":
            performance["areas_for_improvement"].append({
                "area": "productivity",
                "description": "Productivity has been declining",
                "severity": "medium",
            })

        # Add context-specific insights
        if context.event and context.event.event_type == EventType.TASK_COMPLETED:
            task = context.task
            if task:
                if task.actual_hours and task.estimated_hours:
                    accuracy = 1 - abs(task.actual_hours - task.estimated_hours) / task.estimated_hours
                    performance["last_task"] = {
                        "title": task.title,
                        "estimation_accuracy": round(accuracy, 2),
                        "was_on_time": task.status == "completed",
                    }

        return performance

    async def _identify_skill_gaps(self, context: AgentContext) -> List[Dict[str, Any]]:
        """Identify skill gaps based on performance and goals"""
        gaps = []

        user = context.user
        user_skills = user.skills if user else []

        # In production, this would analyze blocked tasks, slow completions, etc.

        # Mock skill gap analysis
        common_gaps = [
            {
                "skill": "python",
                "current_level": 0.6,
                "target_level": 0.8,
                "gap_severity": "medium",
                "reason": "Recent tasks required advanced Python patterns",
                "impact": "Some tasks taking longer than expected",
            },
            {
                "skill": "testing",
                "current_level": 0.4,
                "target_level": 0.7,
                "gap_severity": "high",
                "reason": "Test coverage on recent tasks below standard",
                "impact": "Quality issues in code reviews",
            },
        ]

        # Filter based on user's actual skill needs
        if user_skills:
            gaps = [g for g in common_gaps if g["skill"] not in user_skills]
        else:
            gaps = common_gaps[:1]  # Return at least one gap for demo

        return gaps

    async def _generate_feedback(
        self,
        context: AgentContext,
        performance: Dict[str, Any],
        skill_gaps: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Generate personalized feedback"""
        feedback = {
            "summary": "",
            "highlights": [],
            "improvements": [],
            "tone": self.feedback_style,
        }

        # Build highlights based on strengths
        for strength in performance.get("strengths", []):
            feedback["highlights"].append({
                "area": strength["area"],
                "message": f"Excellent work on {strength['description'].lower()}!",
                "emoji": self._get_emoji(strength["area"]),
            })

        # Build improvement suggestions
        for gap in skill_gaps:
            feedback["improvements"].append({
                "area": gap["skill"],
                "message": f"Consider focusing on {gap['skill']} - {gap['reason'].lower()}",
                "priority": gap["gap_severity"],
            })

        # Generate summary
        if self.feedback_style == "supportive":
            if performance["strengths"]:
                summary = f"Great progress! You've {performance['strengths'][0]['description'].lower()}. "
            else:
                summary = "You're making steady progress. "

            if skill_gaps:
                summary += f"I noticed an opportunity to strengthen your {skill_gaps[0]['skill']} skills."
            else:
                summary += "Keep up the excellent work!"

        elif self.feedback_style == "direct":
            completed = performance["tasks_completed"]
            on_time = performance["tasks_on_time"]
            summary = f"Completed {completed} tasks ({on_time} on time). "

            if skill_gaps:
                summary += f"Focus area: {skill_gaps[0]['skill']}."
            else:
                summary += "All key skills on track."

        else:  # balanced
            summary = f"You've completed {performance['tasks_completed']} tasks this period. "
            if performance["strengths"]:
                summary += f"Strengths: {performance['strengths'][0]['area']}. "
            if skill_gaps:
                summary += f"Growth area: {skill_gaps[0]['skill']}."

        feedback["summary"] = summary

        return feedback

    def _get_emoji(self, area: str) -> str:
        """Get relevant emoji for feedback area"""
        emoji_map = {
            "time_management": "⏰",
            "estimation": "📊",
            "productivity": "🚀",
            "quality": "✨",
            "collaboration": "🤝",
            "learning": "📚",
            "default": "💪",
        }
        return emoji_map.get(area, emoji_map["default"])

    async def _suggest_resources(
        self,
        skill_gaps: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """Suggest learning resources for skill gaps"""
        resources = []

        resource_library = {
            "python": [
                {
                    "title": "Python Advanced Patterns",
                    "type": "course",
                    "provider": "internal_training",
                    "duration": "4 hours",
                    "url": "/learning/python-advanced",
                },
                {
                    "title": "Clean Code in Python",
                    "type": "book",
                    "provider": "library",
                    "duration": "2 weeks",
                    "url": "/library/clean-code-python",
                },
            ],
            "testing": [
                {
                    "title": "Test-Driven Development Workshop",
                    "type": "workshop",
                    "provider": "internal_training",
                    "duration": "2 hours",
                    "url": "/learning/tdd-workshop",
                },
                {
                    "title": "pytest Mastery",
                    "type": "course",
                    "provider": "external",
                    "duration": "3 hours",
                    "url": "https://example.com/pytest",
                },
            ],
            "devops": [
                {
                    "title": "Docker & Kubernetes Fundamentals",
                    "type": "course",
                    "provider": "internal_training",
                    "duration": "6 hours",
                    "url": "/learning/docker-k8s",
                },
            ],
            "javascript": [
                {
                    "title": "Modern JavaScript Patterns",
                    "type": "course",
                    "provider": "internal_training",
                    "duration": "3 hours",
                    "url": "/learning/modern-js",
                },
            ],
        }

        for gap in skill_gaps:
            skill = gap["skill"]
            if skill in resource_library:
                for resource in resource_library[skill][:2]:
                    resources.append({
                        **resource,
                        "skill": skill,
                        "relevance": "high" if gap["gap_severity"] == "high" else "medium",
                    })

        return resources

    def _generate_action_items(
        self,
        performance: Dict[str, Any],
        skill_gaps: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """Generate actionable items for improvement"""
        actions = []

        # Skill-based actions
        for gap in skill_gaps[:2]:
            actions.append({
                "title": f"Improve {gap['skill']} skills",
                "description": f"Complete one learning resource for {gap['skill']} this week",
                "priority": gap["gap_severity"],
                "deadline": "end_of_week",
                "type": "learning",
            })

        # Performance-based actions
        for area in performance.get("areas_for_improvement", []):
            actions.append({
                "title": f"Address {area['area']}",
                "description": area["description"],
                "priority": area["severity"],
                "deadline": "ongoing",
                "type": "behavior",
            })

        # General growth actions
        if performance["streak_days"] > 3:
            actions.append({
                "title": "Maintain your streak",
                "description": f"You're on a {performance['streak_days']}-day streak! Keep the momentum going.",
                "priority": "low",
                "deadline": "daily",
                "type": "motivation",
            })

        return actions

    def _generate_encouragement(self, performance: Dict[str, Any]) -> str:
        """Generate encouraging message based on performance"""
        messages = {
            "improving": [
                "You're on an upward trajectory! Keep pushing forward.",
                "Great momentum! Your dedication is showing results.",
                "Impressive improvement! You're growing every day.",
            ],
            "stable": [
                "Consistent performance is valuable. You're doing well!",
                "Steady progress leads to lasting success. Keep it up!",
                "You're maintaining a solid foundation. Nice work!",
            ],
            "declining": [
                "Everyone has challenging periods. Focus on one thing at a time.",
                "Tomorrow is a new opportunity. You've got this!",
                "Take a breath. Small steps forward still count as progress.",
            ],
        }

        trend = performance.get("productivity_trend", "stable")
        import random
        return random.choice(messages.get(trend, messages["stable"]))

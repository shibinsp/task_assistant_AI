"""
Skill Matcher Agent

AI-powered agent that matches tasks to best-suited team members
based on skill requirements, availability, and workload balance.
"""

import logging
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


class SkillMatcherAgent(BaseAgent):
    """
    Agent that matches tasks to optimal team members.

    Considers:
    - Required skills vs team member skills
    - Current workload and capacity
    - Learning opportunities
    - Historical performance on similar tasks
    """

    name = "skill_matcher_agent"
    description = "Matches tasks to best-suited team members based on skills and availability"
    version = "1.0.0"

    capabilities = [
        AgentCapability.SKILL_MATCHING,
    ]

    handled_events = [
        EventType.TASK_CREATED,
        EventType.TASK_ASSIGNED,
        EventType.USER_COMMAND,
    ]

    priority = 55

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        super().__init__(config)
        self.consider_learning = config.get("consider_learning", True) if config else True
        self.max_suggestions = config.get("max_suggestions", 5) if config else 5

    async def can_handle(self, event: AgentEvent) -> bool:
        """Check if skill matching is needed"""
        if event.event_type == EventType.USER_COMMAND:
            command = event.payload.get("command", "")
            return command.lower() in ["assign", "who should", "best for", "recommend assignee"]

        if event.event_type == EventType.TASK_CREATED:
            # Only if task doesn't have an assignee
            payload = event.payload or {}
            return payload.get("assignee_id") is None

        if event.event_type == EventType.TASK_ASSIGNED:
            # Provide feedback on assignment quality
            return True

        return False

    async def execute(self, context: AgentContext) -> AgentResult:
        """Find best team member matches for the task"""
        result = AgentResult(
            success=True,
            agent_name=self.name,
            event_id=context.event.id if context.event else "direct"
        )

        try:
            if not context.task:
                result.success = False
                result.error = "No task provided for skill matching"
                return result

            # Extract required skills from task
            required_skills = await self._extract_required_skills(context)

            # Get team members with their skills
            team_members = await self._get_team_members(context)

            # Calculate match scores
            matches = await self._calculate_matches(
                required_skills, team_members, context
            )

            # Sort by score
            matches.sort(key=lambda x: x["score"], reverse=True)

            # Get workload data
            workload = await self._get_workload_data(context, matches)

            result.output = {
                "task_id": context.task.id,
                "required_skills": required_skills,
                "matches": matches[:self.max_suggestions],
                "workload_analysis": workload,
                "recommendation": self._generate_recommendation(matches, workload),
            }

            if matches:
                best = matches[0]
                result.message = (
                    f"Best match for '{context.task.title}': {best['name']} "
                    f"(skill match: {best['score']*100:.0f}%). "
                    f"{len(matches)-1} other suitable team members available."
                )
            else:
                result.message = "No suitable team members found for this task's skill requirements."

            context.add_message(
                result.message,
                role=MessageRole.AGENT,
                agent_name=self.name,
            )

            result.actions = [
                {"type": "skills_analyzed", "count": len(required_skills)},
                {"type": "matches_found", "count": len(matches)},
            ]

        except Exception as e:
            logger.error(f"Skill matcher agent error: {e}")
            result.success = False
            result.error = str(e)

        return result

    async def _extract_required_skills(self, context: AgentContext) -> List[Dict[str, Any]]:
        """Extract required skills from task"""
        task = context.task
        skills = []

        # Skill keyword mapping
        skill_keywords = {
            "python": {
                "keywords": ["python", "django", "flask", "fastapi", "pytest"],
                "category": "backend",
                "level": "intermediate"
            },
            "javascript": {
                "keywords": ["javascript", "js", "node", "npm", "typescript", "ts"],
                "category": "frontend",
                "level": "intermediate"
            },
            "react": {
                "keywords": ["react", "redux", "hooks", "jsx", "component"],
                "category": "frontend",
                "level": "intermediate"
            },
            "database": {
                "keywords": ["sql", "database", "postgres", "mysql", "mongodb", "query"],
                "category": "data",
                "level": "intermediate"
            },
            "devops": {
                "keywords": ["docker", "kubernetes", "k8s", "ci/cd", "deploy", "aws", "gcp", "azure"],
                "category": "infrastructure",
                "level": "intermediate"
            },
            "api": {
                "keywords": ["api", "rest", "graphql", "endpoint", "integration"],
                "category": "backend",
                "level": "beginner"
            },
            "testing": {
                "keywords": ["test", "testing", "qa", "unit test", "e2e", "automation"],
                "category": "quality",
                "level": "beginner"
            },
            "security": {
                "keywords": ["security", "auth", "authentication", "encryption", "oauth"],
                "category": "security",
                "level": "advanced"
            },
            "machine_learning": {
                "keywords": ["ml", "machine learning", "ai", "model", "training", "tensorflow", "pytorch"],
                "category": "data_science",
                "level": "advanced"
            },
        }

        text = f"{task.title} {task.description or ''}".lower()

        for skill_name, skill_info in skill_keywords.items():
            if any(kw in text for kw in skill_info["keywords"]):
                # Determine importance based on keyword frequency
                matches = sum(1 for kw in skill_info["keywords"] if kw in text)
                importance = "required" if matches > 1 else "preferred"

                skills.append({
                    "name": skill_name,
                    "category": skill_info["category"],
                    "level": skill_info["level"],
                    "importance": importance,
                    "matched_keywords": [kw for kw in skill_info["keywords"] if kw in text],
                })

        # Add from task tags
        for tag in task.tags:
            if tag.lower() not in [s["name"] for s in skills]:
                skills.append({
                    "name": tag.lower(),
                    "category": "general",
                    "level": "intermediate",
                    "importance": "preferred",
                    "matched_keywords": [tag],
                })

        return skills

    async def _get_team_members(self, context: AgentContext) -> List[Dict[str, Any]]:
        """Get team members with their skills"""
        # In production, this would query the database
        # For now, return mock team members

        team_members = [
            {
                "id": "user_1",
                "name": "Alice Chen",
                "email": "alice@company.com",
                "role": "Senior Developer",
                "skills": [
                    {"name": "python", "level": 0.9, "category": "backend"},
                    {"name": "api", "level": 0.85, "category": "backend"},
                    {"name": "database", "level": 0.8, "category": "data"},
                    {"name": "testing", "level": 0.7, "category": "quality"},
                ],
                "current_load": 0.6,  # 60% capacity used
                "availability": "available",
            },
            {
                "id": "user_2",
                "name": "Bob Smith",
                "email": "bob@company.com",
                "role": "Full Stack Developer",
                "skills": [
                    {"name": "javascript", "level": 0.85, "category": "frontend"},
                    {"name": "react", "level": 0.9, "category": "frontend"},
                    {"name": "python", "level": 0.7, "category": "backend"},
                    {"name": "api", "level": 0.75, "category": "backend"},
                ],
                "current_load": 0.4,
                "availability": "available",
            },
            {
                "id": "user_3",
                "name": "Carol Williams",
                "email": "carol@company.com",
                "role": "DevOps Engineer",
                "skills": [
                    {"name": "devops", "level": 0.95, "category": "infrastructure"},
                    {"name": "python", "level": 0.6, "category": "backend"},
                    {"name": "security", "level": 0.8, "category": "security"},
                ],
                "current_load": 0.8,
                "availability": "busy",
            },
            {
                "id": "user_4",
                "name": "David Lee",
                "email": "david@company.com",
                "role": "Junior Developer",
                "skills": [
                    {"name": "javascript", "level": 0.6, "category": "frontend"},
                    {"name": "react", "level": 0.5, "category": "frontend"},
                    {"name": "testing", "level": 0.4, "category": "quality"},
                ],
                "current_load": 0.3,
                "availability": "available",
            },
            {
                "id": "user_5",
                "name": "Emma Davis",
                "email": "emma@company.com",
                "role": "Data Engineer",
                "skills": [
                    {"name": "python", "level": 0.85, "category": "backend"},
                    {"name": "database", "level": 0.95, "category": "data"},
                    {"name": "machine_learning", "level": 0.7, "category": "data_science"},
                ],
                "current_load": 0.5,
                "availability": "available",
            },
        ]

        return team_members

    async def _calculate_matches(
        self,
        required_skills: List[Dict[str, Any]],
        team_members: List[Dict[str, Any]],
        context: AgentContext
    ) -> List[Dict[str, Any]]:
        """Calculate match scores for each team member"""
        matches = []

        for member in team_members:
            match_details = self._calculate_member_match(required_skills, member)

            # Apply workload penalty
            workload_factor = 1 - (member["current_load"] * 0.3)
            adjusted_score = match_details["skill_score"] * workload_factor

            # Consider learning opportunity
            learning_bonus = 0
            if self.consider_learning and match_details["growth_skills"]:
                learning_bonus = 0.05 * len(match_details["growth_skills"])

            final_score = min(1.0, adjusted_score + learning_bonus)

            matches.append({
                "id": member["id"],
                "name": member["name"],
                "email": member["email"],
                "role": member["role"],
                "score": round(final_score, 2),
                "skill_match": match_details,
                "current_load": member["current_load"],
                "availability": member["availability"],
                "growth_opportunity": len(match_details["growth_skills"]) > 0,
            })

        return matches

    def _calculate_member_match(
        self,
        required_skills: List[Dict[str, Any]],
        member: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Calculate skill match for a single member"""
        if not required_skills:
            return {
                "skill_score": 0.5,
                "matched_skills": [],
                "missing_skills": [],
                "growth_skills": [],
            }

        member_skills = {s["name"]: s["level"] for s in member["skills"]}
        matched = []
        missing = []
        growth = []

        for req in required_skills:
            skill_name = req["name"]
            member_level = member_skills.get(skill_name, 0)

            if member_level > 0.6:
                matched.append({
                    "skill": skill_name,
                    "member_level": member_level,
                    "importance": req["importance"],
                })
            elif member_level > 0.3:
                growth.append({
                    "skill": skill_name,
                    "member_level": member_level,
                    "importance": req["importance"],
                })
            else:
                if req["importance"] == "required":
                    missing.append(skill_name)

        # Calculate score
        total_weight = sum(
            2 if r["importance"] == "required" else 1
            for r in required_skills
        )

        matched_weight = sum(
            (2 if m["importance"] == "required" else 1) * m["member_level"]
            for m in matched
        )

        skill_score = matched_weight / total_weight if total_weight > 0 else 0.5

        return {
            "skill_score": round(skill_score, 2),
            "matched_skills": matched,
            "missing_skills": missing,
            "growth_skills": growth,
        }

    async def _get_workload_data(
        self,
        context: AgentContext,
        matches: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Get workload analysis for top matches"""
        analysis = {
            "average_load": 0,
            "available_count": 0,
            "busy_count": 0,
            "overloaded": [],
        }

        if not matches:
            return analysis

        loads = [m["current_load"] for m in matches[:5]]
        analysis["average_load"] = sum(loads) / len(loads)
        analysis["available_count"] = sum(1 for m in matches[:5] if m["availability"] == "available")
        analysis["busy_count"] = sum(1 for m in matches[:5] if m["availability"] != "available")
        analysis["overloaded"] = [m["name"] for m in matches[:5] if m["current_load"] > 0.8]

        return analysis

    def _generate_recommendation(
        self,
        matches: List[Dict[str, Any]],
        workload: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Generate assignment recommendation"""
        if not matches:
            return {
                "assign_to": None,
                "reason": "No suitable matches found",
                "confidence": 0,
                "alternatives": [],
            }

        best = matches[0]
        alternatives = matches[1:3] if len(matches) > 1 else []

        # Determine confidence based on score gap
        score_gap = (best["score"] - matches[1]["score"]) if len(matches) > 1 else 0.3
        confidence = min(0.95, best["score"] + score_gap)

        reasons = []
        if best["skill_match"]["matched_skills"]:
            top_skills = [s["skill"] for s in best["skill_match"]["matched_skills"][:3]]
            reasons.append(f"Strong skills in {', '.join(top_skills)}")

        if best["current_load"] < 0.5:
            reasons.append("Good availability")

        if best["growth_opportunity"]:
            reasons.append("Learning opportunity")

        return {
            "assign_to": {
                "id": best["id"],
                "name": best["name"],
                "email": best["email"],
            },
            "reason": "; ".join(reasons) if reasons else "Best overall match",
            "confidence": round(confidence, 2),
            "alternatives": [
                {"id": a["id"], "name": a["name"], "score": a["score"]}
                for a in alternatives
            ],
            "consider_alternatives_if": [
                "Primary assignee becomes unavailable",
                "Task requires more expertise than estimated",
                "Workload balance needed",
            ],
        }

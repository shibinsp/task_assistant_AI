"""
Decomposer Agent

AI-powered agent that breaks complex tasks into manageable subtasks.
Analyzes task complexity, generates subtasks with estimates, and
assigns skill requirements.
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


class DecomposerAgent(BaseAgent):
    """
    Agent that decomposes complex tasks into subtasks.

    Analyzes task description and complexity to generate:
    - Ordered list of subtasks
    - Time estimates for each
    - Skill requirements
    - Dependencies between subtasks
    """

    name = "decomposer_agent"
    description = "Breaks complex tasks into manageable subtasks with estimates"
    version = "1.0.0"

    capabilities = [
        AgentCapability.TASK_DECOMPOSITION,
        AgentCapability.NATURAL_LANGUAGE,
    ]

    handled_events = [
        EventType.TASK_CREATED,
        EventType.USER_COMMAND,
    ]

    priority = 50

    # Thresholds for auto-decomposition
    AUTO_DECOMPOSE_HOURS = 8  # Auto-decompose tasks > 8 hours
    MAX_SUBTASKS = 10
    MIN_SUBTASK_HOURS = 0.5

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        super().__init__(config)
        self.auto_decompose = config.get("auto_decompose", True) if config else True
        self.min_hours_threshold = config.get("min_hours", self.AUTO_DECOMPOSE_HOURS) if config else self.AUTO_DECOMPOSE_HOURS

    async def can_handle(self, event: AgentEvent) -> bool:
        """Check if task needs decomposition"""
        if event.event_type == EventType.USER_COMMAND:
            command = event.payload.get("command", "")
            return command.lower() in ["decompose", "break down", "split task"]

        if event.event_type == EventType.TASK_CREATED:
            if not self.auto_decompose:
                return False
            # Check if task is complex enough to warrant decomposition
            payload = event.payload or {}
            estimated_hours = payload.get("estimated_hours", 0)
            return estimated_hours >= self.min_hours_threshold

        return False

    async def execute(self, context: AgentContext) -> AgentResult:
        """Decompose the task into subtasks"""
        result = AgentResult(
            success=True,
            agent_name=self.name,
            event_id=context.event.id if context.event else "direct"
        )

        try:
            if not context.task:
                result.success = False
                result.error = "No task provided for decomposition"
                return result

            # Analyze task complexity
            complexity = await self._analyze_complexity(context)

            # Generate subtasks
            subtasks = await self._generate_subtasks(context, complexity)

            # Identify dependencies
            dependencies = self._identify_dependencies(subtasks)

            # Calculate total estimates
            totals = self._calculate_totals(subtasks)

            result.output = {
                "original_task": {
                    "id": context.task.id,
                    "title": context.task.title,
                    "estimated_hours": context.task.estimated_hours,
                },
                "complexity_analysis": complexity,
                "subtasks": subtasks,
                "dependencies": dependencies,
                "totals": totals,
                "recommendation": self._generate_recommendation(complexity, subtasks),
            }

            result.message = (
                f"I've broken down '{context.task.title}' into {len(subtasks)} subtasks. "
                f"Total estimated time: {totals['total_hours']} hours."
            )

            context.add_message(
                result.message,
                role=MessageRole.AGENT,
                agent_name=self.name,
            )

            result.actions = [
                {"type": "task_analyzed", "complexity": complexity["level"]},
                {"type": "subtasks_generated", "count": len(subtasks)},
            ]

            # Store subtasks for potential creation
            context.set_chain_data("proposed_subtasks", subtasks)

        except Exception as e:
            logger.error(f"Decomposer agent error: {e}")
            result.success = False
            result.error = str(e)

        return result

    async def _analyze_complexity(self, context: AgentContext) -> Dict[str, Any]:
        """Analyze task complexity"""
        task = context.task
        description = task.description or ""
        title = task.title

        # Complexity factors
        factors = {
            "size": self._assess_size(task.estimated_hours),
            "technical_depth": self._assess_technical_depth(description),
            "ambiguity": self._assess_ambiguity(description),
            "dependencies": self._assess_dependencies(description),
            "skills_required": self._extract_skills(description, title),
        }

        # Calculate overall complexity
        scores = [
            factors["size"]["score"],
            factors["technical_depth"]["score"],
            factors["ambiguity"]["score"],
            factors["dependencies"]["score"],
        ]
        avg_score = sum(scores) / len(scores)

        level = "simple" if avg_score < 0.4 else "moderate" if avg_score < 0.7 else "complex"

        return {
            "level": level,
            "score": round(avg_score, 2),
            "factors": factors,
            "recommended_subtasks": self._recommended_subtask_count(avg_score, task.estimated_hours),
        }

    def _assess_size(self, hours: Optional[float]) -> Dict[str, Any]:
        """Assess task size based on hours"""
        if not hours:
            return {"score": 0.5, "label": "unknown", "hours": 0}

        if hours < 4:
            return {"score": 0.2, "label": "small", "hours": hours}
        elif hours < 16:
            return {"score": 0.5, "label": "medium", "hours": hours}
        elif hours < 40:
            return {"score": 0.7, "label": "large", "hours": hours}
        else:
            return {"score": 0.9, "label": "very_large", "hours": hours}

    def _assess_technical_depth(self, description: str) -> Dict[str, Any]:
        """Assess technical complexity from description"""
        technical_keywords = [
            "algorithm", "architecture", "database", "security", "performance",
            "integration", "migration", "optimization", "scalability", "api",
            "authentication", "encryption", "deployment", "infrastructure"
        ]

        desc_lower = description.lower()
        matches = [kw for kw in technical_keywords if kw in desc_lower]
        score = min(len(matches) / 5, 1.0)

        return {
            "score": score,
            "indicators": matches[:5],
            "label": "low" if score < 0.3 else "medium" if score < 0.6 else "high"
        }

    def _assess_ambiguity(self, description: str) -> Dict[str, Any]:
        """Assess how well-defined the task is"""
        if not description:
            return {"score": 0.8, "label": "high", "reason": "No description provided"}

        # Indicators of clear requirements
        clarity_indicators = [
            "must", "should", "will", "specific", "exactly",
            "requirement", "criteria", "acceptance"
        ]

        # Indicators of ambiguity
        ambiguity_indicators = [
            "maybe", "might", "could", "possibly", "tbd",
            "unclear", "figure out", "investigate", "research"
        ]

        desc_lower = description.lower()
        clarity_count = sum(1 for i in clarity_indicators if i in desc_lower)
        ambiguity_count = sum(1 for i in ambiguity_indicators if i in desc_lower)

        if clarity_count > ambiguity_count:
            score = max(0.2, 0.5 - (clarity_count - ambiguity_count) * 0.1)
        else:
            score = min(0.9, 0.5 + (ambiguity_count - clarity_count) * 0.1)

        return {
            "score": score,
            "label": "low" if score < 0.4 else "medium" if score < 0.7 else "high"
        }

    def _assess_dependencies(self, description: str) -> Dict[str, Any]:
        """Assess external dependencies"""
        dependency_indicators = [
            "depends on", "requires", "after", "before", "blocked by",
            "waiting for", "pending", "prerequisite", "external"
        ]

        desc_lower = description.lower()
        matches = [i for i in dependency_indicators if i in desc_lower]
        score = min(len(matches) / 3, 1.0)

        return {
            "score": score,
            "indicators": matches,
            "label": "few" if score < 0.3 else "some" if score < 0.6 else "many"
        }

    def _extract_skills(self, description: str, title: str) -> List[str]:
        """Extract required skills from task"""
        skill_keywords = {
            "python": ["python", "django", "flask", "fastapi"],
            "javascript": ["javascript", "js", "node", "react", "vue", "angular"],
            "database": ["sql", "database", "postgres", "mysql", "mongodb"],
            "devops": ["docker", "kubernetes", "ci/cd", "deploy", "aws", "gcp"],
            "api": ["api", "rest", "graphql", "endpoint"],
            "frontend": ["frontend", "ui", "ux", "css", "html"],
            "backend": ["backend", "server", "microservice"],
            "testing": ["test", "testing", "qa", "automation"],
        }

        text = f"{title} {description}".lower()
        skills = []

        for skill, keywords in skill_keywords.items():
            if any(kw in text for kw in keywords):
                skills.append(skill)

        return skills

    def _recommended_subtask_count(
        self,
        complexity_score: float,
        hours: Optional[float]
    ) -> int:
        """Calculate recommended number of subtasks"""
        if not hours:
            return 3

        # Base on hours with complexity adjustment
        base_count = int(hours / 4)  # One subtask per 4 hours
        complexity_adjustment = int(complexity_score * 3)

        count = base_count + complexity_adjustment
        return max(2, min(count, self.MAX_SUBTASKS))

    async def _generate_subtasks(
        self,
        context: AgentContext,
        complexity: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """Generate subtasks based on task analysis"""
        task = context.task
        target_count = complexity["recommended_subtasks"]

        # In production, this would use AI to generate contextual subtasks
        # For now, generate template-based subtasks

        subtasks = []
        total_hours = task.estimated_hours or 8
        hours_per_task = total_hours / target_count

        # Common task patterns
        patterns = self._get_task_patterns(task.title, task.description or "")

        for i, pattern in enumerate(patterns[:target_count]):
            subtask = {
                "order": i + 1,
                "title": pattern["title"],
                "description": pattern["description"],
                "estimated_hours": round(
                    hours_per_task * pattern.get("weight", 1.0),
                    1
                ),
                "skills_required": pattern.get("skills", []),
                "priority": pattern.get("priority", "medium"),
                "type": pattern.get("type", "development"),
            }
            subtasks.append(subtask)

        # Ensure we have enough subtasks
        while len(subtasks) < target_count:
            subtasks.append({
                "order": len(subtasks) + 1,
                "title": f"Additional work item {len(subtasks) + 1}",
                "description": "Complete remaining tasks",
                "estimated_hours": round(hours_per_task, 1),
                "skills_required": complexity["factors"]["skills_required"],
                "priority": "medium",
                "type": "development",
            })

        return subtasks

    def _get_task_patterns(
        self,
        title: str,
        description: str
    ) -> List[Dict[str, Any]]:
        """Get task patterns based on title and description"""
        text = f"{title} {description}".lower()
        patterns = []

        # Feature development pattern
        if any(kw in text for kw in ["feature", "implement", "add", "create", "build"]):
            patterns = [
                {
                    "title": "Requirements analysis and design",
                    "description": "Analyze requirements and create technical design",
                    "weight": 0.15,
                    "skills": ["analysis"],
                    "type": "planning",
                    "priority": "high",
                },
                {
                    "title": "Set up development environment",
                    "description": "Configure necessary tools and dependencies",
                    "weight": 0.1,
                    "skills": ["devops"],
                    "type": "setup",
                },
                {
                    "title": "Implement core functionality",
                    "description": "Build the main feature logic",
                    "weight": 0.35,
                    "skills": ["development"],
                    "type": "development",
                    "priority": "high",
                },
                {
                    "title": "Write unit tests",
                    "description": "Create comprehensive test coverage",
                    "weight": 0.15,
                    "skills": ["testing"],
                    "type": "testing",
                },
                {
                    "title": "Integration and documentation",
                    "description": "Integrate with existing system and document",
                    "weight": 0.15,
                    "skills": ["development"],
                    "type": "documentation",
                },
                {
                    "title": "Code review and refinement",
                    "description": "Address review feedback and polish",
                    "weight": 0.1,
                    "skills": ["development"],
                    "type": "review",
                },
            ]

        # Bug fix pattern
        elif any(kw in text for kw in ["bug", "fix", "issue", "error", "broken"]):
            patterns = [
                {
                    "title": "Reproduce and investigate issue",
                    "description": "Reproduce the bug and identify root cause",
                    "weight": 0.25,
                    "skills": ["debugging"],
                    "type": "investigation",
                    "priority": "high",
                },
                {
                    "title": "Implement fix",
                    "description": "Apply the necessary code changes",
                    "weight": 0.35,
                    "skills": ["development"],
                    "type": "development",
                    "priority": "high",
                },
                {
                    "title": "Add regression tests",
                    "description": "Create tests to prevent recurrence",
                    "weight": 0.2,
                    "skills": ["testing"],
                    "type": "testing",
                },
                {
                    "title": "Verify and deploy",
                    "description": "Test fix and deploy to production",
                    "weight": 0.2,
                    "skills": ["devops"],
                    "type": "deployment",
                },
            ]

        # API/Integration pattern
        elif any(kw in text for kw in ["api", "integration", "connect", "sync"]):
            patterns = [
                {
                    "title": "API design and documentation",
                    "description": "Design API contract and document endpoints",
                    "weight": 0.15,
                    "skills": ["api"],
                    "type": "planning",
                },
                {
                    "title": "Implement endpoints",
                    "description": "Build API endpoints with validation",
                    "weight": 0.35,
                    "skills": ["backend", "api"],
                    "type": "development",
                    "priority": "high",
                },
                {
                    "title": "Add authentication/authorization",
                    "description": "Implement security controls",
                    "weight": 0.15,
                    "skills": ["backend", "security"],
                    "type": "development",
                },
                {
                    "title": "Write API tests",
                    "description": "Create integration tests for endpoints",
                    "weight": 0.2,
                    "skills": ["testing"],
                    "type": "testing",
                },
                {
                    "title": "Client integration",
                    "description": "Integrate with consuming systems",
                    "weight": 0.15,
                    "skills": ["api"],
                    "type": "integration",
                },
            ]

        # Default pattern
        else:
            patterns = [
                {
                    "title": "Research and planning",
                    "description": "Understand requirements and plan approach",
                    "weight": 0.15,
                    "type": "planning",
                },
                {
                    "title": "Implementation phase 1",
                    "description": "Initial development work",
                    "weight": 0.3,
                    "type": "development",
                    "priority": "high",
                },
                {
                    "title": "Implementation phase 2",
                    "description": "Complete remaining development",
                    "weight": 0.25,
                    "type": "development",
                },
                {
                    "title": "Testing and validation",
                    "description": "Test and validate implementation",
                    "weight": 0.2,
                    "type": "testing",
                },
                {
                    "title": "Finalization",
                    "description": "Final touches and documentation",
                    "weight": 0.1,
                    "type": "documentation",
                },
            ]

        return patterns

    def _identify_dependencies(
        self,
        subtasks: List[Dict[str, Any]]
    ) -> List[Dict[str, int]]:
        """Identify dependencies between subtasks"""
        dependencies = []

        # Simple sequential dependencies based on order
        for i in range(1, len(subtasks)):
            # Planning/setup tasks should be done first
            if subtasks[i-1].get("type") in ["planning", "setup"]:
                dependencies.append({
                    "from": i,  # 0-indexed
                    "to": i + 1,
                    "type": "must_complete_before"
                })

            # Testing depends on implementation
            if (subtasks[i].get("type") == "testing" and
                subtasks[i-1].get("type") == "development"):
                dependencies.append({
                    "from": i,
                    "to": i + 1,
                    "type": "must_complete_before"
                })

        return dependencies

    def _calculate_totals(
        self,
        subtasks: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Calculate totals across all subtasks"""
        total_hours = sum(s.get("estimated_hours", 0) for s in subtasks)
        all_skills = set()
        for s in subtasks:
            all_skills.update(s.get("skills_required", []))

        types = {}
        for s in subtasks:
            t = s.get("type", "other")
            types[t] = types.get(t, 0) + s.get("estimated_hours", 0)

        return {
            "total_hours": round(total_hours, 1),
            "subtask_count": len(subtasks),
            "unique_skills": list(all_skills),
            "hours_by_type": types,
            "average_hours_per_subtask": round(total_hours / len(subtasks), 1) if subtasks else 0,
        }

    def _generate_recommendation(
        self,
        complexity: Dict[str, Any],
        subtasks: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Generate recommendation for task execution"""
        high_priority = [s for s in subtasks if s.get("priority") == "high"]

        return {
            "approach": "sequential" if complexity["level"] == "complex" else "parallel_possible",
            "start_with": subtasks[0]["title"] if subtasks else None,
            "critical_path": [s["title"] for s in high_priority],
            "parallelizable": [
                s["title"] for s in subtasks
                if s.get("type") in ["testing", "documentation"]
            ],
            "suggested_team_size": 1 if complexity["score"] < 0.5 else 2,
        }

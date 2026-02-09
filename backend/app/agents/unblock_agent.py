"""
Unblock Agent

AI-powered agent that helps stuck employees by providing:
- RAG-powered contextual assistance
- Knowledge base search
- Teammate suggestions
- Step-by-step guidance
- Escalation recommendations
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


class UnblockAgent(BaseAgent):
    """
    Agent that helps unblock stuck employees.

    Uses RAG to search knowledge base, suggests relevant teammates,
    and provides step-by-step guidance based on the blocker context.
    """

    name = "unblock_agent"
    description = "Helps stuck employees with AI-powered suggestions and guidance"
    version = "1.0.0"

    capabilities = [
        AgentCapability.UNBLOCK_ASSISTANCE,
        AgentCapability.NATURAL_LANGUAGE,
    ]

    handled_events = [
        EventType.TASK_BLOCKED,
        EventType.USER_STUCK,
        EventType.CHECKIN_RESPONSE,
    ]

    priority = 10  # High priority for blocking issues

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        super().__init__(config)
        self.max_suggestions = config.get("max_suggestions", 5) if config else 5
        self.include_teammates = config.get("include_teammates", True) if config else True
        self.escalation_threshold = config.get("escalation_threshold", 3) if config else 3

    async def can_handle(self, event: AgentEvent) -> bool:
        """Check if this event indicates someone is stuck"""
        if event.event_type == EventType.TASK_BLOCKED:
            return True

        if event.event_type == EventType.USER_STUCK:
            return True

        if event.event_type == EventType.CHECKIN_RESPONSE:
            # Check if response indicates struggle
            payload = event.payload or {}
            sentiment = payload.get("sentiment", "")
            progress = payload.get("progress_percent", 100)
            return sentiment in ["negative", "frustrated"] or progress < 20

        return False

    async def execute(self, context: AgentContext) -> AgentResult:
        """Provide unblock assistance"""
        result = AgentResult(
            success=True,
            agent_name=self.name,
            event_id=context.event.id if context.event else "direct"
        )

        try:
            # Extract blocker information
            blocker_info = await self._extract_blocker_info(context)

            # Search knowledge base for relevant solutions
            kb_results = await self._search_knowledge_base(context, blocker_info)

            # Find relevant teammates who can help
            teammates = []
            if self.include_teammates:
                teammates = await self._find_helpful_teammates(context, blocker_info)

            # Generate AI suggestion
            suggestion = await self._generate_suggestion(
                context, blocker_info, kb_results, teammates
            )

            # Determine if escalation is needed
            escalation = await self._check_escalation(context, blocker_info)

            # Build response
            result.output = {
                "blocker_summary": blocker_info.get("summary", ""),
                "suggestion": suggestion,
                "knowledge_base_results": kb_results[:self.max_suggestions],
                "suggested_teammates": teammates[:3],
                "escalation": escalation,
                "confidence_score": self._calculate_confidence(kb_results),
            }

            result.message = suggestion.get("summary", "Here are some suggestions to help you.")

            # Add response to conversation
            context.add_message(
                result.message,
                role=MessageRole.AGENT,
                agent_name=self.name,
                metadata={"type": "unblock_suggestion"}
            )

            result.actions = [
                {"type": "suggestion_provided", "count": len(kb_results)},
                {"type": "teammates_suggested", "count": len(teammates)},
            ]

            if escalation.get("recommended"):
                result.actions.append({
                    "type": "escalation_recommended",
                    "to": escalation.get("escalate_to")
                })

        except Exception as e:
            logger.error(f"Unblock agent error: {e}")
            result.success = False
            result.error = str(e)
            result.message = "I encountered an issue while finding help. Let me connect you with your team lead."

        return result

    async def _extract_blocker_info(
        self,
        context: AgentContext
    ) -> Dict[str, Any]:
        """Extract structured information about the blocker"""
        info = {
            "summary": "",
            "category": "unknown",
            "keywords": [],
            "attempted_solutions": [],
            "time_stuck": None,
        }

        # From event payload
        if context.event and context.event.payload:
            payload = context.event.payload
            info["summary"] = payload.get("blocker_description", "")
            info["category"] = payload.get("blocker_category", "unknown")
            info["time_stuck"] = payload.get("hours_stuck")

        # From task
        if context.task:
            if context.task.blockers:
                info["summary"] = info["summary"] or context.task.blockers[0]
            info["keywords"].extend(context.task.tags)

        # From conversation
        if context.conversation_history:
            last_msg = context.get_last_message()
            if last_msg and last_msg.role == MessageRole.USER:
                if not info["summary"]:
                    info["summary"] = last_msg.content
                # Extract keywords from message
                info["keywords"].extend(
                    self._extract_keywords(last_msg.content)
                )

        return info

    def _extract_keywords(self, text: str) -> List[str]:
        """Extract potential keywords from text"""
        # Simple keyword extraction - in production, use NLP
        stop_words = {
            "i", "am", "is", "are", "the", "a", "an", "and", "or", "but",
            "in", "on", "at", "to", "for", "of", "with", "by", "from",
            "this", "that", "these", "those", "my", "your", "it", "its"
        }
        words = text.lower().split()
        return [
            w.strip(".,!?;:") for w in words
            if w.lower() not in stop_words and len(w) > 3
        ]

    async def _search_knowledge_base(
        self,
        context: AgentContext,
        blocker_info: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """Search knowledge base for relevant solutions"""
        results = []

        # In production, this would use the UnblockService RAG
        # For now, return mock results based on keywords
        keywords = blocker_info.get("keywords", [])
        summary = blocker_info.get("summary", "")

        if context.db:
            # Would query actual knowledge base
            pass

        # Mock results for demonstration
        if any(kw in summary.lower() for kw in ["api", "endpoint", "request"]):
            results.append({
                "title": "API Integration Guide",
                "content": "Check authentication headers and request format...",
                "relevance": 0.92,
                "source": "internal_wiki",
                "link": "/docs/api-guide"
            })

        if any(kw in summary.lower() for kw in ["database", "query", "sql"]):
            results.append({
                "title": "Database Troubleshooting",
                "content": "Common database issues and solutions...",
                "relevance": 0.88,
                "source": "internal_wiki",
                "link": "/docs/db-troubleshooting"
            })

        if any(kw in summary.lower() for kw in ["deploy", "build", "ci", "cd"]):
            results.append({
                "title": "Deployment Pipeline Guide",
                "content": "Step-by-step deployment troubleshooting...",
                "relevance": 0.85,
                "source": "runbook",
                "link": "/docs/deployment"
            })

        # Default helpful resources
        if not results:
            results.append({
                "title": "General Troubleshooting Guide",
                "content": "Start by checking logs and recent changes...",
                "relevance": 0.6,
                "source": "internal_wiki",
                "link": "/docs/troubleshooting"
            })

        return results

    async def _find_helpful_teammates(
        self,
        context: AgentContext,
        blocker_info: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """Find teammates who might be able to help"""
        teammates = []

        # In production, this would query the skill graph and user history
        keywords = blocker_info.get("keywords", [])

        # Mock teammate suggestions
        if any(kw in str(keywords).lower() for kw in ["api", "backend", "python"]):
            teammates.append({
                "name": "Alex Chen",
                "email": "alex@company.com",
                "skill_match": 0.95,
                "reason": "Expert in API development, solved similar issue last week",
                "availability": "available"
            })

        if any(kw in str(keywords).lower() for kw in ["frontend", "react", "ui"]):
            teammates.append({
                "name": "Sarah Kim",
                "email": "sarah@company.com",
                "skill_match": 0.88,
                "reason": "Frontend specialist with React expertise",
                "availability": "in_meeting"
            })

        if any(kw in str(keywords).lower() for kw in ["devops", "deploy", "kubernetes"]):
            teammates.append({
                "name": "Mike Johnson",
                "email": "mike@company.com",
                "skill_match": 0.92,
                "reason": "DevOps lead, handles all deployment issues",
                "availability": "available"
            })

        return teammates

    async def _generate_suggestion(
        self,
        context: AgentContext,
        blocker_info: Dict[str, Any],
        kb_results: List[Dict[str, Any]],
        teammates: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Generate AI-powered suggestion"""
        # In production, this would call the AI service
        summary = blocker_info.get("summary", "your issue")

        suggestion = {
            "summary": f"Based on your description about {summary[:50]}..., here's what I recommend:",
            "steps": [],
            "resources": [],
            "estimated_time": "30-60 minutes",
        }

        # Generate steps based on context
        suggestion["steps"] = [
            {
                "order": 1,
                "action": "Review the error logs for specific error messages",
                "details": "Check both application and system logs"
            },
            {
                "order": 2,
                "action": "Compare with recent changes",
                "details": "Check git history for changes in the affected area"
            },
        ]

        if kb_results:
            suggestion["steps"].append({
                "order": 3,
                "action": f"Review: {kb_results[0]['title']}",
                "details": kb_results[0].get("content", "")[:200],
                "link": kb_results[0].get("link")
            })

        if teammates:
            available = [t for t in teammates if t.get("availability") == "available"]
            if available:
                suggestion["steps"].append({
                    "order": len(suggestion["steps"]) + 1,
                    "action": f"Reach out to {available[0]['name']}",
                    "details": available[0].get("reason", "They can help with this"),
                    "contact": available[0].get("email")
                })

        suggestion["resources"] = [
            {"title": r["title"], "link": r.get("link")}
            for r in kb_results[:3]
        ]

        return suggestion

    async def _check_escalation(
        self,
        context: AgentContext,
        blocker_info: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Determine if escalation is needed"""
        escalation = {
            "recommended": False,
            "reason": None,
            "escalate_to": None,
            "urgency": "normal"
        }

        time_stuck = blocker_info.get("time_stuck")
        if time_stuck and time_stuck >= self.escalation_threshold:
            escalation["recommended"] = True
            escalation["reason"] = f"Blocked for {time_stuck} hours"
            escalation["escalate_to"] = "team_lead"
            escalation["urgency"] = "high" if time_stuck > 6 else "normal"

        # Check task priority
        if context.task and context.task.priority in ["critical", "high"]:
            if time_stuck and time_stuck >= 1:
                escalation["recommended"] = True
                escalation["reason"] = "High priority task blocked"
                escalation["urgency"] = "high"

        return escalation

    def _calculate_confidence(self, kb_results: List[Dict[str, Any]]) -> float:
        """Calculate confidence score for suggestions"""
        if not kb_results:
            return 0.3

        avg_relevance = sum(r.get("relevance", 0.5) for r in kb_results) / len(kb_results)
        return min(0.95, avg_relevance + 0.1 * min(len(kb_results), 3))

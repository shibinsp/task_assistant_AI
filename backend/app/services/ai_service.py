"""
TaskPulse - AI Assistant - AI Service
AI integration with mock responses (switchable to OpenAI/Claude)
"""

import json
import hashlib
import random
from typing import Optional, List, Dict, Any
from datetime import datetime, timedelta
from dataclasses import dataclass
from enum import Enum

from app.config import settings


class AIProvider(str, Enum):
    """Supported AI providers."""
    MOCK = "mock"
    OPENAI = "openai"
    ANTHROPIC = "anthropic"
    MISTRAL = "mistral"
    KIMI = "kimi"


@dataclass
class AIResponse:
    """Standardized AI response."""
    content: str
    model: str
    provider: str
    tokens_used: int
    cached: bool = False
    confidence: float = 0.9
    processing_time_ms: int = 0


class AICache:
    """Simple in-memory cache for AI responses."""

    def __init__(self, ttl_seconds: int = 3600):
        self._cache: Dict[str, tuple] = {}  # key -> (response, timestamp)
        self.ttl = timedelta(seconds=ttl_seconds)

    def _make_key(self, prompt: str, context: str = "") -> str:
        """Generate cache key from prompt."""
        content = f"{prompt}:{context}"
        return hashlib.md5(content.encode()).hexdigest()

    def get(self, prompt: str, context: str = "") -> Optional[AIResponse]:
        """Get cached response if exists and not expired."""
        key = self._make_key(prompt, context)
        if key in self._cache:
            response, timestamp = self._cache[key]
            if datetime.utcnow() - timestamp < self.ttl:
                response.cached = True
                return response
            else:
                del self._cache[key]
        return None

    def set(self, prompt: str, response: AIResponse, context: str = "") -> None:
        """Cache a response."""
        key = self._make_key(prompt, context)
        self._cache[key] = (response, datetime.utcnow())

    def clear(self) -> None:
        """Clear all cached responses."""
        self._cache.clear()


class MockAIProvider:
    """Mock AI provider for development and testing."""

    DECOMPOSITION_TEMPLATES = [
        {
            "subtasks": [
                {"title": "Research and gather requirements", "hours": 2.0, "skills": ["analysis", "communication"]},
                {"title": "Design solution architecture", "hours": 3.0, "skills": ["architecture", "design"]},
                {"title": "Implement core functionality", "hours": 8.0, "skills": ["coding", "testing"]},
                {"title": "Write unit tests", "hours": 4.0, "skills": ["testing", "quality assurance"]},
                {"title": "Code review and refinement", "hours": 2.0, "skills": ["code review"]},
                {"title": "Documentation and handoff", "hours": 1.0, "skills": ["documentation"]}
            ],
            "complexity": 0.6,
            "risk_factors": ["Dependencies on external systems", "Unclear requirements"],
            "recommendations": ["Break into smaller PRs", "Add integration tests"]
        },
        {
            "subtasks": [
                {"title": "Analyze current implementation", "hours": 1.5, "skills": ["analysis"]},
                {"title": "Create implementation plan", "hours": 1.0, "skills": ["planning"]},
                {"title": "Develop feature", "hours": 6.0, "skills": ["coding"]},
                {"title": "Test and validate", "hours": 3.0, "skills": ["testing"]},
                {"title": "Deploy and monitor", "hours": 1.5, "skills": ["devops"]}
            ],
            "complexity": 0.4,
            "risk_factors": ["Potential regression issues"],
            "recommendations": ["Run full test suite before merging"]
        }
    ]

    UNBLOCK_SUGGESTIONS = [
        {
            "suggestion": "Based on the error you're seeing, try checking the following:\n1. Verify the configuration file exists at the expected path\n2. Ensure environment variables are properly set\n3. Check file permissions",
            "confidence": 0.85,
            "sources": ["internal_docs", "stack_overflow"]
        },
        {
            "suggestion": "This issue typically occurs due to a race condition. Consider:\n1. Adding proper synchronization\n2. Using async/await patterns\n3. Implementing retry logic with exponential backoff",
            "confidence": 0.78,
            "sources": ["internal_docs"]
        },
        {
            "suggestion": "The dependency conflict can be resolved by:\n1. Checking version compatibility\n2. Using virtual environments\n3. Updating to the latest stable version",
            "confidence": 0.82,
            "sources": ["documentation", "internal_wiki"]
        }
    ]

    SKILL_SUGGESTIONS = [
        {"skill": "Python", "confidence": 0.9},
        {"skill": "FastAPI", "confidence": 0.85},
        {"skill": "SQL", "confidence": 0.8},
        {"skill": "REST APIs", "confidence": 0.75},
        {"skill": "Testing", "confidence": 0.7}
    ]

    def __init__(self):
        self.model = "mock-ai-v1"
        self.provider = AIProvider.MOCK.value

    async def generate(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 1000
    ) -> AIResponse:
        """Generate a mock response."""
        # Simulate processing time
        import asyncio
        await asyncio.sleep(0.1)

        # Generate contextual response based on prompt keywords
        content = self._generate_contextual_response(prompt)

        return AIResponse(
            content=content,
            model=self.model,
            provider=self.provider,
            tokens_used=len(prompt.split()) + len(content.split()),
            processing_time_ms=100
        )

    def _generate_contextual_response(self, prompt: str) -> str:
        """Generate response based on prompt content."""
        prompt_lower = prompt.lower()

        if "decompose" in prompt_lower or "subtask" in prompt_lower:
            template = random.choice(self.DECOMPOSITION_TEMPLATES)
            return json.dumps(template)

        if "unblock" in prompt_lower or "stuck" in prompt_lower or "help" in prompt_lower:
            suggestion = random.choice(self.UNBLOCK_SUGGESTIONS)
            return json.dumps(suggestion)

        if "skill" in prompt_lower:
            return json.dumps(self.SKILL_SUGGESTIONS)

        # Default response
        return json.dumps({
            "response": "I understand your request. Here's my analysis and suggestions based on the context provided.",
            "confidence": 0.75
        })

    async def decompose_task(
        self,
        title: str,
        description: str,
        goal: Optional[str] = None,
        max_subtasks: int = 10
    ) -> Dict[str, Any]:
        """Decompose a task into subtasks."""
        template = random.choice(self.DECOMPOSITION_TEMPLATES)

        # Limit subtasks
        subtasks = template["subtasks"][:max_subtasks]

        # Calculate total hours
        total_hours = sum(s["hours"] for s in subtasks)

        return {
            "subtasks": [
                {
                    "title": s["title"],
                    "description": f"Part of: {title}",
                    "estimated_hours": s["hours"],
                    "skills_required": s["skills"],
                    "order": i + 1
                }
                for i, s in enumerate(subtasks)
            ],
            "total_estimated_hours": total_hours,
            "complexity_score": template["complexity"],
            "risk_factors": template["risk_factors"],
            "recommendations": template["recommendations"]
        }

    async def get_unblock_suggestion(
        self,
        task_title: str,
        task_description: str,
        blocker_type: str,
        blocker_description: str,
        user_skill_level: str = "intermediate"
    ) -> Dict[str, Any]:
        """Get AI suggestion to unblock a task."""
        suggestion = random.choice(self.UNBLOCK_SUGGESTIONS)

        # Adjust detail level based on skill
        detail_level = {
            "junior": "detailed",
            "intermediate": "moderate",
            "senior": "concise"
        }.get(user_skill_level, "moderate")

        return {
            "suggestion": suggestion["suggestion"],
            "confidence": suggestion["confidence"],
            "sources": suggestion["sources"],
            "detail_level": detail_level,
            "escalation_recommended": suggestion["confidence"] < 0.7
        }

    async def infer_skills(
        self,
        task_title: str,
        task_description: str
    ) -> List[Dict[str, Any]]:
        """Infer required skills from task."""
        # Return subset of skills based on mock logic
        num_skills = random.randint(2, 5)
        return random.sample(self.SKILL_SUGGESTIONS, min(num_skills, len(self.SKILL_SUGGESTIONS)))


class MistralAIProvider:
    """Mistral AI provider for real AI responses."""

    def __init__(self):
        self.api_key = settings.MISTRAL_API_KEY
        self.model = settings.MISTRAL_MODEL
        self.provider = AIProvider.MISTRAL.value

    async def generate(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 1000
    ) -> AIResponse:
        """Generate response using Mistral AI."""
        import httpx
        import time

        start_time = time.time()

        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})

        async with httpx.AsyncClient() as client:
            response = await client.post(
                "https://api.mistral.ai/v1/chat/completions",
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json"
                },
                json={
                    "model": self.model,
                    "messages": messages,
                    "temperature": temperature,
                    "max_tokens": max_tokens
                },
                timeout=60.0
            )
            response.raise_for_status()
            data = response.json()

        content = data["choices"][0]["message"]["content"]
        tokens_used = data.get("usage", {}).get("total_tokens", 0)
        processing_time = int((time.time() - start_time) * 1000)

        return AIResponse(
            content=content,
            model=self.model,
            provider=self.provider,
            tokens_used=tokens_used,
            processing_time_ms=processing_time
        )

    async def decompose_task(
        self,
        title: str,
        description: str,
        goal: Optional[str] = None,
        max_subtasks: int = 10
    ) -> Dict[str, Any]:
        """Decompose a task into subtasks using Mistral AI."""
        system_prompt = """You are a project management AI assistant.
Analyze the given task and break it down into subtasks.
Return a JSON object with the following structure:
{
    "subtasks": [
        {"title": "string", "description": "string", "estimated_hours": number, "skills_required": ["string"], "order": number}
    ],
    "total_estimated_hours": number,
    "complexity_score": number (0-1),
    "risk_factors": ["string"],
    "recommendations": ["string"]
}
Return ONLY valid JSON, no additional text."""

        prompt = f"""Task Title: {title}
Description: {description}
{f'Goal: {goal}' if goal else ''}

Break this task into up to {max_subtasks} subtasks."""

        response = await self.generate(prompt, system_prompt, temperature=0.3)

        try:
            return json.loads(response.content)
        except json.JSONDecodeError:
            # Fallback to mock if parsing fails
            return MockAIProvider().DECOMPOSITION_TEMPLATES[0]

    async def get_unblock_suggestion(
        self,
        task_title: str,
        task_description: str,
        blocker_type: str,
        blocker_description: str,
        user_skill_level: str = "intermediate"
    ) -> Dict[str, Any]:
        """Get AI suggestion to unblock a task using Mistral."""
        detail_map = {
            "junior": "very detailed with step-by-step explanations",
            "intermediate": "moderately detailed",
            "senior": "concise and to the point"
        }
        detail_level = detail_map.get(user_skill_level, "moderately detailed")

        system_prompt = f"""You are a helpful technical assistant.
Provide suggestions to help unblock a task. Be {detail_level}.
Return a JSON object with:
{{
    "suggestion": "string with actionable advice",
    "confidence": number (0-1),
    "sources": ["internal_docs", "documentation", etc],
    "escalation_recommended": boolean
}}
Return ONLY valid JSON."""

        prompt = f"""Task: {task_title}
Description: {task_description}
Blocker Type: {blocker_type}
Blocker Description: {blocker_description}

Provide a suggestion to help unblock this task."""

        response = await self.generate(prompt, system_prompt, temperature=0.5)

        try:
            result = json.loads(response.content)
            result["detail_level"] = user_skill_level
            return result
        except json.JSONDecodeError:
            return MockAIProvider().UNBLOCK_SUGGESTIONS[0]

    async def infer_skills(
        self,
        task_title: str,
        task_description: str
    ) -> List[Dict[str, Any]]:
        """Infer skills from task using Mistral AI."""
        system_prompt = """Analyze the task and identify required skills.
Return a JSON array of skills:
[{"skill": "string", "confidence": number (0-1)}]
Return ONLY valid JSON array."""

        prompt = f"""Task: {task_title}
Description: {task_description}

What skills are required for this task?"""

        response = await self.generate(prompt, system_prompt, temperature=0.3)

        try:
            return json.loads(response.content)
        except json.JSONDecodeError:
            return MockAIProvider().SKILL_SUGGESTIONS


class KimiAIProvider:
    """Kimi/Moonshot AI provider (OpenAI-compatible API)."""

    def __init__(self):
        self.api_key = settings.KIMI_API_KEY
        self.model = settings.KIMI_MODEL
        self.base_url = settings.KIMI_BASE_URL
        self.provider = AIProvider.KIMI.value

    async def generate(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 1000
    ) -> AIResponse:
        """Generate response using Kimi/Moonshot AI."""
        import httpx
        import time

        start_time = time.time()

        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})

        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.base_url}/chat/completions",
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json"
                },
                json={
                    "model": self.model,
                    "messages": messages,
                    "temperature": temperature,
                    "max_tokens": max_tokens
                },
                timeout=60.0
            )
            response.raise_for_status()
            data = response.json()

        content = data["choices"][0]["message"]["content"]
        tokens_used = data.get("usage", {}).get("total_tokens", 0)
        processing_time = int((time.time() - start_time) * 1000)

        return AIResponse(
            content=content,
            model=self.model,
            provider=self.provider,
            tokens_used=tokens_used,
            processing_time_ms=processing_time
        )

    async def decompose_task(
        self,
        title: str,
        description: str,
        goal: Optional[str] = None,
        max_subtasks: int = 10
    ) -> Dict[str, Any]:
        """Decompose a task into subtasks using Kimi AI."""
        system_prompt = """You are a project management AI assistant.
Analyze the given task and break it down into subtasks.
Return a JSON object with the following structure:
{
    "subtasks": [
        {"title": "string", "description": "string", "estimated_hours": number, "skills_required": ["string"], "order": number}
    ],
    "total_estimated_hours": number,
    "complexity_score": number (0-1),
    "risk_factors": ["string"],
    "recommendations": ["string"]
}
Return ONLY valid JSON, no additional text."""

        prompt = f"""Task Title: {title}
Description: {description}
{f'Goal: {goal}' if goal else ''}

Break this task into up to {max_subtasks} subtasks."""

        response = await self.generate(prompt, system_prompt, temperature=0.3)

        try:
            return json.loads(response.content)
        except json.JSONDecodeError:
            return MockAIProvider().DECOMPOSITION_TEMPLATES[0]

    async def get_unblock_suggestion(
        self,
        task_title: str,
        task_description: str,
        blocker_type: str,
        blocker_description: str,
        user_skill_level: str = "intermediate"
    ) -> Dict[str, Any]:
        """Get AI suggestion to unblock a task using Kimi."""
        detail_map = {
            "junior": "very detailed with step-by-step explanations",
            "intermediate": "moderately detailed",
            "senior": "concise and to the point"
        }
        detail_level = detail_map.get(user_skill_level, "moderately detailed")

        system_prompt = f"""You are a helpful technical assistant.
Provide suggestions to help unblock a task. Be {detail_level}.
Return a JSON object with:
{{
    "suggestion": "string with actionable advice",
    "confidence": number (0-1),
    "sources": ["internal_docs", "documentation", etc],
    "escalation_recommended": boolean
}}
Return ONLY valid JSON."""

        prompt = f"""Task: {task_title}
Description: {task_description}
Blocker Type: {blocker_type}
Blocker Description: {blocker_description}

Provide a suggestion to help unblock this task."""

        response = await self.generate(prompt, system_prompt, temperature=0.5)

        try:
            result = json.loads(response.content)
            result["detail_level"] = user_skill_level
            return result
        except json.JSONDecodeError:
            return MockAIProvider().UNBLOCK_SUGGESTIONS[0]

    async def infer_skills(
        self,
        task_title: str,
        task_description: str
    ) -> List[Dict[str, Any]]:
        """Infer skills from task using Kimi AI."""
        system_prompt = """Analyze the task and identify required skills.
Return a JSON array of skills:
[{"skill": "string", "confidence": number (0-1)}]
Return ONLY valid JSON array."""

        prompt = f"""Task: {task_title}
Description: {task_description}

What skills are required for this task?"""

        response = await self.generate(prompt, system_prompt, temperature=0.3)

        try:
            return json.loads(response.content)
        except json.JSONDecodeError:
            return MockAIProvider().SKILL_SUGGESTIONS


class AIService:
    """Main AI service with provider abstraction and caching."""

    def __init__(self):
        self.cache = AICache(ttl_seconds=settings.AI_CACHE_TTL)
        self._init_provider()

    def _init_provider(self):
        """Initialize the appropriate AI provider."""
        provider = settings.AI_PROVIDER.lower()

        if provider == AIProvider.KIMI.value and settings.KIMI_API_KEY:
            self.provider = KimiAIProvider()
        elif provider == AIProvider.MISTRAL.value and settings.MISTRAL_API_KEY:
            self.provider = MistralAIProvider()
        elif provider == AIProvider.OPENAI.value and settings.OPENAI_API_KEY:
            self.provider = MockAIProvider()
        elif provider == AIProvider.ANTHROPIC.value and settings.ANTHROPIC_API_KEY:
            self.provider = MockAIProvider()
        else:
            self.provider = MockAIProvider()

    async def generate(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        use_cache: bool = True,
        temperature: float = 0.7,
        max_tokens: int = 1000
    ) -> AIResponse:
        """Generate AI response with optional caching."""
        context = system_prompt or ""

        # Check cache
        if use_cache:
            cached = self.cache.get(prompt, context)
            if cached:
                return cached

        # Generate response
        response = await self.provider.generate(
            prompt, system_prompt, temperature, max_tokens
        )

        # Cache response
        if use_cache:
            self.cache.set(prompt, response, context)

        return response

    async def decompose_task(
        self,
        title: str,
        description: str,
        goal: Optional[str] = None,
        max_subtasks: int = 10,
        include_time_estimates: bool = True,
        include_skill_requirements: bool = True
    ) -> Dict[str, Any]:
        """Decompose a task into subtasks using AI."""
        return await self.provider.decompose_task(
            title, description, goal, max_subtasks
        )

    async def get_unblock_suggestion(
        self,
        task_title: str,
        task_description: str,
        blocker_type: str,
        blocker_description: str,
        user_skill_level: str = "intermediate",
        context: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """Get AI-powered suggestion to unblock a task."""
        return await self.provider.get_unblock_suggestion(
            task_title, task_description,
            blocker_type, blocker_description,
            user_skill_level
        )

    async def infer_skills(
        self,
        task_title: str,
        task_description: str
    ) -> List[Dict[str, Any]]:
        """Infer skills from task using AI."""
        return await self.provider.infer_skills(task_title, task_description)

    async def analyze_sentiment(self, text: str) -> Dict[str, Any]:
        """Analyze sentiment of text (e.g., check-in responses)."""
        # Mock sentiment analysis
        sentiments = ["positive", "neutral", "negative", "frustrated", "confident"]
        return {
            "sentiment": random.choice(sentiments),
            "confidence": random.uniform(0.7, 0.95),
            "indicators": ["tone", "word_choice"]
        }

    async def generate_summary(
        self,
        items: List[str],
        max_length: int = 200
    ) -> str:
        """Generate a summary of multiple items."""
        # Mock summary
        if not items:
            return "No items to summarize."

        return f"Summary of {len(items)} items: Key points include progress updates, blockers addressed, and upcoming milestones."

    def clear_cache(self) -> None:
        """Clear the AI response cache."""
        self.cache.clear()


# Singleton instance
_ai_service: Optional[AIService] = None


def get_ai_service() -> AIService:
    """Get or create the AI service singleton."""
    global _ai_service
    if _ai_service is None:
        _ai_service = AIService()
    return _ai_service

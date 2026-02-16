"""
TaskPulse - AI Assistant - AI Service
AI integration with mock responses (switchable to OpenAI/Claude)
"""

import json
import hashlib
import logging
import random
import re
from collections import OrderedDict
from typing import Optional, List, Dict, Any
from datetime import datetime, timedelta
from dataclasses import dataclass
from enum import Enum

from app.config import settings

logger = logging.getLogger(__name__)


class AIProvider(str, Enum):
    """Supported AI providers."""
    MOCK = "mock"
    OPENAI = "openai"
    ANTHROPIC = "anthropic"
    MISTRAL = "mistral"
    KIMI = "kimi"
    OLLAMA = "ollama"


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
    """
    In-memory cache for AI responses with LRU eviction and SHA-256 keys.
    SEC-009: Uses SHA-256 instead of MD5 for cache key generation.
    SEC-010: Bounded cache with configurable max size and LRU eviction.
    """

    def __init__(self, ttl_seconds: int = 3600, max_size: int = 1000):
        self._cache: OrderedDict[str, tuple] = OrderedDict()
        self.ttl = timedelta(seconds=ttl_seconds)
        self.max_size = max_size

    def _make_key(self, prompt: str, context: str = "") -> str:
        """Generate cache key from prompt using SHA-256."""
        content = f"{prompt}:{context}"
        return hashlib.sha256(content.encode()).hexdigest()

    def get(self, prompt: str, context: str = "") -> Optional[AIResponse]:
        """Get cached response if exists and not expired."""
        key = self._make_key(prompt, context)
        if key in self._cache:
            response, timestamp = self._cache[key]
            if datetime.utcnow() - timestamp < self.ttl:
                # Move to end (most recently used)
                self._cache.move_to_end(key)
                response.cached = True
                return response
            else:
                del self._cache[key]
        return None

    def set(self, prompt: str, response: AIResponse, context: str = "") -> None:
        """Cache a response with LRU eviction."""
        key = self._make_key(prompt, context)
        # If key already exists, remove it first so it goes to end
        if key in self._cache:
            del self._cache[key]
        self._cache[key] = (response, datetime.utcnow())
        # Evict oldest entries if over max size
        while len(self._cache) > self.max_size:
            self._cache.popitem(last=False)

    def clear(self) -> None:
        """Clear all cached responses."""
        self._cache.clear()

    @property
    def size(self) -> int:
        """Return current cache size."""
        return len(self._cache)


# SEC-004: Input sanitization for prompt injection defense
def sanitize_user_input(text: str, max_length: int = 10000) -> str:
    """
    Sanitize user-provided text before including it in AI prompts.
    Strips control characters and known injection patterns.
    """
    if not text:
        return ""

    # Truncate to max length
    text = text[:max_length]

    # Remove null bytes and control characters (except newlines and tabs)
    text = re.sub(r'[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]', '', text)

    # Strip common prompt injection markers
    injection_patterns = [
        r'(?i)ignore\s+(all\s+)?(previous|above|prior)\s+(instructions|prompts|rules)',
        r'(?i)you\s+are\s+now\s+(a|an|the)\s+',
        r'(?i)system\s*:\s*',
        r'(?i)###\s*(system|instruction|override)',
        r'(?i)<\|?(system|im_start|im_end)\|?>',
    ]

    for pattern in injection_patterns:
        text = re.sub(pattern, '[filtered]', text)

    return text.strip()


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

        # Intent classification requests — return a valid intent word
        if "classify" in prompt_lower and ("category" in prompt_lower or "one of these" in prompt_lower):
            if any(w in prompt_lower for w in ["build", "create", "develop", "implement", "task"]):
                return "smart_create_task"
            if any(w in prompt_lower for w in ["stuck", "blocked", "error", "bug"]):
                return "blocker_help"
            if any(w in prompt_lower for w in ["progress", "on track", "% done"]):
                return "checkin_response"
            return "general"

        # Task parsing requests — return structured JSON
        if "parse" in prompt_lower and "task" in prompt_lower:
            return json.dumps({
                "title": "New Task",
                "description": prompt[:200],
                "deadline": None,
                "work_start_hour": 9,
                "work_end_hour": 18,
                "estimated_hours": None,
                "priority": "medium",
                "tags": [],
                "skills_required": [],
            })

        if "decompose" in prompt_lower or "subtask" in prompt_lower:
            template = random.choice(self.DECOMPOSITION_TEMPLATES)
            return json.dumps(template)

        if "unblock" in prompt_lower or "stuck" in prompt_lower or "help" in prompt_lower:
            suggestion = random.choice(self.UNBLOCK_SUGGESTIONS)
            return json.dumps(suggestion)

        if "skill" in prompt_lower:
            return json.dumps(self.SKILL_SUGGESTIONS)

        # Default conversational response
        responses = [
            "I can help you with task management, tracking progress, and getting unblocked. Try saying something like:\n\n- **\"I need to build X by Y\"** to create a task\n- **\"my tasks\"** to see your task list\n- **\"I'm stuck\"** to get help with blockers\n- **\"how am I doing\"** to check your status\n\nWhat would you like to do?",
            "I'm your AI assistant for task management! I can create tasks, break them into subtasks, track your progress, and help when you're stuck. What can I help you with?",
            "Here's what I can do for you:\n\n- Create and manage tasks with AI-powered decomposition\n- Track your progress with check-ins\n- Help you get unblocked with AI suggestions\n- Show your performance overview\n\nJust describe what you need!",
        ]
        return random.choice(responses)

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

        # SEC-004: Sanitize user inputs before including in prompts
        safe_title = sanitize_user_input(title, max_length=500)
        safe_description = sanitize_user_input(description, max_length=5000)
        safe_goal = sanitize_user_input(goal, max_length=1000) if goal else None

        prompt = f"""Task Title: {safe_title}
Description: {safe_description}
{f'Goal: {safe_goal}' if safe_goal else ''}

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

        # SEC-004: Sanitize user inputs before including in prompts
        safe_title = sanitize_user_input(task_title, max_length=500)
        safe_description = sanitize_user_input(task_description, max_length=5000)
        safe_blocker_type = sanitize_user_input(blocker_type, max_length=200)
        safe_blocker_desc = sanitize_user_input(blocker_description, max_length=5000)

        prompt = f"""Task: {safe_title}
Description: {safe_description}
Blocker Type: {safe_blocker_type}
Blocker Description: {safe_blocker_desc}

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

        # SEC-004: Sanitize user inputs
        safe_title = sanitize_user_input(task_title, max_length=500)
        safe_description = sanitize_user_input(task_description, max_length=5000)

        prompt = f"""Task: {safe_title}
Description: {safe_description}

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

        # SEC-004: Sanitize user inputs
        safe_title = sanitize_user_input(title, max_length=500)
        safe_description = sanitize_user_input(description, max_length=5000)
        safe_goal = sanitize_user_input(goal, max_length=1000) if goal else None

        prompt = f"""Task Title: {safe_title}
Description: {safe_description}
{f'Goal: {safe_goal}' if safe_goal else ''}

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

        # SEC-004: Sanitize user inputs
        safe_title = sanitize_user_input(task_title, max_length=500)
        safe_description = sanitize_user_input(task_description, max_length=5000)
        safe_blocker_type = sanitize_user_input(blocker_type, max_length=200)
        safe_blocker_desc = sanitize_user_input(blocker_description, max_length=5000)

        prompt = f"""Task: {safe_title}
Description: {safe_description}
Blocker Type: {safe_blocker_type}
Blocker Description: {safe_blocker_desc}

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

        safe_title = sanitize_user_input(task_title, max_length=500)
        safe_description = sanitize_user_input(task_description, max_length=5000)

        prompt = f"""Task: {safe_title}
Description: {safe_description}

What skills are required for this task?"""

        response = await self.generate(prompt, system_prompt, temperature=0.3)

        try:
            return json.loads(response.content)
        except json.JSONDecodeError:
            return MockAIProvider().SKILL_SUGGESTIONS


class OllamaAIProvider:
    """Ollama AI provider (OpenAI-compatible local API)."""

    def __init__(self):
        self.base_url = settings.OLLAMA_BASE_URL
        self.model = settings.OLLAMA_MODEL
        self.provider = AIProvider.OLLAMA.value

    async def generate(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 1000
    ) -> AIResponse:
        """Generate response using Ollama."""
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
                headers={"Content-Type": "application/json"},
                json={
                    "model": self.model,
                    "messages": messages,
                    "temperature": temperature,
                    "max_tokens": max_tokens
                },
                timeout=120.0
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
        """Decompose a task into subtasks using Ollama."""
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

        safe_title = sanitize_user_input(title, max_length=500)
        safe_description = sanitize_user_input(description, max_length=5000)
        safe_goal = sanitize_user_input(goal, max_length=1000) if goal else None

        prompt = f"""Task Title: {safe_title}
Description: {safe_description}
{f'Goal: {safe_goal}' if safe_goal else ''}

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
        """Get AI suggestion to unblock a task using Ollama."""
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

        safe_title = sanitize_user_input(task_title, max_length=500)
        safe_description = sanitize_user_input(task_description, max_length=5000)
        safe_blocker_type = sanitize_user_input(blocker_type, max_length=200)
        safe_blocker_desc = sanitize_user_input(blocker_description, max_length=5000)

        prompt = f"""Task: {safe_title}
Description: {safe_description}
Blocker Type: {safe_blocker_type}
Blocker Description: {safe_blocker_desc}

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
        """Infer skills from task using Ollama."""
        system_prompt = """Analyze the task and identify required skills.
Return a JSON array of skills:
[{"skill": "string", "confidence": number (0-1)}]
Return ONLY valid JSON array."""

        safe_title = sanitize_user_input(task_title, max_length=500)
        safe_description = sanitize_user_input(task_description, max_length=5000)

        prompt = f"""Task: {safe_title}
Description: {safe_description}

What skills are required for this task?"""

        response = await self.generate(prompt, system_prompt, temperature=0.3)

        try:
            return json.loads(response.content)
        except json.JSONDecodeError:
            return MockAIProvider().SKILL_SUGGESTIONS


class AIService:
    """Main AI service with provider abstraction and caching."""

    def __init__(self):
        self.cache = AICache(
            ttl_seconds=settings.AI_CACHE_TTL,
            max_size=settings.AI_CACHE_MAX_SIZE
        )
        self._init_provider()

    def _init_provider(self):
        """Initialize the appropriate AI provider."""
        provider = settings.AI_PROVIDER.lower()

        if provider == AIProvider.OLLAMA.value:
            self.provider = OllamaAIProvider()
        elif provider == AIProvider.KIMI.value and settings.KIMI_API_KEY:
            self.provider = KimiAIProvider()
        elif provider == AIProvider.MISTRAL.value and settings.MISTRAL_API_KEY:
            self.provider = MistralAIProvider()
        elif provider == AIProvider.OPENAI.value:
            # SEC-013: Raise explicit error instead of silently falling back to mock
            if settings.OPENAI_API_KEY:
                raise NotImplementedError(
                    "OpenAI provider is not yet implemented. "
                    "Set AI_PROVIDER to 'mock', 'mistral', 'kimi', or 'ollama'."
                )
            logger.warning("OpenAI selected but no API key provided, falling back to mock.")
            self.provider = MockAIProvider()
        elif provider == AIProvider.ANTHROPIC.value:
            # SEC-013: Raise explicit error instead of silently falling back to mock
            if settings.ANTHROPIC_API_KEY:
                raise NotImplementedError(
                    "Anthropic provider is not yet implemented. "
                    "Set AI_PROVIDER to 'mock', 'mistral', 'kimi', or 'ollama'."
                )
            logger.warning("Anthropic selected but no API key provided, falling back to mock.")
            self.provider = MockAIProvider()
        else:
            self.provider = MockAIProvider()

        logger.info(f"AI provider initialized: {self.provider.provider} ({self.provider.model})")

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

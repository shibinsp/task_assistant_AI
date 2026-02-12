"""
TaskPulse - Smart Task Service
Coordinates AI-powered task creation with decomposition and check-in scheduling.
"""

import json
import logging
from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta

from sqlalchemy.ext.asyncio import AsyncSession

from app.services.task_service import TaskService
from app.services.ai_service import get_ai_service
from app.services.checkin_service import CheckInService
from app.schemas.task import TaskCreate, SubtaskCreate
from app.schemas.checkin import CheckInConfigCreate
from app.models.checkin import CheckInTrigger

logger = logging.getLogger(__name__)


class SmartTaskService:
    """Orchestrates intelligent task creation with AI decomposition and check-in setup."""

    def __init__(self, db: AsyncSession):
        self.db = db
        self.task_service = TaskService(db)
        self.ai_service = get_ai_service()
        self.checkin_service = CheckInService(db)

    async def parse_natural_language_task(self, message: str) -> Dict[str, Any]:
        """
        Use AI to parse a natural language message into structured task parameters.

        Args:
            message: Raw user message like "I need to build a payment API by Feb 15th, I work 10am-7pm"

        Returns:
            Dict with title, description, deadline, work hours, priority, etc.
        """
        today = datetime.utcnow().strftime("%Y-%m-%d")
        system_prompt = f"""You are a task management AI. Parse the user's message and extract task details.
Today's date is {today}.

Return ONLY a valid JSON object with these fields:
{{
    "title": "concise task title (max 100 chars)",
    "description": "detailed description of what needs to be done",
    "deadline": "ISO datetime string (YYYY-MM-DDTHH:MM:SS) or null if not mentioned",
    "work_start_hour": integer 0-23 (default 9 if not mentioned),
    "work_end_hour": integer 0-23 (default 18 if not mentioned),
    "estimated_hours": float or null,
    "priority": "low" or "medium" or "high" or "critical",
    "tags": ["relevant", "tags"],
    "skills_required": ["relevant", "skills"]
}}

Parse dates relative to today. If office hours are mentioned ("9am-6pm", "10 to 7"), extract them as 24-hour integers.
If deadline is a date without time, use end of day (23:59:00).
Return ONLY valid JSON, no extra text."""

        try:
            response = await self.ai_service.generate(
                prompt=f"Parse this task request: {message}",
                system_prompt=system_prompt,
                temperature=0.2,
                max_tokens=500,
                use_cache=False,
            )
            logger.debug(f"AI parse response: {response.content[:300]}")
            parsed = self._parse_json(response.content)
            if parsed and parsed.get("title"):
                return parsed
            logger.warning(f"AI returned invalid JSON, falling back to regex: {response.content[:200]}")
        except Exception as e:
            logger.warning(f"AI parsing failed: {e}")

        # Regex-based fallback extraction
        return self._regex_parse_task(message)

    async def create_smart_task(
        self,
        parsed_task: Dict[str, Any],
        org_id: str,
        user_id: str,
        auto_decompose: bool = True,
        schedule_checkins: bool = True,
    ) -> Dict[str, Any]:
        """
        Create a task with AI decomposition and check-in scheduling.

        Returns:
            Dict with task, subtasks, checkin_config, summary
        """
        # 1. Parse deadline
        deadline = None
        if parsed_task.get("deadline"):
            try:
                deadline = datetime.fromisoformat(parsed_task["deadline"])
            except (ValueError, TypeError):
                pass

        # 2. Create main task
        priority = parsed_task.get("priority", "medium")
        task_create = TaskCreate(
            title=parsed_task.get("title", "New Task"),
            description=parsed_task.get("description", ""),
            priority=priority,
            deadline=deadline,
            estimated_hours=parsed_task.get("estimated_hours"),
            assigned_to=user_id,
            tags=parsed_task.get("tags", []),
            skills_required=parsed_task.get("skills_required", []),
        )

        task = await self.task_service.create_task(task_create, org_id, user_id)
        logger.info(f"Smart task created: {task.id} - {task.title}")

        # 3. AI decompose into subtasks
        subtasks = []
        decomposition = None
        if auto_decompose:
            try:
                decomposition = await self.ai_service.decompose_task(
                    title=task.title,
                    description=task.description or "",
                    goal=task.goal,
                    max_subtasks=8,
                    include_time_estimates=True,
                )

                # Fit subtask hours within available work hours
                if deadline:
                    work_start = parsed_task.get("work_start_hour", 9)
                    work_end = parsed_task.get("work_end_hour", 18)
                    available = self._calculate_available_hours(
                        datetime.utcnow(), deadline, work_start, work_end
                    )
                    decomposition = self._fit_subtasks_to_hours(decomposition, available)

                # Create subtasks in DB
                for i, sub_data in enumerate(decomposition.get("subtasks", [])):
                    subtask_create = SubtaskCreate(
                        title=sub_data.get("title", f"Subtask {i+1}"),
                        description=sub_data.get("description", ""),
                        estimated_hours=sub_data.get("estimated_hours"),
                        sort_order=sub_data.get("order", i),
                    )
                    subtask = await self.task_service.create_subtask(
                        task.id, org_id, subtask_create, user_id
                    )
                    subtasks.append(subtask)

                logger.info(f"Created {len(subtasks)} subtasks for task {task.id}")
            except Exception as e:
                logger.warning(f"Decomposition failed: {e}")

        # 4. Schedule check-ins
        checkin_config = None
        first_checkin = None
        if schedule_checkins:
            try:
                work_start = parsed_task.get("work_start_hour", 9)
                work_end = parsed_task.get("work_end_hour", 18)
                max_daily = max(1, work_end - work_start)

                config_data = CheckInConfigCreate(
                    task_id=task.id,
                    interval_hours=1.0,
                    work_start_hour=work_start,
                    work_end_hour=work_end,
                    max_daily_checkins=min(max_daily, 10),
                    ai_suggestions_enabled=True,
                    ai_sentiment_analysis=True,
                )
                checkin_config = await self.checkin_service.create_config(org_id, config_data)

                # Create first check-in 1 hour from now (if within work hours)
                now = datetime.utcnow()
                next_checkin = now + timedelta(hours=1)
                if work_start <= next_checkin.hour < work_end:
                    first_checkin = await self.checkin_service.create_checkin(
                        org_id=org_id,
                        task_id=task.id,
                        user_id=user_id,
                        trigger=CheckInTrigger.SCHEDULED,
                        scheduled_at=next_checkin,
                        expires_hours=2.0,
                    )

                logger.info(f"Check-in config created for task {task.id}: hourly {work_start}:00-{work_end}:00")
            except Exception as e:
                logger.warning(f"Check-in setup failed: {e}")

        # 5. Build summary
        summary = self._build_summary(task, subtasks, decomposition, checkin_config, parsed_task)

        return {
            "task": task,
            "subtasks": subtasks,
            "decomposition": decomposition,
            "checkin_config": checkin_config,
            "first_checkin": first_checkin,
            "summary": summary,
        }

    def _calculate_available_hours(
        self,
        start_date: datetime,
        deadline: datetime,
        work_start: int,
        work_end: int,
    ) -> float:
        """Calculate total available work hours between now and deadline."""
        hours_per_day = max(1, work_end - work_start)
        total_days = max(0, (deadline - start_date).days)

        # Estimate work days (exclude weekends)
        work_days = 0
        current = start_date
        for _ in range(total_days):
            current += timedelta(days=1)
            if current.weekday() < 5:  # Monday-Friday
                work_days += 1

        return max(1.0, work_days * hours_per_day)

    def _fit_subtasks_to_hours(
        self,
        decomposition: Dict[str, Any],
        available_hours: float,
    ) -> Dict[str, Any]:
        """Scale subtask estimates to fit within available hours."""
        subtasks = decomposition.get("subtasks", [])
        total = decomposition.get("total_estimated_hours", 0)

        if total <= 0 or total <= available_hours:
            return decomposition

        # Scale down proportionally
        scale = available_hours / total
        for sub in subtasks:
            if sub.get("estimated_hours"):
                sub["estimated_hours"] = round(sub["estimated_hours"] * scale, 1)

        decomposition["total_estimated_hours"] = round(available_hours, 1)
        return decomposition

    def _build_summary(
        self,
        task,
        subtasks,
        decomposition,
        checkin_config,
        parsed_task,
    ) -> str:
        """Build a human-readable summary of what was created."""
        lines = [f"I've created your task: **{task.title}**\n"]

        if task.deadline:
            lines.append(f"**Deadline:** {task.deadline.strftime('%B %d, %Y')}")

        if task.priority:
            prio = task.priority.value if hasattr(task.priority, "value") else task.priority
            lines.append(f"**Priority:** {prio.capitalize()}")

        if subtasks:
            total_hours = sum(s.estimated_hours or 0 for s in subtasks)
            lines.append(f"\n**{len(subtasks)} subtasks** (~{total_hours:.1f} hours total):")
            for i, sub in enumerate(subtasks, 1):
                hours_str = f" (~{sub.estimated_hours}h)" if sub.estimated_hours else ""
                lines.append(f"  {i}. {sub.title}{hours_str}")

        if checkin_config:
            start = parsed_task.get("work_start_hour", 9)
            end = parsed_task.get("work_end_hour", 18)
            lines.append(
                f"\n**Hourly check-ins** scheduled during your work hours ({start}:00 - {end}:00)."
            )
            lines.append("I'll ask for your status every hour to keep things on track.")

        if decomposition and decomposition.get("recommendations"):
            lines.append("\n**Recommendations:**")
            for rec in decomposition["recommendations"][:3]:
                lines.append(f"- {rec}")

        return "\n".join(lines)

    def _regex_parse_task(self, message: str) -> Dict[str, Any]:
        """Regex-based fallback to extract task details when AI parsing fails."""
        import re

        title = message
        deadline = None
        work_start = 9
        work_end = 18

        # Extract title: everything before "by" / "before" / "deadline"
        title_match = re.match(
            r"(?:i need to |i want to |please |can you )?"
            r"((?:build|create|develop|implement|design|write|make|finish|complete|do|work on)\s+.+?)"
            r"(?:\s+by\s+|\s+before\s+|\s+deadline\s+|,\s+i work|$)",
            message, re.IGNORECASE,
        )
        if title_match:
            title = title_match.group(1).strip()
            # Capitalize first letter
            title = title[0].upper() + title[1:] if title else title

        # Extract deadline
        deadline_match = re.search(
            r"(?:by|before|deadline)\s+([\w\s,]+?\d{1,2}(?:st|nd|rd|th)?(?:\s*,?\s*\d{4})?)",
            message, re.IGNORECASE,
        )
        if deadline_match:
            from dateutil import parser as dateparser
            try:
                deadline = dateparser.parse(deadline_match.group(1), fuzzy=True)
                if deadline:
                    deadline = deadline.replace(hour=23, minute=59)
                    deadline = deadline.isoformat()
            except Exception:
                deadline = None

        # Extract work hours (e.g., "10am to 7pm", "10 to 7", "9am-6pm")
        hours_match = re.search(
            r"(\d{1,2})\s*(?:am|AM)?\s*(?:to|-)\s*(\d{1,2})\s*(?:pm|PM)?",
            message,
        )
        if hours_match:
            start_h = int(hours_match.group(1))
            end_h = int(hours_match.group(2))
            # Normalize: if start < 12 and end < 12 and end < start, end is PM
            if end_h < start_h and end_h < 12:
                end_h += 12
            if start_h < 7:  # likely PM
                start_h += 12
            work_start = start_h
            work_end = end_h

        return {
            "title": title[:100],
            "description": message,
            "deadline": deadline,
            "work_start_hour": work_start,
            "work_end_hour": work_end,
            "estimated_hours": None,
            "priority": "medium",
            "tags": [],
            "skills_required": [],
        }

    def _parse_json(self, content: str) -> Optional[Dict[str, Any]]:
        """Robustly parse JSON from AI response."""
        text = content.strip()

        # Strip markdown code blocks
        if "```" in text:
            lines = text.split("\n")
            lines = [l for l in lines if not l.strip().startswith("```")]
            text = "\n".join(lines).strip()

        # Find JSON object
        start = text.find("{")
        end = text.rfind("}") + 1
        if start >= 0 and end > start:
            try:
                return json.loads(text[start:end])
            except json.JSONDecodeError:
                pass

        return None

"""
TaskPulse - AI-Powered Automation Execution Engine
Autonomous AI agent engine that analyzes context, plans actions intelligently,
executes work as a virtual team member, and auto-fixes issues.
"""

import json
import logging
import time
from typing import Dict, Any, List, Optional
from datetime import datetime

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func

from app.models.automation import AIAgent, AgentRun, AutomationPattern
from app.models.task import Task, TaskStatus
from app.models.user import User
from app.models.notification import NotificationType, NotificationPriority
from app.services.task_service import TaskService
from app.services.notification_service import NotificationService
from app.services.ai_service import get_ai_service
from app.schemas.task import TaskCreate, TaskStatusUpdate, SubtaskCreate, CommentCreate
from app.utils.helpers import generate_uuid

logger = logging.getLogger(__name__)


class ActionResult:
    """Result of a single action execution."""

    def __init__(self, action_type: str, success: bool, data: Dict[str, Any] = None, error: str = None):
        self.action_type = action_type
        self.success = success
        self.data = data or {}
        self.error = error

    def to_dict(self):
        return {
            "action_type": self.action_type,
            "success": self.success,
            "data": self.data,
            "error": self.error,
        }


class AutomationExecutor:
    """
    AI-Powered Automation Execution Engine.

    For agents with "ai_driven": true:
      - Gathers org context (workloads, tasks, history)
      - AI plans actions based on natural language purpose
      - Executes with auto-fix and retry on failures

    For agents without "ai_driven":
      - Uses existing rule-based execution (backward compatible)
    """

    def __init__(self, db: AsyncSession):
        self.db = db
        self.task_service = TaskService(db)
        self.notification_service = NotificationService(db)
        self.ai_service = get_ai_service()

    # ==================== Main Entry Point ====================

    async def execute_agent(
        self,
        agent: AIAgent,
        trigger_data: Dict[str, Any],
        is_shadow: bool = False,
    ) -> AgentRun:
        """Execute an automation agent (AI-driven or rule-based)."""
        start_time = time.time()
        self._agent_creator_id = agent.created_by

        run = AgentRun(
            id=generate_uuid(),
            agent_id=agent.id,
            org_id=agent.org_id,
            started_at=datetime.utcnow(),
            status="running",
            is_shadow=is_shadow,
        )
        run.input_data = trigger_data
        self.db.add(run)
        await self.db.flush()

        try:
            config = agent.config
            is_ai_driven = config.get("ai_driven", False)

            if is_ai_driven:
                action_results, ai_reasoning = await self._execute_ai_driven(
                    agent, trigger_data, is_shadow
                )
            else:
                action_results, ai_reasoning = await self._execute_rule_based(
                    agent, trigger_data, is_shadow
                )

            all_success = all(r.success for r in action_results) if action_results else True

            elapsed_ms = int((time.time() - start_time) * 1000)
            run.status = "success" if all_success else "failed"
            run.completed_at = datetime.utcnow()
            run.execution_time_ms = elapsed_ms
            run.output_data = {
                "ai_driven": is_ai_driven,
                "reasoning": ai_reasoning,
                "actions_executed": len(action_results),
                "actions_succeeded": sum(1 for r in action_results if r.success),
                "results": [r.to_dict() for r in action_results],
            }

            if not all_success:
                failed = [r for r in action_results if not r.success]
                run.error_message = "; ".join(r.error or "Unknown error" for r in failed)

            await self.db.flush()

            if not is_shadow:
                await self._update_agent_metrics(agent, all_success)

            logger.info(
                f"Agent '{agent.name}' executed: {len(action_results)} actions, "
                f"success={all_success}, ai_driven={is_ai_driven}, shadow={is_shadow}, {elapsed_ms}ms"
            )
            return run

        except Exception as e:
            logger.error(f"Automation execution failed for agent {agent.id}: {e}")
            elapsed_ms = int((time.time() - start_time) * 1000)
            run.status = "failed"
            run.completed_at = datetime.utcnow()
            run.execution_time_ms = elapsed_ms
            run.error_message = str(e)
            run.output_data = {"error": str(e)}
            await self.db.flush()

            if not is_shadow:
                await self._update_agent_metrics(agent, success=False)

            return run

    # ==================== AI-Driven Execution ====================

    async def _execute_ai_driven(
        self,
        agent: AIAgent,
        trigger_data: Dict[str, Any],
        is_shadow: bool,
    ) -> tuple:
        """Execute agent using AI intelligence."""
        config = agent.config
        org_context = await self._gather_org_context(agent.org_id, agent)

        # Check if agent targets a specific task
        target_task_id = trigger_data.get("task_id") or config.get("target_task_id")

        if target_task_id:
            results, reasoning = await self._ai_process_task(
                agent, target_task_id, org_context, is_shadow
            )
        else:
            plan = await self._ai_plan_actions(agent, trigger_data, org_context)
            reasoning = plan.get("reasoning", "")
            planned_actions = plan.get("actions", [])

            # Validate AI plan
            planned_actions = self._validate_ai_plan(planned_actions, config)

            if is_shadow:
                results = [
                    ActionResult(
                        a.get("type", "unknown"), True,
                        {"simulated": True, "would_execute": a.get("type"), "params": a.get("params", {})}
                    )
                    for a in planned_actions
                ]
            else:
                results = await self._execute_planned_actions(
                    planned_actions, agent.org_id, trigger_data, org_context, config
                )

        return results, reasoning

    async def _execute_planned_actions(
        self,
        planned_actions: List[Dict],
        org_id: str,
        trigger_data: Dict[str, Any],
        org_context: Dict[str, Any],
        config: Dict[str, Any],
    ) -> List[ActionResult]:
        """Execute AI-planned actions with auto-fix on failure."""
        max_retries = config.get("constraints", {}).get("max_retries", 2)
        results = []

        for action_def in planned_actions:
            result = await self._execute_action(action_def, org_id, trigger_data)

            if not result.success:
                # AI auto-fix: analyze failure and decide recovery
                for attempt in range(max_retries):
                    fix = await self._ai_handle_failure(action_def, result.error, org_context)
                    decision = fix.get("decision", "skip")

                    if decision == "retry":
                        modified = fix.get("modified_params", {})
                        if modified:
                            action_def = dict(action_def)
                            action_def["params"] = {**action_def.get("params", {}), **modified}
                        result = await self._execute_action(action_def, org_id, trigger_data)
                        if result.success:
                            break
                    elif decision == "substitute":
                        sub_action = fix.get("substitute_action")
                        if sub_action:
                            result = await self._execute_action(sub_action, org_id, trigger_data)
                        break
                    elif decision == "abort":
                        results.append(result)
                        return results
                    else:  # skip
                        break

            results.append(result)

        return results

    # ==================== Context Gathering ====================

    async def _gather_org_context(self, org_id: str, agent: AIAgent) -> Dict[str, Any]:
        """Gather organization context for AI decision-making."""
        context = {}

        # Task counts by status
        for status in TaskStatus:
            count = (await self.db.execute(
                select(func.count()).select_from(Task).where(
                    Task.org_id == org_id, Task.status == status
                )
            )).scalar() or 0
            context.setdefault("task_counts", {})[status.value] = count

        # Overdue tasks
        overdue_result = await self.db.execute(
            select(Task).where(
                Task.org_id == org_id,
                Task.deadline < datetime.utcnow(),
                Task.status.notin_([TaskStatus.DONE, TaskStatus.ARCHIVED]),
            ).limit(10)
        )
        overdue_tasks = overdue_result.scalars().all()
        context["overdue_tasks"] = [
            {"id": t.id, "title": t.title, "assigned_to": t.assigned_to,
             "deadline": t.deadline.isoformat() if t.deadline else None, "priority": t.priority.value}
            for t in overdue_tasks
        ]

        # Blocked tasks
        blocked_result = await self.db.execute(
            select(Task).where(
                Task.org_id == org_id, Task.status == TaskStatus.BLOCKED
            ).limit(10)
        )
        blocked_tasks = blocked_result.scalars().all()
        context["blocked_tasks"] = [
            {"id": t.id, "title": t.title, "assigned_to": t.assigned_to,
             "blocker_type": t.blocker_type.value if t.blocker_type else None,
             "blocker_description": t.blocker_description}
            for t in blocked_tasks
        ]

        # Recent completed tasks
        recent_done = await self.db.execute(
            select(Task).where(
                Task.org_id == org_id, Task.status == TaskStatus.DONE
            ).order_by(Task.completed_at.desc()).limit(10)
        )
        context["recent_completed"] = [
            {"id": t.id, "title": t.title, "actual_hours": t.actual_hours}
            for t in recent_done.scalars().all()
        ]

        # User workloads
        workload_result = await self.db.execute(
            select(Task.assigned_to, func.count().label("count")).where(
                Task.org_id == org_id,
                Task.assigned_to.isnot(None),
                Task.status.in_([TaskStatus.TODO, TaskStatus.IN_PROGRESS]),
            ).group_by(Task.assigned_to)
        )
        user_workloads = {}
        for row in workload_result.all():
            user_workloads[row[0]] = row[1]

        # Get user names
        if user_workloads:
            users_result = await self.db.execute(
                select(User).where(User.id.in_(list(user_workloads.keys())))
            )
            for u in users_result.scalars().all():
                user_workloads[u.id] = {
                    "name": f"{u.first_name} {u.last_name}",
                    "active_tasks": user_workloads.get(u.id, 0),
                }
        context["user_workloads"] = user_workloads

        # Agent's recent runs
        runs_result = await self.db.execute(
            select(AgentRun).where(
                AgentRun.agent_id == agent.id
            ).order_by(AgentRun.created_at.desc()).limit(5)
        )
        context["recent_agent_runs"] = [
            {"status": r.status, "created_at": r.created_at.isoformat(),
             "actions_count": (r.output_data or {}).get("actions_executed", 0)}
            for r in runs_result.scalars().all()
        ]

        return context

    # ==================== AI Action Planning ====================

    async def _ai_plan_actions(
        self,
        agent: AIAgent,
        trigger_data: Dict[str, Any],
        org_context: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Ask AI to plan actions based on agent purpose and context."""
        config = agent.config
        permissions = config.get("permissions", [
            "create_task", "assign_task", "add_comment",
            "update_status", "notify_user", "decompose_task",
            "unblock_task", "analyze_and_complete", "smart_assign"
        ])

        system_prompt = """You are an autonomous AI automation agent in a task management system.
You analyze the current workspace state and plan actions to fulfill your purpose.

AVAILABLE ACTIONS (only use types from the permissions list):
- create_task: Create a new task. Params: title (required), description, priority (low/medium/high/critical), assigned_to (user_id), tags (list), estimated_hours
- assign_task: Assign a task. Params: task_id (required), assignee_id (required)
- update_status: Change task status. Params: task_id (required), status (required: todo/in_progress/blocked/review/done)
- add_comment: Post a comment on a task. Params: task_id (required), content (required)
- decompose_task: Break task into subtasks using AI. Params: task_id (required), max_subtasks
- unblock_task: Analyze and resolve a blocked task. Params: task_id (required)
- notify_user: Send notification. Params: user_id (required), title (required), message (required)
- analyze_and_complete: AI works on and completes a task. Params: task_id (required)
- smart_assign: AI picks best assignee by workload+skills. Params: task_id (required)

RULES:
- Only use action types from your permissions list
- Provide all required params for each action
- Use real task_id and user_id values from the context
- Be conservative: only take actions that clearly align with your purpose
- Return valid JSON only

Return a JSON object:
{
  "reasoning": "Brief explanation of your analysis and decisions",
  "actions": [
    {"type": "action_type", "params": {...}},
    ...
  ]
}"""

        prompt = f"""AGENT PURPOSE: {config.get('purpose', 'General task management')}

PERMISSIONS: {json.dumps(permissions)}

CONSTRAINTS: {json.dumps(config.get('constraints', {}))}

TRIGGER EVENT: {json.dumps(trigger_data, default=str)}

CURRENT WORKSPACE STATE:
- Task counts: {json.dumps(org_context.get('task_counts', {}))}
- Overdue tasks: {json.dumps(org_context.get('overdue_tasks', []), default=str)}
- Blocked tasks: {json.dumps(org_context.get('blocked_tasks', []))}
- User workloads: {json.dumps(org_context.get('user_workloads', {}), default=str)}
- Recent completed: {json.dumps(org_context.get('recent_completed', []))}
- Agent's recent runs: {json.dumps(org_context.get('recent_agent_runs', []))}

Analyze the workspace and plan actions to fulfill your purpose. Return JSON only."""

        try:
            response = await self.ai_service.generate(
                prompt=prompt,
                system_prompt=system_prompt,
                temperature=0.4,
                max_tokens=2000,
                use_cache=False,
            )
            plan = self._parse_ai_json(response.content)
            logger.info(f"AI planned {len(plan.get('actions', []))} actions: {plan.get('reasoning', '')[:100]}")
            return plan
        except Exception as e:
            logger.error(f"AI planning failed: {e}")
            return {"reasoning": f"AI planning failed: {e}", "actions": []}

    def _validate_ai_plan(self, actions: List[Dict], config: Dict) -> List[Dict]:
        """Validate and sanitize AI-planned actions."""
        permissions = set(config.get("permissions", []))
        constraints = config.get("constraints", {})
        max_tasks = constraints.get("max_tasks_per_run", 10)
        allowed_priorities = constraints.get("allowed_priorities")

        validated = []
        for action in actions:
            if len(validated) >= max_tasks:
                break

            action_type = action.get("type")
            if not action_type:
                continue

            # Check permissions
            if permissions and action_type not in permissions:
                logger.warning(f"AI planned unauthorized action '{action_type}', skipping")
                continue

            # Check priority constraints
            if allowed_priorities and action_type == "create_task":
                priority = action.get("params", {}).get("priority", "medium")
                if priority not in allowed_priorities:
                    action.setdefault("params", {})["priority"] = "medium"

            validated.append(action)

        return validated

    # ==================== AI Task Processing ====================

    async def _ai_process_task(
        self,
        agent: AIAgent,
        task_id: str,
        org_context: Dict[str, Any],
        is_shadow: bool,
    ) -> tuple:
        """AI works on a specific task as a virtual team member."""
        task = await self.task_service.get_task_by_id(task_id, agent.org_id, include_subtasks=True)
        if not task:
            return [ActionResult("process_task", False, error=f"Task {task_id} not found")], "Task not found"

        # Build task context
        task_context = {
            "id": task.id,
            "title": task.title,
            "description": task.description,
            "status": task.status.value,
            "priority": task.priority.value,
            "assigned_to": task.assigned_to,
            "blocker_type": task.blocker_type.value if task.blocker_type else None,
            "blocker_description": task.blocker_description,
            "estimated_hours": task.estimated_hours,
            "actual_hours": task.actual_hours,
            "deadline": task.deadline.isoformat() if task.deadline else None,
            "tags": task.tags,
            "skills_required": task.skills_required,
        }

        # Get subtask info
        subtasks = await self.task_service.get_subtasks(task_id, agent.org_id)
        task_context["subtasks"] = [
            {"id": s.id, "title": s.title, "status": s.status.value}
            for s in subtasks
        ]

        # Get recent comments
        comments = await self.task_service.get_task_comments(task_id, limit=5)
        task_context["recent_comments"] = [
            {"content": c.content[:200], "is_ai": c.is_ai_generated}
            for c in comments
        ]

        config = agent.config

        system_prompt = """You are an autonomous AI task worker. You are assigned a specific task and must decide how to work on it.

STRATEGIES:
- decompose: Break a complex task into subtasks (use when task is large/vague and has no subtasks)
- provide_solution: Generate a detailed solution and post as comment (use when task is blocked or needs guidance)
- complete: Generate deliverable content, post as comment, mark task as done (use for simple/repetitive tasks)
- reassign: Find a better-suited team member (use when current assignee is overloaded or lacks skills)
- escalate: Notify manager with analysis (use only when issue is serious and can't be auto-resolved)

AVAILABLE ACTIONS:
- add_comment: {task_id, content} - Post AI-generated content
- update_status: {task_id, status} - Change task status (todo/in_progress/review/done)
- decompose_task: {task_id, max_subtasks} - Break into subtasks
- unblock_task: {task_id} - Analyze blocker and provide fix
- smart_assign: {task_id} - AI picks best assignee
- assign_task: {task_id, assignee_id} - Assign to specific user
- notify_user: {user_id, title, message} - Send notification
- create_task: {title, description, priority, assigned_to} - Create follow-up task

Return JSON:
{
  "reasoning": "Analysis of the task and chosen strategy",
  "strategy": "decompose|provide_solution|complete|reassign|escalate",
  "actions": [{"type": "...", "params": {...}}, ...]
}"""

        prompt = f"""AGENT PURPOSE: {config.get('purpose', 'Work on assigned tasks')}

TARGET TASK:
{json.dumps(task_context, default=str, indent=2)}

WORKSPACE STATE:
- User workloads: {json.dumps(org_context.get('user_workloads', {}), default=str)}
- Blocked tasks: {json.dumps(org_context.get('blocked_tasks', []))}

Analyze this task and decide how to work on it. Return JSON only."""

        try:
            response = await self.ai_service.generate(
                prompt=prompt,
                system_prompt=system_prompt,
                temperature=0.4,
                max_tokens=2000,
                use_cache=False,
            )
            plan = self._parse_ai_json(response.content)
            reasoning = plan.get("reasoning", "")
            actions = plan.get("actions", [])

            logger.info(f"AI task processing: strategy={plan.get('strategy')}, actions={len(actions)}")

            if is_shadow:
                results = [
                    ActionResult(a.get("type", "unknown"), True,
                                 {"simulated": True, "strategy": plan.get("strategy"),
                                  "would_execute": a.get("type"), "params": a.get("params", {})})
                    for a in actions
                ]
            else:
                results = await self._execute_planned_actions(
                    actions, agent.org_id, {}, org_context, config
                )

            return results, reasoning

        except Exception as e:
            logger.error(f"AI task processing failed: {e}")
            return [ActionResult("process_task", False, error=str(e))], f"AI processing failed: {e}"

    # ==================== AI Auto-Fix ====================

    async def _ai_handle_failure(
        self,
        failed_action: Dict[str, Any],
        error: str,
        org_context: Dict[str, Any],
    ) -> Dict[str, Any]:
        """AI analyzes action failure and decides recovery strategy."""
        system_prompt = """You are an error recovery AI. An automation action failed and you must decide how to handle it.

DECISIONS:
- retry: Retry with modified params. Provide "modified_params" dict with corrected values.
- skip: Skip this action and continue with the next one.
- substitute: Replace with a completely different action. Provide "substitute_action" with type and params.
- abort: Stop all execution. Use only for critical/unrecoverable errors.

Return JSON:
{"decision": "retry|skip|substitute|abort", "reason": "...", "modified_params": {...}, "substitute_action": {...}}"""

        prompt = f"""FAILED ACTION: {json.dumps(failed_action, default=str)}

ERROR: {error}

AVAILABLE USERS: {json.dumps(list(org_context.get('user_workloads', {}).keys())[:5])}

Decide how to recover. Return JSON only."""

        try:
            response = await self.ai_service.generate(
                prompt=prompt,
                system_prompt=system_prompt,
                temperature=0.3,
                max_tokens=500,
                use_cache=False,
            )
            fix = self._parse_ai_json(response.content)
            logger.info(f"AI failure recovery: {fix.get('decision')} - {fix.get('reason', '')[:80]}")
            return fix
        except Exception as e:
            logger.error(f"AI failure recovery failed: {e}")
            return {"decision": "skip", "reason": f"Recovery AI failed: {e}"}

    # ==================== AI Trigger Evaluation ====================

    async def _ai_evaluate_trigger(
        self,
        agent: AIAgent,
        org_context: Dict[str, Any],
    ) -> tuple:
        """AI decides whether agent should fire based on context."""
        config = agent.config

        system_prompt = """You are an automation trigger evaluator. Decide if this agent should execute now based on its purpose and the current workspace state.

Return JSON: {"should_fire": true/false, "reason": "...", "confidence": 0.0-1.0}"""

        prompt = f"""AGENT PURPOSE: {config.get('purpose', '')}

WORKSPACE STATE:
- Task counts: {json.dumps(org_context.get('task_counts', {}))}
- Overdue: {len(org_context.get('overdue_tasks', []))} tasks
- Blocked: {len(org_context.get('blocked_tasks', []))} tasks
- Agent's recent runs: {json.dumps(org_context.get('recent_agent_runs', []))}

Should this agent execute now? Return JSON only."""

        try:
            response = await self.ai_service.generate(
                prompt=prompt,
                system_prompt=system_prompt,
                temperature=0.2,
                max_tokens=300,
                use_cache=False,
            )
            result = self._parse_ai_json(response.content)
            threshold = config.get("constraints", {}).get("confidence_threshold", 0.7)
            should_fire = result.get("should_fire", False) and result.get("confidence", 0) >= threshold
            return should_fire, {
                "trigger_type": "ai_evaluate",
                "ai_reason": result.get("reason", ""),
                "confidence": result.get("confidence", 0),
            }
        except Exception as e:
            logger.error(f"AI trigger evaluation failed: {e}")
            return False, {}

    # ==================== Trigger Evaluation ====================

    async def evaluate_trigger(
        self,
        agent: AIAgent,
        event_type: str = None,
        event_data: Dict[str, Any] = None,
    ) -> tuple:
        """Evaluate whether an agent's triggers are satisfied."""
        config = agent.config
        triggers = config.get("triggers", [])

        if agent.pattern_id and not triggers:
            pattern = await self._get_pattern(agent.pattern_id)
            if pattern:
                triggers = pattern.triggers

        if not triggers:
            return False, {}

        for trigger in triggers:
            trigger_type = trigger.get("type")

            if trigger_type == "event" and event_type:
                if self._matches_event_trigger(trigger, event_type, event_data):
                    return True, {
                        "trigger_type": "event",
                        "event_type": event_type,
                        "event_data": event_data or {},
                        "trigger_config": trigger,
                    }

            elif trigger_type == "condition":
                matches, context = await self._evaluate_condition_trigger(
                    trigger, agent.org_id
                )
                if matches:
                    return True, {
                        "trigger_type": "condition",
                        "condition": trigger,
                        "context": context,
                    }

            elif trigger_type == "ai_evaluate":
                org_context = await self._gather_org_context(agent.org_id, agent)
                should_fire, ai_data = await self._ai_evaluate_trigger(agent, org_context)
                if should_fire:
                    return True, ai_data

        return False, {}

    def _matches_event_trigger(
        self,
        trigger: Dict[str, Any],
        event_type: str,
        event_data: Dict[str, Any] = None,
    ) -> bool:
        """Check if an event matches a trigger definition."""
        trigger_events = trigger.get("events", [])
        if event_type not in trigger_events:
            return False

        filters = trigger.get("filters", {})
        if not filters or not event_data:
            return True

        for key, expected in filters.items():
            actual = event_data.get(key)
            if isinstance(expected, list):
                if actual not in expected:
                    return False
            elif actual != expected:
                return False

        return True

    async def _evaluate_condition_trigger(
        self,
        trigger: Dict[str, Any],
        org_id: str,
    ) -> tuple:
        """Evaluate a condition-based trigger."""
        condition_type = trigger.get("condition_type")
        params = trigger.get("params", {})

        if condition_type == "task_count_exceeds":
            tag = params.get("tag")
            threshold = params.get("threshold", 5)
            status_filter = params.get("status")

            query = select(func.count()).select_from(Task).where(Task.org_id == org_id)
            if tag:
                query = query.where(Task.tags_json.contains(tag))
            if status_filter:
                query = query.where(Task.status == TaskStatus(status_filter))

            count = (await self.db.execute(query)).scalar() or 0
            return count > threshold, {"count": count, "threshold": threshold}

        elif condition_type == "no_tasks_assigned":
            user_id = params.get("user_id")
            if not user_id:
                return False, {}

            query = select(func.count()).select_from(Task).where(
                Task.org_id == org_id,
                Task.assigned_to == user_id,
                Task.status.in_([TaskStatus.TODO, TaskStatus.IN_PROGRESS]),
            )
            count = (await self.db.execute(query)).scalar() or 0
            return count == 0, {"user_id": user_id, "active_tasks": count}

        elif condition_type == "overdue_tasks_exist":
            query = select(func.count()).select_from(Task).where(
                Task.org_id == org_id,
                Task.deadline < datetime.utcnow(),
                Task.status.notin_([TaskStatus.DONE, TaskStatus.ARCHIVED]),
            )
            count = (await self.db.execute(query)).scalar() or 0
            threshold = params.get("threshold", 0)
            return count > threshold, {"overdue_count": count}

        return False, {}

    # ==================== Rule-Based Execution (Backward Compatible) ====================

    async def _execute_rule_based(
        self,
        agent: AIAgent,
        trigger_data: Dict[str, Any],
        is_shadow: bool,
    ) -> tuple:
        """Existing rule-based execution for non-AI agents."""
        config = agent.config
        actions = config.get("actions", [])

        if agent.pattern_id and not actions:
            pattern = await self._get_pattern(agent.pattern_id)
            if pattern:
                actions = pattern.actions

        if not actions:
            raise ValueError("Agent has no configured actions")

        action_results = []
        for action_def in actions:
            if is_shadow:
                result = await self._simulate_action(action_def, agent.org_id, trigger_data)
            else:
                result = await self._execute_action(action_def, agent.org_id, trigger_data)
            action_results.append(result)

            if not result.success and not action_def.get("continue_on_error", False):
                break

        return action_results, "rule-based execution"

    # ==================== Action Execution ====================

    async def _execute_action(
        self,
        action_def: Dict[str, Any],
        org_id: str,
        trigger_data: Dict[str, Any],
    ) -> ActionResult:
        """Execute a single automation action."""
        action_type = action_def.get("type")
        params = action_def.get("params", {})

        try:
            if action_type == "create_task":
                return await self._action_create_task(params, org_id, trigger_data)
            elif action_type in ("update_task_status", "update_status"):
                return await self._action_update_task_status(params, org_id)
            elif action_type == "assign_task":
                return await self._action_assign_task(params, org_id)
            elif action_type == "decompose_task":
                return await self._action_decompose_task(params, org_id)
            elif action_type == "create_recurring_task":
                return await self._action_create_task(params, org_id, trigger_data)
            elif action_type in ("notify", "notify_user"):
                return await self._action_notify(params, org_id)
            elif action_type == "add_comment":
                return await self._action_add_comment(params, org_id)
            elif action_type == "unblock_task":
                return await self._action_unblock_task(params, org_id)
            elif action_type == "analyze_and_complete":
                return await self._action_analyze_and_complete(params, org_id)
            elif action_type == "smart_assign":
                return await self._action_smart_assign(params, org_id)
            else:
                return ActionResult(action_type or "unknown", False, error=f"Unknown action type: {action_type}")
        except Exception as e:
            logger.error(f"Action {action_type} failed: {e}")
            return ActionResult(action_type or "unknown", False, error=str(e))

    async def _simulate_action(
        self,
        action_def: Dict[str, Any],
        org_id: str,
        trigger_data: Dict[str, Any],
    ) -> ActionResult:
        """Simulate an action without persisting (shadow mode)."""
        action_type = action_def.get("type")
        params = action_def.get("params", {})

        return ActionResult(
            action_type=action_type or "unknown",
            success=True,
            data={
                "simulated": True,
                "would_execute": action_type,
                "params": params,
            },
        )

    # ==================== Action Handlers ====================

    async def _action_create_task(
        self,
        params: Dict[str, Any],
        org_id: str,
        trigger_data: Dict[str, Any],
    ) -> ActionResult:
        """Create a task from automation parameters."""
        title = self._resolve_template(params.get("title", "Automated Task"), trigger_data)
        description = self._resolve_template(params.get("description", ""), trigger_data)

        task_create = TaskCreate(
            title=title,
            description=description,
            priority=params.get("priority", "medium"),
            assigned_to=params.get("assigned_to"),
            tags=params.get("tags", ["automation", "ai-agent"]),
            skills_required=params.get("skills_required", []),
            tools=params.get("tools", []),
            team_id=params.get("team_id"),
            project_id=params.get("project_id"),
            estimated_hours=params.get("estimated_hours"),
        )

        created_by = params.get("created_by") or getattr(self, "_agent_creator_id", None) or "system"
        task = await self.task_service.create_task(task_create, org_id, created_by)

        return ActionResult("create_task", True, {"task_id": task.id, "title": task.title})

    async def _action_update_task_status(
        self,
        params: Dict[str, Any],
        org_id: str,
    ) -> ActionResult:
        """Update a task's status."""
        task_id = params.get("task_id")
        new_status = params.get("status")

        if not task_id or not new_status:
            return ActionResult("update_status", False, error="task_id and status required")

        status_update = TaskStatusUpdate(status=TaskStatus(new_status))
        updated_by = getattr(self, "_agent_creator_id", None) or "system"
        task = await self.task_service.update_task_status(
            task_id, org_id, status_update, updated_by=updated_by
        )
        return ActionResult("update_status", True, {"task_id": task.id, "new_status": new_status})

    async def _action_assign_task(
        self,
        params: Dict[str, Any],
        org_id: str,
    ) -> ActionResult:
        """Assign a task to a user."""
        task_id = params.get("task_id")
        assignee_id = params.get("assignee_id")

        if not task_id or not assignee_id:
            return ActionResult("assign_task", False, error="task_id and assignee_id required")

        assigned_by = getattr(self, "_agent_creator_id", None) or "system"
        task = await self.task_service.assign_task(
            task_id, org_id, assignee_id, assigned_by=assigned_by
        )
        return ActionResult("assign_task", True, {"task_id": task.id, "assigned_to": assignee_id})

    async def _action_decompose_task(
        self,
        params: Dict[str, Any],
        org_id: str,
    ) -> ActionResult:
        """Auto-decompose a task into subtasks using AI."""
        task_id = params.get("task_id")
        if not task_id:
            return ActionResult("decompose_task", False, error="task_id required")

        task = await self.task_service.get_task_by_id(task_id, org_id)
        if not task:
            return ActionResult("decompose_task", False, error=f"Task {task_id} not found")

        decomposition = await self.ai_service.decompose_task(
            title=task.title,
            description=task.description or "",
            goal=task.goal,
            max_subtasks=params.get("max_subtasks", 10),
        )

        created_subtasks = []
        for sub_data in decomposition.get("subtasks", []):
            subtask_create = SubtaskCreate(
                title=sub_data.get("title", "Subtask"),
                description=sub_data.get("description", ""),
                estimated_hours=sub_data.get("estimated_hours"),
                sort_order=sub_data.get("order", 0),
            )
            subtask_creator = getattr(self, "_agent_creator_id", None) or "system"
            subtask = await self.task_service.create_subtask(
                task_id, org_id, subtask_create, created_by=subtask_creator
            )
            created_subtasks.append(subtask.id)

        return ActionResult(
            "decompose_task", True,
            {"task_id": task_id, "subtasks_created": len(created_subtasks), "subtask_ids": created_subtasks}
        )

    async def _action_notify(
        self,
        params: Dict[str, Any],
        org_id: str,
    ) -> ActionResult:
        """Send a notification."""
        user_id = params.get("user_id")
        title = params.get("title", "Automation Notification")
        message = params.get("message", "")

        if not user_id:
            return ActionResult("notify_user", False, error="user_id required")

        notification = await self.notification_service.create_notification(
            user_id=user_id,
            org_id=org_id,
            notification_type=NotificationType.AI_SUGGESTION,
            title=title,
            message=message,
            priority=NotificationPriority.MEDIUM,
        )
        return ActionResult("notify_user", True, {"notification_id": notification.id})

    async def _action_add_comment(
        self,
        params: Dict[str, Any],
        org_id: str,
    ) -> ActionResult:
        """Post an AI-generated comment on a task."""
        task_id = params.get("task_id")
        content = params.get("content")

        if not task_id or not content:
            return ActionResult("add_comment", False, error="task_id and content required")

        user_id = getattr(self, "_agent_creator_id", None) or "system"
        comment = await self.task_service.add_comment(
            task_id=task_id,
            org_id=org_id,
            comment_data=CommentCreate(content=content),
            user_id=user_id,
            is_ai_generated=True,
        )
        return ActionResult("add_comment", True, {"comment_id": comment.id, "task_id": task_id})

    async def _action_unblock_task(
        self,
        params: Dict[str, Any],
        org_id: str,
    ) -> ActionResult:
        """Analyze a blocked task and provide an AI solution to unblock it."""
        task_id = params.get("task_id")
        if not task_id:
            return ActionResult("unblock_task", False, error="task_id required")

        task = await self.task_service.get_task_by_id(task_id, org_id)
        if not task:
            return ActionResult("unblock_task", False, error=f"Task {task_id} not found")

        # Get AI unblock suggestion
        suggestion = await self.ai_service.get_unblock_suggestion(
            task_title=task.title,
            task_description=task.description or "",
            blocker_type=task.blocker_type.value if task.blocker_type else "unknown",
            blocker_description=task.blocker_description or "No description provided",
        )

        suggestion_text = suggestion.get("suggestion", "No suggestion available")
        confidence = suggestion.get("confidence", 0)

        # Post solution as comment
        user_id = getattr(self, "_agent_creator_id", None) or "system"
        comment_content = (
            f"**AI Unblock Suggestion** (confidence: {confidence:.0%})\n\n"
            f"{suggestion_text}\n\n"
            f"_This suggestion was generated automatically by the AI agent._"
        )
        await self.task_service.add_comment(
            task_id=task_id,
            org_id=org_id,
            comment_data=CommentCreate(content=comment_content),
            user_id=user_id,
            is_ai_generated=True,
        )

        # Move task from BLOCKED to IN_PROGRESS if currently blocked
        status_changed = False
        if task.status == TaskStatus.BLOCKED:
            try:
                status_update = TaskStatusUpdate(status=TaskStatus.IN_PROGRESS)
                await self.task_service.update_task_status(
                    task_id, org_id, status_update, updated_by=user_id
                )
                status_changed = True
            except Exception:
                pass  # Status change is best-effort

        # Notify assigned user
        if task.assigned_to:
            try:
                await self.notification_service.notify_ai_suggestion(
                    user_id=task.assigned_to,
                    org_id=org_id,
                    task_id=task_id,
                    suggestion_preview=suggestion_text[:100],
                )
            except Exception:
                pass  # Notification is best-effort

        return ActionResult("unblock_task", True, {
            "task_id": task_id,
            "suggestion_confidence": confidence,
            "status_changed": status_changed,
        })

    async def _action_analyze_and_complete(
        self,
        params: Dict[str, Any],
        org_id: str,
    ) -> ActionResult:
        """AI works on a task, generates deliverable content, and marks it done."""
        task_id = params.get("task_id")
        if not task_id:
            return ActionResult("analyze_and_complete", False, error="task_id required")

        task = await self.task_service.get_task_by_id(task_id, org_id)
        if not task:
            return ActionResult("analyze_and_complete", False, error=f"Task {task_id} not found")

        # AI generates deliverable
        system_prompt = """You are a task completion AI. Analyze the task and produce the deliverable.
If it's a report task, write the report. If it's an analysis task, provide the analysis.
If it's a planning task, create the plan. Be thorough and professional."""

        prompt = f"""Task: {task.title}
Description: {task.description or 'No description'}
Goal: {task.goal or 'Complete the task'}
Skills required: {', '.join(task.skills_required) if task.skills_required else 'General'}

Complete this task and provide the deliverable."""

        response = await self.ai_service.generate(
            prompt=prompt,
            system_prompt=system_prompt,
            temperature=0.6,
            max_tokens=2000,
            use_cache=False,
        )

        # Post deliverable as comment
        user_id = getattr(self, "_agent_creator_id", None) or "system"
        comment_content = (
            f"**AI Task Completion**\n\n"
            f"{response.content}\n\n"
            f"_Completed automatically by AI agent._"
        )
        await self.task_service.add_comment(
            task_id=task_id,
            org_id=org_id,
            comment_data=CommentCreate(content=comment_content),
            user_id=user_id,
            is_ai_generated=True,
        )

        # Move to REVIEW (not directly to DONE, let human verify)
        status_changed = False
        if task.status in (TaskStatus.TODO, TaskStatus.IN_PROGRESS):
            try:
                target_status = TaskStatus.REVIEW if task.can_transition_to(TaskStatus.REVIEW) else TaskStatus.DONE
                status_update = TaskStatusUpdate(status=target_status)
                await self.task_service.update_task_status(
                    task_id, org_id, status_update, updated_by=user_id
                )
                status_changed = True
            except Exception:
                pass

        return ActionResult("analyze_and_complete", True, {
            "task_id": task_id,
            "deliverable_length": len(response.content),
            "status_changed": status_changed,
        })

    async def _action_smart_assign(
        self,
        params: Dict[str, Any],
        org_id: str,
    ) -> ActionResult:
        """AI picks the best assignee based on workload and skills."""
        task_id = params.get("task_id")
        if not task_id:
            return ActionResult("smart_assign", False, error="task_id required")

        task = await self.task_service.get_task_by_id(task_id, org_id)
        if not task:
            return ActionResult("smart_assign", False, error=f"Task {task_id} not found")

        # Get user workloads
        workload_result = await self.db.execute(
            select(Task.assigned_to, func.count().label("count")).where(
                Task.org_id == org_id,
                Task.assigned_to.isnot(None),
                Task.status.in_([TaskStatus.TODO, TaskStatus.IN_PROGRESS]),
            ).group_by(Task.assigned_to)
        )
        workloads = {row[0]: row[1] for row in workload_result.all()}

        # Get all org users
        users_result = await self.db.execute(
            select(User).where(User.org_id == org_id, User.is_active == True)
        )
        users = users_result.scalars().all()

        if not users:
            return ActionResult("smart_assign", False, error="No users available for assignment")

        # Ask AI to pick best assignee
        user_info = [
            {"id": u.id, "name": f"{u.first_name} {u.last_name}",
             "role": u.role.value if hasattr(u.role, 'value') else str(u.role),
             "active_tasks": workloads.get(u.id, 0)}
            for u in users
        ]

        system_prompt = """Pick the best user to assign this task to. Consider workload (prefer less busy users) and role fit.
Return JSON: {"assignee_id": "user-id", "reason": "why this person"}"""

        prompt = f"""Task: {task.title}
Description: {task.description or 'No description'}
Skills needed: {', '.join(task.skills_required) if task.skills_required else 'General'}

Available team members:
{json.dumps(user_info, indent=2)}

Pick the best assignee. Return JSON only."""

        try:
            response = await self.ai_service.generate(
                prompt=prompt,
                system_prompt=system_prompt,
                temperature=0.3,
                max_tokens=300,
                use_cache=False,
            )
            decision = self._parse_ai_json(response.content)
            assignee_id = decision.get("assignee_id")

            if not assignee_id:
                # Fallback: pick user with lowest workload
                assignee_id = min(user_info, key=lambda u: u["active_tasks"])["id"]

            assigned_by = getattr(self, "_agent_creator_id", None) or "system"
            await self.task_service.assign_task(task_id, org_id, assignee_id, assigned_by=assigned_by)

            # Notify
            try:
                await self.notification_service.notify_task_assigned(
                    user_id=assignee_id,
                    org_id=org_id,
                    task_id=task_id,
                    task_title=task.title,
                    assigned_by=assigned_by,
                )
            except Exception:
                pass

            return ActionResult("smart_assign", True, {
                "task_id": task_id,
                "assigned_to": assignee_id,
                "reason": decision.get("reason", "AI selected"),
            })

        except Exception as e:
            logger.error(f"Smart assign failed: {e}")
            return ActionResult("smart_assign", False, error=str(e))

    # ==================== Helpers ====================

    def _resolve_template(self, template: str, context: Dict[str, Any]) -> str:
        """Simple template variable resolution: {variable_name} -> value."""
        if not template or not context:
            return template
        try:
            return template.format(**context)
        except (KeyError, IndexError, ValueError):
            return template

    def _parse_ai_json(self, content: str) -> Dict[str, Any]:
        """Parse JSON from AI response, handling markdown code blocks."""
        text = content.strip()
        # Remove markdown code blocks
        if text.startswith("```"):
            lines = text.split("\n")
            # Remove first and last line (```json and ```)
            lines = [l for l in lines if not l.strip().startswith("```")]
            text = "\n".join(lines).strip()
        try:
            return json.loads(text)
        except json.JSONDecodeError:
            # Try to find JSON object in the text
            start = text.find("{")
            end = text.rfind("}") + 1
            if start >= 0 and end > start:
                try:
                    return json.loads(text[start:end])
                except json.JSONDecodeError:
                    pass
            logger.warning(f"Failed to parse AI JSON: {text[:200]}")
            return {}

    async def _get_pattern(self, pattern_id: str) -> Optional[AutomationPattern]:
        """Get an AutomationPattern by ID."""
        result = await self.db.execute(
            select(AutomationPattern).where(AutomationPattern.id == pattern_id)
        )
        return result.scalar_one_or_none()

    async def _update_agent_metrics(self, agent: AIAgent, success: bool):
        """Update agent run metrics."""
        agent.total_runs = (agent.total_runs or 0) + 1
        if success:
            agent.successful_runs = (agent.successful_runs or 0) + 1
        agent.last_run_at = datetime.utcnow()

        if success:
            hours_per_run = agent.config.get("hours_saved_per_run", 0.25)
            agent.hours_saved_total = (agent.hours_saved_total or 0) + hours_per_run

        await self.db.flush()

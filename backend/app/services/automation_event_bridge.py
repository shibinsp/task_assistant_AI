"""
TaskPulse - Automation Event Bridge
Connects task mutations to the automation execution engine.
"""

import logging
from typing import Dict, Any

from sqlalchemy import select

from app.database import AsyncSessionLocal
from app.models.automation import AIAgent, AgentStatus
from app.services.automation_executor import AutomationExecutor
from app.agents.base import EventType

logger = logging.getLogger(__name__)

# Map EventType enum values to automation trigger event names
EVENT_TYPE_MAP = {
    EventType.TASK_CREATED: "task_created",
    EventType.TASK_COMPLETED: "task_completed",
    EventType.TASK_BLOCKED: "task_blocked",
    EventType.TASK_ASSIGNED: "task_assigned",
    EventType.TASK_UPDATED: "task_updated",
}


async def handle_automation_event(event_type: EventType, event_data: Dict[str, Any]):
    """
    Called when a task event occurs. Checks all LIVE/SHADOW agents
    for matching event triggers and executes them.
    """
    automation_event = EVENT_TYPE_MAP.get(event_type)
    if not automation_event:
        return

    logger.debug(f"Automation event bridge: received {automation_event}")

    async with AsyncSessionLocal() as db:
        try:
            result = await db.execute(
                select(AIAgent).where(
                    AIAgent.status.in_([AgentStatus.LIVE, AgentStatus.SHADOW])
                )
            )
            agents = result.scalars().all()

            if not agents:
                return

            executor = AutomationExecutor(db)

            for agent in agents:
                try:
                    should_fire, trigger_data = await executor.evaluate_trigger(
                        agent, event_type=automation_event, event_data=event_data
                    )
                    if should_fire:
                        is_shadow = (agent.status == AgentStatus.SHADOW)
                        logger.info(
                            f"Event trigger matched for agent '{agent.name}' "
                            f"on {automation_event} (shadow={is_shadow})"
                        )
                        await executor.execute_agent(agent, trigger_data, is_shadow=is_shadow)

                except Exception as e:
                    logger.error(f"Error evaluating agent {agent.id} for event: {e}")

            await db.commit()

        except Exception as e:
            logger.error(f"Automation event bridge failed: {e}")
            await db.rollback()

"""
TaskPulse - Automation Scheduler
APScheduler integration for running automations on schedule and responding to events.
"""

import logging
from datetime import datetime
from typing import Optional

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from apscheduler.triggers.interval import IntervalTrigger
from sqlalchemy import select

from app.database import AsyncSessionLocal
from app.models.automation import AIAgent, AgentStatus
from app.services.automation_executor import AutomationExecutor

logger = logging.getLogger(__name__)

# Global scheduler instance
_scheduler: Optional[AsyncIOScheduler] = None


async def _execute_scheduled_agents():
    """
    Periodic job: find all LIVE/SHADOW agents with condition triggers and evaluate them.
    Runs every 5 minutes.
    """
    logger.debug("Automation scheduler tick: checking for condition-triggered agents")

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
                    config = agent.config
                    triggers = config.get("triggers", [])

                    for trigger in triggers:
                        if trigger.get("type") == "condition":
                            should_fire, trigger_data = await executor.evaluate_trigger(
                                agent, event_type=None, event_data=None
                            )
                            if should_fire:
                                is_shadow = (agent.status == AgentStatus.SHADOW)
                                logger.info(
                                    f"Condition trigger fired for agent '{agent.name}' "
                                    f"(shadow={is_shadow})"
                                )
                                await executor.execute_agent(agent, trigger_data, is_shadow=is_shadow)
                            break  # Only evaluate condition triggers once per agent

                except Exception as e:
                    logger.error(f"Error checking agent {agent.id}: {e}")

            await db.commit()

        except Exception as e:
            logger.error(f"Automation scheduler tick failed: {e}")
            await db.rollback()


async def _execute_cron_agent(agent_id: str):
    """Execute a specific agent triggered by its cron schedule."""
    logger.info(f"Cron trigger fired for agent {agent_id}")

    async with AsyncSessionLocal() as db:
        try:
            result = await db.execute(
                select(AIAgent).where(AIAgent.id == agent_id)
            )
            agent = result.scalar_one_or_none()

            if not agent:
                logger.warning(f"Cron-triggered agent {agent_id} not found")
                return

            if agent.status not in (AgentStatus.LIVE, AgentStatus.SHADOW):
                logger.info(f"Agent {agent_id} status is {agent.status.value}, skipping cron execution")
                return

            executor = AutomationExecutor(db)
            is_shadow = (agent.status == AgentStatus.SHADOW)
            trigger_data = {
                "trigger_type": "schedule",
                "scheduled_at": datetime.utcnow().isoformat(),
            }

            await executor.execute_agent(agent, trigger_data, is_shadow=is_shadow)
            await db.commit()

        except Exception as e:
            logger.error(f"Cron execution failed for agent {agent_id}: {e}")
            await db.rollback()


async def register_agent_cron(agent: AIAgent):
    """
    Register cron schedules for an agent.
    Call this when an agent transitions to SHADOW or LIVE status.
    """
    global _scheduler
    if not _scheduler:
        return

    config = agent.config
    triggers = config.get("triggers", [])

    for trigger in triggers:
        if trigger.get("type") == "schedule":
            cron_expr = trigger.get("cron")
            if not cron_expr:
                continue

            job_id = f"agent_cron_{agent.id}"

            # Remove existing job if present
            existing = _scheduler.get_job(job_id)
            if existing:
                _scheduler.remove_job(job_id)

            # Parse 5-part cron: minute hour day_of_month month day_of_week
            parts = cron_expr.split()
            if len(parts) == 5:
                cron_trigger = CronTrigger(
                    minute=parts[0],
                    hour=parts[1],
                    day=parts[2],
                    month=parts[3],
                    day_of_week=parts[4],
                    timezone=trigger.get("timezone", "UTC"),
                )
                _scheduler.add_job(
                    _execute_cron_agent,
                    trigger=cron_trigger,
                    args=[agent.id],
                    id=job_id,
                    name=f"Automation: {agent.name}",
                    replace_existing=True,
                )
                logger.info(f"Registered cron job for agent '{agent.name}': {cron_expr}")
            break  # Only one schedule trigger per agent


async def unregister_agent_cron(agent_id: str):
    """Remove cron jobs for a paused/retired agent."""
    global _scheduler
    if not _scheduler:
        return

    job_id = f"agent_cron_{agent_id}"
    existing = _scheduler.get_job(job_id)
    if existing:
        _scheduler.remove_job(job_id)
        logger.info(f"Removed cron job for agent {agent_id}")


async def init_scheduler() -> AsyncIOScheduler:
    """
    Initialize and start the APScheduler.
    Called from app lifespan startup.
    """
    global _scheduler

    _scheduler = AsyncIOScheduler()

    # Add periodic condition-check job (every 5 minutes)
    _scheduler.add_job(
        _execute_scheduled_agents,
        trigger=IntervalTrigger(minutes=5),
        id="automation_condition_check",
        name="Automation Condition Check",
        replace_existing=True,
    )

    # Register cron jobs for existing LIVE/SHADOW agents
    async with AsyncSessionLocal() as db:
        try:
            result = await db.execute(
                select(AIAgent).where(
                    AIAgent.status.in_([AgentStatus.LIVE, AgentStatus.SHADOW])
                )
            )
            agents = result.scalars().all()
            for agent in agents:
                await register_agent_cron(agent)
            logger.info(f"Loaded {len(agents)} existing agent schedules")
        except Exception as e:
            logger.error(f"Failed to load existing agent schedules: {e}")

    _scheduler.start()
    logger.info("Automation scheduler started")
    return _scheduler


async def shutdown_scheduler():
    """Shutdown the scheduler gracefully."""
    global _scheduler
    if _scheduler:
        _scheduler.shutdown(wait=False)
        _scheduler = None
        logger.info("Automation scheduler shut down")


def get_scheduler() -> Optional[AsyncIOScheduler]:
    """Get the global scheduler instance."""
    return _scheduler

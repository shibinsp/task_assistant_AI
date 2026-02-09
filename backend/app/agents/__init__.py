"""
TaskPulse - AI Assistant - Multi-Agent System

This module provides a comprehensive multi-agent framework for intelligent
task management, including:

- AI Agents: Unblock, Decomposer, Predictor, Skill Matcher, Coach
- Integration Agents: Jira, GitHub, Slack, Email, Calendar
- Conversational Agents: In-App Chat, Slack Bot, Teams Bot

The orchestrator coordinates all agents through an event-driven architecture.
"""

from .base import (
    BaseAgent,
    AgentCapability,
    AgentStatus,
    AgentEvent,
    AgentResult,
    AgentError,
)
from .context import AgentContext, ConversationMessage
from .event_bus import AgentEventBus, EventType
from .orchestrator import AgentOrchestrator

__all__ = [
    # Base classes
    "BaseAgent",
    "AgentCapability",
    "AgentStatus",
    "AgentEvent",
    "AgentResult",
    "AgentError",
    # Context
    "AgentContext",
    "ConversationMessage",
    # Event system
    "AgentEventBus",
    "EventType",
    # Orchestrator
    "AgentOrchestrator",
]

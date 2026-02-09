"""
Integration Agents

External integration agents for connecting TaskPulse - AI Assistant with:
- Jira
- GitHub
- Slack
- Email
- Calendar
"""

from .base_integration import BaseIntegrationAgent, IntegrationStatus, SyncResult
from .jira_agent import JiraAgent
from .github_agent import GitHubAgent
from .slack_agent import SlackAgent
from .email_agent import EmailAgent
from .calendar_agent import CalendarAgent

__all__ = [
    "BaseIntegrationAgent",
    "IntegrationStatus",
    "SyncResult",
    "JiraAgent",
    "GitHubAgent",
    "SlackAgent",
    "EmailAgent",
    "CalendarAgent",
]

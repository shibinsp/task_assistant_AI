"""
Conversational Agents

Chat and messaging interfaces for TaskPulse - AI Assistant:
- In-app chat widget
- Slack bot
- Teams bot
"""

from .chat_agent import ChatAgent
from .slack_bot import SlackBotAgent
from .teams_bot import TeamsBotAgent

__all__ = [
    "ChatAgent",
    "SlackBotAgent",
    "TeamsBotAgent",
]

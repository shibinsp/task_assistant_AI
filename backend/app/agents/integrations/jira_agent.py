"""
Jira Integration Agent

Bidirectional sync between TaskPulse - AI Assistant and Jira.
Supports issue sync, status updates, and webhook handling.
"""

import logging
from typing import Any, Dict, List, Optional

from ..base import AgentCapability, EventType
from ..context import AgentContext
from .base_integration import (
    BaseIntegrationAgent,
    ExternalItem,
    IntegrationStatus,
    SyncDirection,
    WebhookEvent,
)

logger = logging.getLogger(__name__)


class JiraAgent(BaseIntegrationAgent):
    """
    Jira integration agent for bidirectional issue sync.

    Features:
    - Sync Jira issues to TaskPulse tasks
    - Push TaskPulse updates to Jira
    - Handle Jira webhooks for real-time updates
    - Map custom fields and statuses
    """

    integration_type = "jira"
    name = "jira_agent"
    description = "Bidirectional sync with Jira for issue tracking"
    version = "1.0.0"

    capabilities = [AgentCapability.JIRA_SYNC]

    api_base_url = "https://api.atlassian.com/ex/jira"
    api_version = "3"

    sync_direction = SyncDirection.BIDIRECTIONAL
    sync_interval_minutes = 10

    # Status mapping: Jira -> TaskPulse
    STATUS_MAP_INBOUND = {
        "To Do": "pending",
        "In Progress": "in_progress",
        "In Review": "in_review",
        "Done": "completed",
        "Blocked": "blocked",
    }

    # Status mapping: TaskPulse -> Jira
    STATUS_MAP_OUTBOUND = {
        "pending": "To Do",
        "in_progress": "In Progress",
        "in_review": "In Review",
        "completed": "Done",
        "blocked": "Blocked",
    }

    # Priority mapping
    PRIORITY_MAP_INBOUND = {
        "Highest": "critical",
        "High": "high",
        "Medium": "medium",
        "Low": "low",
        "Lowest": "low",
    }

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        super().__init__(config)
        self.cloud_id: Optional[str] = None
        self.project_key: Optional[str] = None
        self.jql_filter: Optional[str] = None

        if config:
            self.cloud_id = config.get("cloud_id")
            self.project_key = config.get("project_key")
            self.jql_filter = config.get("jql_filter")

    async def sync_inbound(self, context: AgentContext) -> List[Dict[str, Any]]:
        """Sync Jira issues to TaskPulse"""
        synced_items = []

        try:
            # In production, this would call Jira API
            # GET /rest/api/3/search?jql={jql}

            # Mock Jira issues for demonstration
            jira_issues = await self._fetch_jira_issues()

            for issue in jira_issues:
                task_data = self._map_issue_to_task(issue)
                synced_items.append({
                    **task_data,
                    "is_new": not self._task_exists(task_data["external_id"]),
                    "source": "jira",
                })

            logger.info(f"Synced {len(synced_items)} issues from Jira")

        except Exception as e:
            logger.error(f"Jira inbound sync error: {e}")
            raise

        return synced_items

    async def sync_outbound(self, context: AgentContext) -> Dict[str, Any]:
        """Sync TaskPulse tasks to Jira"""
        result = {"count": 0, "created": 0, "updated": 0, "errors": []}

        try:
            # Get tasks that need syncing
            tasks = await self._get_tasks_to_sync(context)

            for task in tasks:
                try:
                    if task.get("jira_issue_key"):
                        # Update existing issue
                        await self._update_jira_issue(task)
                        result["updated"] += 1
                    else:
                        # Create new issue
                        await self._create_jira_issue(task)
                        result["created"] += 1

                    result["count"] += 1

                except Exception as e:
                    result["errors"].append(f"Task {task.get('id')}: {str(e)}")

            logger.info(f"Synced {result['count']} tasks to Jira")

        except Exception as e:
            logger.error(f"Jira outbound sync error: {e}")
            raise

        return result

    async def handle_webhook(self, event: WebhookEvent) -> Dict[str, Any]:
        """Handle Jira webhook events"""
        result = {"processed": False, "action": None}

        try:
            webhook_event = event.event_type
            payload = event.payload

            if webhook_event == "jira:issue_created":
                result = await self._handle_issue_created(payload)

            elif webhook_event == "jira:issue_updated":
                result = await self._handle_issue_updated(payload)

            elif webhook_event == "jira:issue_deleted":
                result = await self._handle_issue_deleted(payload)

            elif webhook_event.startswith("comment"):
                result = await self._handle_comment(webhook_event, payload)

            result["processed"] = True
            logger.info(f"Processed Jira webhook: {webhook_event}")

        except Exception as e:
            logger.error(f"Jira webhook error: {e}")
            result["error"] = str(e)

        return result

    async def _fetch_jira_issues(self) -> List[Dict[str, Any]]:
        """Fetch issues from Jira API"""
        # Mock response for demonstration
        return [
            {
                "key": "PROJ-123",
                "fields": {
                    "summary": "Implement user authentication",
                    "description": "Add OAuth2 authentication flow",
                    "status": {"name": "In Progress"},
                    "priority": {"name": "High"},
                    "assignee": {"emailAddress": "dev@company.com"},
                    "created": "2024-01-15T10:00:00Z",
                    "updated": "2024-01-16T14:30:00Z",
                    "timeestimate": 28800,  # seconds
                    "timespent": 14400,
                },
                "self": "https://company.atlassian.net/rest/api/3/issue/PROJ-123",
            },
            {
                "key": "PROJ-124",
                "fields": {
                    "summary": "Fix database connection pooling",
                    "description": "Connection pool exhaustion under load",
                    "status": {"name": "To Do"},
                    "priority": {"name": "Highest"},
                    "assignee": None,
                    "created": "2024-01-16T09:00:00Z",
                    "updated": "2024-01-16T09:00:00Z",
                },
                "self": "https://company.atlassian.net/rest/api/3/issue/PROJ-124",
            },
        ]

    def _map_issue_to_task(self, issue: Dict[str, Any]) -> Dict[str, Any]:
        """Map Jira issue to TaskPulse task format"""
        fields = issue.get("fields", {})

        # Map status
        jira_status = fields.get("status", {}).get("name", "To Do")
        status = self.STATUS_MAP_INBOUND.get(jira_status, "pending")

        # Map priority
        jira_priority = fields.get("priority", {}).get("name", "Medium")
        priority = self.PRIORITY_MAP_INBOUND.get(jira_priority, "medium")

        # Convert time estimate from seconds to hours
        estimate_seconds = fields.get("timeestimate") or 0
        estimate_hours = estimate_seconds / 3600 if estimate_seconds else None

        spent_seconds = fields.get("timespent") or 0
        spent_hours = spent_seconds / 3600 if spent_seconds else None

        return {
            "external_id": issue["key"],
            "external_url": issue.get("self", "").replace("/rest/api/3/issue/", "/browse/"),
            "title": fields.get("summary", ""),
            "description": fields.get("description", ""),
            "status": status,
            "priority": priority,
            "estimated_hours": estimate_hours,
            "actual_hours": spent_hours,
            "assignee_email": fields.get("assignee", {}).get("emailAddress") if fields.get("assignee") else None,
            "metadata": {
                "jira_key": issue["key"],
                "jira_status": jira_status,
                "jira_priority": jira_priority,
            },
        }

    def _task_exists(self, external_id: str) -> bool:
        """Check if task already exists in TaskPulse"""
        # In production, query database
        return False

    async def _get_tasks_to_sync(self, context: AgentContext) -> List[Dict[str, Any]]:
        """Get TaskPulse tasks that need syncing to Jira"""
        # In production, query for tasks with jira_sync enabled
        return []

    async def _create_jira_issue(self, task: Dict[str, Any]) -> str:
        """Create a new Jira issue from TaskPulse task"""
        # POST /rest/api/3/issue
        # Returns issue key

        jira_status = self.STATUS_MAP_OUTBOUND.get(task.get("status"), "To Do")

        payload = {
            "fields": {
                "project": {"key": self.project_key or "PROJ"},
                "summary": task.get("title"),
                "description": task.get("description", ""),
                "issuetype": {"name": "Task"},
            }
        }

        logger.info(f"Would create Jira issue: {payload}")
        return "PROJ-NEW"

    async def _update_jira_issue(self, task: Dict[str, Any]) -> None:
        """Update existing Jira issue from TaskPulse task"""
        # PUT /rest/api/3/issue/{issueKey}

        issue_key = task.get("jira_issue_key")
        jira_status = self.STATUS_MAP_OUTBOUND.get(task.get("status"), "To Do")

        payload = {
            "fields": {
                "summary": task.get("title"),
                "description": task.get("description", ""),
            }
        }

        logger.info(f"Would update Jira issue {issue_key}: {payload}")

    async def _handle_issue_created(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Handle issue created webhook"""
        issue = payload.get("issue", {})
        task_data = self._map_issue_to_task(issue)

        return {
            "action": "create_task",
            "task_data": task_data,
        }

    async def _handle_issue_updated(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Handle issue updated webhook"""
        issue = payload.get("issue", {})
        changelog = payload.get("changelog", {})

        task_data = self._map_issue_to_task(issue)

        # Check what changed
        changes = []
        for item in changelog.get("items", []):
            changes.append({
                "field": item.get("field"),
                "from": item.get("fromString"),
                "to": item.get("toString"),
            })

        return {
            "action": "update_task",
            "task_data": task_data,
            "changes": changes,
        }

    async def _handle_issue_deleted(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Handle issue deleted webhook"""
        issue = payload.get("issue", {})

        return {
            "action": "archive_task",
            "external_id": issue.get("key"),
        }

    async def _handle_comment(
        self,
        event_type: str,
        payload: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Handle comment webhook events"""
        comment = payload.get("comment", {})

        return {
            "action": "sync_comment",
            "external_id": payload.get("issue", {}).get("key"),
            "comment": {
                "author": comment.get("author", {}).get("displayName"),
                "body": comment.get("body"),
                "created": comment.get("created"),
            },
        }

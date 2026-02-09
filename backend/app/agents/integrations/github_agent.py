"""
GitHub Integration Agent

Sync between TaskPulse AI and GitHub for issues, PRs, and commits.
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


class GitHubAgent(BaseIntegrationAgent):
    """
    GitHub integration agent for issues, PRs, and commits.

    Features:
    - Sync GitHub issues to TaskPulse tasks
    - Link PRs to tasks
    - Auto-complete tasks on PR merge
    - Track commit activity
    - Handle GitHub webhooks
    """

    integration_type = "github"
    name = "github_agent"
    description = "GitHub integration for issues, PRs, and code tracking"
    version = "1.0.0"

    capabilities = [AgentCapability.GITHUB_SYNC]

    api_base_url = "https://api.github.com"
    api_version = "2022-11-28"

    sync_direction = SyncDirection.BIDIRECTIONAL
    sync_interval_minutes = 5

    # Issue state mapping
    STATE_MAP_INBOUND = {
        "open": "pending",
        "closed": "completed",
    }

    # Label to priority mapping
    PRIORITY_LABELS = {
        "priority: critical": "critical",
        "priority: high": "high",
        "priority: medium": "medium",
        "priority: low": "low",
        "bug": "high",
        "enhancement": "medium",
    }

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        super().__init__(config)
        self.owner: Optional[str] = None
        self.repo: Optional[str] = None
        self.sync_issues = True
        self.sync_prs = True
        self.auto_complete_on_merge = True

        if config:
            self.owner = config.get("owner")
            self.repo = config.get("repo")
            self.sync_issues = config.get("sync_issues", True)
            self.sync_prs = config.get("sync_prs", True)
            self.auto_complete_on_merge = config.get("auto_complete_on_merge", True)

    async def sync_inbound(self, context: AgentContext) -> List[Dict[str, Any]]:
        """Sync GitHub issues and PRs to TaskPulse"""
        synced_items = []

        try:
            if self.sync_issues:
                issues = await self._fetch_github_issues()
                for issue in issues:
                    task_data = self._map_issue_to_task(issue)
                    synced_items.append({
                        **task_data,
                        "is_new": not self._task_exists(task_data["external_id"]),
                        "source": "github_issue",
                    })

            if self.sync_prs:
                prs = await self._fetch_github_prs()
                for pr in prs:
                    task_data = self._map_pr_to_task(pr)
                    synced_items.append({
                        **task_data,
                        "is_new": not self._task_exists(task_data["external_id"]),
                        "source": "github_pr",
                    })

            logger.info(f"Synced {len(synced_items)} items from GitHub")

        except Exception as e:
            logger.error(f"GitHub inbound sync error: {e}")
            raise

        return synced_items

    async def sync_outbound(self, context: AgentContext) -> Dict[str, Any]:
        """Sync TaskPulse tasks to GitHub issues"""
        result = {"count": 0, "created": 0, "updated": 0, "errors": []}

        try:
            tasks = await self._get_tasks_to_sync(context)

            for task in tasks:
                try:
                    if task.get("github_issue_number"):
                        await self._update_github_issue(task)
                        result["updated"] += 1
                    else:
                        await self._create_github_issue(task)
                        result["created"] += 1

                    result["count"] += 1

                except Exception as e:
                    result["errors"].append(f"Task {task.get('id')}: {str(e)}")

            logger.info(f"Synced {result['count']} tasks to GitHub")

        except Exception as e:
            logger.error(f"GitHub outbound sync error: {e}")
            raise

        return result

    async def handle_webhook(self, event: WebhookEvent) -> Dict[str, Any]:
        """Handle GitHub webhook events"""
        result = {"processed": False, "action": None}

        try:
            event_type = event.event_type
            payload = event.payload

            handlers = {
                "issues": self._handle_issue_event,
                "pull_request": self._handle_pr_event,
                "push": self._handle_push_event,
                "issue_comment": self._handle_comment_event,
            }

            handler = handlers.get(event_type)
            if handler:
                result = await handler(payload)
                result["processed"] = True
                logger.info(f"Processed GitHub webhook: {event_type}")
            else:
                result["skipped"] = True
                result["reason"] = f"Unhandled event type: {event_type}"

        except Exception as e:
            logger.error(f"GitHub webhook error: {e}")
            result["error"] = str(e)

        return result

    async def _fetch_github_issues(self) -> List[Dict[str, Any]]:
        """Fetch issues from GitHub API"""
        # GET /repos/{owner}/{repo}/issues
        # Mock response
        return [
            {
                "number": 42,
                "title": "Add dark mode support",
                "body": "Users have requested dark mode theme",
                "state": "open",
                "labels": [{"name": "enhancement"}, {"name": "priority: medium"}],
                "assignee": {"login": "developer1"},
                "created_at": "2024-01-15T10:00:00Z",
                "updated_at": "2024-01-16T14:30:00Z",
                "html_url": "https://github.com/company/repo/issues/42",
            },
            {
                "number": 43,
                "title": "Fix memory leak in worker process",
                "body": "Memory usage grows over time",
                "state": "open",
                "labels": [{"name": "bug"}, {"name": "priority: critical"}],
                "assignee": None,
                "created_at": "2024-01-16T09:00:00Z",
                "updated_at": "2024-01-16T09:00:00Z",
                "html_url": "https://github.com/company/repo/issues/43",
            },
        ]

    async def _fetch_github_prs(self) -> List[Dict[str, Any]]:
        """Fetch pull requests from GitHub API"""
        # GET /repos/{owner}/{repo}/pulls
        return [
            {
                "number": 100,
                "title": "feat: Add user preferences API",
                "body": "Implements user preferences endpoint\n\nCloses #42",
                "state": "open",
                "draft": False,
                "user": {"login": "developer1"},
                "head": {"ref": "feature/user-preferences"},
                "base": {"ref": "main"},
                "created_at": "2024-01-16T10:00:00Z",
                "updated_at": "2024-01-16T15:00:00Z",
                "html_url": "https://github.com/company/repo/pull/100",
                "requested_reviewers": [{"login": "reviewer1"}],
            },
        ]

    def _map_issue_to_task(self, issue: Dict[str, Any]) -> Dict[str, Any]:
        """Map GitHub issue to TaskPulse task"""
        state = issue.get("state", "open")
        status = self.STATE_MAP_INBOUND.get(state, "pending")

        # Determine priority from labels
        priority = "medium"
        labels = [l.get("name", "").lower() for l in issue.get("labels", [])]
        for label in labels:
            if label in self.PRIORITY_LABELS:
                priority = self.PRIORITY_LABELS[label]
                break

        # Determine task type from labels
        task_type = "task"
        if "bug" in labels:
            task_type = "bug"
        elif "enhancement" in labels or "feature" in labels:
            task_type = "feature"

        return {
            "external_id": f"github_issue_{issue['number']}",
            "external_url": issue.get("html_url", ""),
            "title": issue.get("title", ""),
            "description": issue.get("body", ""),
            "status": status,
            "priority": priority,
            "assignee_username": issue.get("assignee", {}).get("login") if issue.get("assignee") else None,
            "tags": labels,
            "metadata": {
                "github_issue_number": issue["number"],
                "github_type": "issue",
                "task_type": task_type,
            },
        }

    def _map_pr_to_task(self, pr: Dict[str, Any]) -> Dict[str, Any]:
        """Map GitHub PR to TaskPulse task"""
        state = pr.get("state", "open")
        is_draft = pr.get("draft", False)

        if state == "closed":
            status = "completed"
        elif is_draft:
            status = "pending"
        else:
            status = "in_review"

        return {
            "external_id": f"github_pr_{pr['number']}",
            "external_url": pr.get("html_url", ""),
            "title": f"[PR] {pr.get('title', '')}",
            "description": pr.get("body", ""),
            "status": status,
            "priority": "medium",
            "assignee_username": pr.get("user", {}).get("login"),
            "tags": ["pull_request"],
            "metadata": {
                "github_pr_number": pr["number"],
                "github_type": "pr",
                "branch": pr.get("head", {}).get("ref"),
                "base_branch": pr.get("base", {}).get("ref"),
                "is_draft": is_draft,
                "reviewers": [r.get("login") for r in pr.get("requested_reviewers", [])],
            },
        }

    def _task_exists(self, external_id: str) -> bool:
        """Check if task already exists"""
        return False

    async def _get_tasks_to_sync(self, context: AgentContext) -> List[Dict[str, Any]]:
        """Get tasks to sync to GitHub"""
        return []

    async def _create_github_issue(self, task: Dict[str, Any]) -> int:
        """Create GitHub issue from task"""
        # POST /repos/{owner}/{repo}/issues
        logger.info(f"Would create GitHub issue: {task.get('title')}")
        return 999

    async def _update_github_issue(self, task: Dict[str, Any]) -> None:
        """Update GitHub issue from task"""
        # PATCH /repos/{owner}/{repo}/issues/{issue_number}
        issue_number = task.get("github_issue_number")
        logger.info(f"Would update GitHub issue #{issue_number}")

    async def _handle_issue_event(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Handle issue events (opened, closed, edited, etc.)"""
        action = payload.get("action")
        issue = payload.get("issue", {})

        task_data = self._map_issue_to_task(issue)

        if action == "opened":
            return {"action": "create_task", "task_data": task_data}
        elif action == "closed":
            return {"action": "complete_task", "task_data": task_data}
        elif action == "reopened":
            task_data["status"] = "pending"
            return {"action": "update_task", "task_data": task_data}
        elif action == "edited":
            return {"action": "update_task", "task_data": task_data}
        elif action == "assigned":
            return {"action": "assign_task", "task_data": task_data}

        return {"action": None}

    async def _handle_pr_event(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Handle pull request events"""
        action = payload.get("action")
        pr = payload.get("pull_request", {})

        task_data = self._map_pr_to_task(pr)

        if action == "opened":
            return {"action": "create_task", "task_data": task_data}
        elif action == "closed":
            if pr.get("merged"):
                # PR was merged
                result = {"action": "complete_task", "task_data": task_data}

                # Check if PR closes any issues
                if self.auto_complete_on_merge:
                    linked_issues = self._extract_linked_issues(pr.get("body", ""))
                    result["linked_issues"] = linked_issues

                return result
            else:
                # PR was closed without merge
                return {"action": "archive_task", "task_data": task_data}
        elif action == "ready_for_review":
            task_data["status"] = "in_review"
            return {"action": "update_task", "task_data": task_data}
        elif action == "converted_to_draft":
            task_data["status"] = "in_progress"
            return {"action": "update_task", "task_data": task_data}

        return {"action": None}

    async def _handle_push_event(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Handle push events (commits)"""
        commits = payload.get("commits", [])
        ref = payload.get("ref", "")

        commit_info = []
        for commit in commits:
            commit_info.append({
                "sha": commit.get("id", "")[:7],
                "message": commit.get("message", ""),
                "author": commit.get("author", {}).get("name"),
            })

        return {
            "action": "log_activity",
            "branch": ref.replace("refs/heads/", ""),
            "commits": commit_info,
        }

    async def _handle_comment_event(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Handle issue comment events"""
        action = payload.get("action")
        comment = payload.get("comment", {})
        issue = payload.get("issue", {})

        if action == "created":
            return {
                "action": "add_comment",
                "external_id": f"github_issue_{issue.get('number')}",
                "comment": {
                    "author": comment.get("user", {}).get("login"),
                    "body": comment.get("body"),
                    "created_at": comment.get("created_at"),
                },
            }

        return {"action": None}

    def _extract_linked_issues(self, body: str) -> List[int]:
        """Extract issue numbers from PR body (Closes #123, Fixes #456)"""
        import re

        patterns = [
            r"(?:close[sd]?|fix(?:e[sd])?|resolve[sd]?)\s*#(\d+)",
        ]

        issues = []
        body_lower = body.lower()

        for pattern in patterns:
            matches = re.findall(pattern, body_lower)
            issues.extend([int(m) for m in matches])

        return list(set(issues))

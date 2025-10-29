"""
AutoCodit Agent - GitHub Event Processors

Processes different types of GitHub webhook events and creates
tasks for the coding agent.
"""

from typing import Dict, Any, Optional
import re

import structlog

from app.schemas.github import WebhookEvent
from app.services.task_service import TaskService
from app.services.github_service import GitHubService
from app.core.config import get_settings

logger = structlog.get_logger()


class GitHubEventProcessor:
    """Process GitHub webhook events"""
    
    def __init__(self):
        self.settings = get_settings()
        self.task_service = TaskService()
        self.github_service = GitHubService()
    
    async def process_event(self, event: WebhookEvent) -> None:
        """Route event to appropriate processor"""
        try:
            if event.event_type == "issues":
                await self._process_issues_event(event)
            elif event.event_type == "issue_comment":
                await self._process_issue_comment_event(event)
            elif event.event_type == "pull_request":
                await self._process_pull_request_event(event)
            elif event.event_type == "pull_request_review":
                await self._process_pull_request_review_event(event)
            elif event.event_type == "push":
                await self._process_push_event(event)
            else:
                logger.debug(
                    "Unhandled event type",
                    event_type=event.event_type,
                    delivery_id=event.delivery_id
                )
        
        except Exception as e:
            logger.error(
                "Error processing GitHub event",
                event_type=event.event_type,
                delivery_id=event.delivery_id,
                error=str(e)
            )
    
    async def _process_issues_event(self, event: WebhookEvent) -> None:
        """Process issues events (opened, assigned, labeled, etc.)"""
        payload = event.payload
        action = payload.get("action")
        issue = payload.get("issue", {})
        repository = payload.get("repository", {})
        
        logger.info(
            "Processing issues event",
            action=action,
            issue_number=issue.get("number"),
            repository=repository.get("full_name")
        )
        
        # Check if issue is assigned to our bot
        if action == "assigned":
            assignee = payload.get("assignee", {})
            if assignee.get("login") == self.settings.GITHUB_BOT_LOGIN:
                await self._create_task_from_issue(issue, repository)
        
        # Check for specific labels
        elif action == "labeled":
            label = payload.get("label", {})
            label_name = label.get("name", "").lower()
            
            if label_name.startswith("agent:"):
                agent_action = label_name.replace("agent:", "")
                await self._create_task_from_issue(
                    issue, repository, agent_action=agent_action
                )
    
    async def _process_issue_comment_event(self, event: WebhookEvent) -> None:
        """Process issue comment events"""
        payload = event.payload
        action = payload.get("action")
        
        if action != "created":
            return
        
        comment = payload.get("comment", {})
        issue = payload.get("issue", {})
        repository = payload.get("repository", {})
        
        comment_body = comment.get("body", "")
        
        # Check if bot is mentioned
        bot_mention = f"@{self.settings.GITHUB_BOT_LOGIN}"
        if bot_mention not in comment_body:
            return
        
        logger.info(
            "Processing bot mention in comment",
            issue_number=issue.get("number"),
            repository=repository.get("full_name"),
            comment_id=comment.get("id")
        )
        
        # Parse bot commands
        command = self._parse_bot_command(comment_body)
        if command:
            await self._create_task_from_comment(
                issue, repository, comment, command
            )
    
    async def _process_pull_request_event(self, event: WebhookEvent) -> None:
        """Process pull request events"""
        payload = event.payload
        action = payload.get("action")
        pull_request = payload.get("pull_request", {})
        repository = payload.get("repository", {})
        
        logger.info(
            "Processing pull request event",
            action=action,
            pr_number=pull_request.get("number"),
            repository=repository.get("full_name")
        )
        
        # Handle PR events that might trigger agent actions
        if action in ["opened", "synchronize", "reopened"]:
            # Check if PR was created by our bot
            pr_author = pull_request.get("user", {}).get("login")
            if pr_author == self.settings.GITHUB_BOT_LOGIN:
                # This is our bot's PR, potentially update status
                await self._update_bot_pr_status(pull_request, repository)
    
    async def _process_pull_request_review_event(self, event: WebhookEvent) -> None:
        """Process pull request review events"""
        payload = event.payload
        action = payload.get("action")
        review = payload.get("review", {})
        pull_request = payload.get("pull_request", {})
        repository = payload.get("repository", {})
        
        # Handle review feedback for bot PRs
        if action == "submitted":
            pr_author = pull_request.get("user", {}).get("login")
            if pr_author == self.settings.GITHUB_BOT_LOGIN:
                review_state = review.get("state")
                if review_state == "changes_requested":
                    await self._handle_pr_changes_requested(
                        pull_request, repository, review
                    )
    
    async def _process_push_event(self, event: WebhookEvent) -> None:
        """Process push events"""
        payload = event.payload
        repository = payload.get("repository", {})
        ref = payload.get("ref", "")
        
        # Only process pushes to main/master branch
        if ref not in ["refs/heads/main", "refs/heads/master"]:
            return
        
        logger.info(
            "Processing push event",
            repository=repository.get("full_name"),
            ref=ref,
            commits=len(payload.get("commits", []))
        )
        
        # TODO: Handle base branch updates that might affect ongoing tasks
    
    def _parse_bot_command(self, comment_body: str) -> Optional[Dict[str, Any]]:
        """Parse bot commands from comment text"""
        bot_mention = f"@{self.settings.GITHUB_BOT_LOGIN}"
        
        # Find bot mention and extract command
        mention_pattern = rf"{re.escape(bot_mention)}\s+([^\n]+)"
        match = re.search(mention_pattern, comment_body, re.IGNORECASE)
        
        if not match:
            return None
        
        command_text = match.group(1).strip()
        
        # Parse different command formats
        command_patterns = [
            (r"plan:?\s+(.+)", "plan"),
            (r"apply:?\s+(.+)", "apply"),
            (r"fix:?\s+(.+)", "fix"),
            (r"review:?\s+(.+)", "review"),
            (r"test:?\s+(.+)", "test"),
            (r"stop", "stop"),
            (r"status", "status"),
        ]
        
        for pattern, command_type in command_patterns:
            match = re.match(pattern, command_text, re.IGNORECASE)
            if match:
                if command_type in ["stop", "status"]:
                    return {"type": command_type}
                else:
                    return {
                        "type": command_type,
                        "description": match.group(1).strip()
                    }
        
        # Default to "plan" if no specific command found
        return {
            "type": "plan",
            "description": command_text
        }
    
    async def _create_task_from_issue(
        self,
        issue: Dict[str, Any],
        repository: Dict[str, Any],
        agent_action: str = "plan"
    ) -> None:
        """Create task from issue assignment or labeling"""
        task_data = {
            "title": issue.get("title", ""),
            "description": issue.get("body", ""),
            "repository": repository.get("full_name"),
            "issue_number": issue.get("number"),
            "action_type": agent_action,
            "triggered_by": "issue_assignment",
            "github_installation_id": None,  # TODO: Get from payload
        }
        
        await self.task_service.create_task(task_data)
        
        logger.info(
            "Created task from issue",
            issue_number=issue.get("number"),
            repository=repository.get("full_name"),
            action_type=agent_action
        )
    
    async def _create_task_from_comment(
        self,
        issue: Dict[str, Any],
        repository: Dict[str, Any],
        comment: Dict[str, Any],
        command: Dict[str, Any]
    ) -> None:
        """Create task from bot comment command"""
        task_data = {
            "title": f"{command['type'].title()}: {issue.get('title', '')}",
            "description": command.get("description", issue.get("body", "")),
            "repository": repository.get("full_name"),
            "issue_number": issue.get("number"),
            "comment_id": comment.get("id"),
            "action_type": command["type"],
            "triggered_by": "comment_command",
            "github_installation_id": None,  # TODO: Get from payload
        }
        
        await self.task_service.create_task(task_data)
        
        logger.info(
            "Created task from comment command",
            issue_number=issue.get("number"),
            repository=repository.get("full_name"),
            command_type=command["type"]
        )
    
    async def _update_bot_pr_status(
        self,
        pull_request: Dict[str, Any],
        repository: Dict[str, Any]
    ) -> None:
        """Update status of bot-created PR"""
        # TODO: Implement PR status updates
        pass
    
    async def _handle_pr_changes_requested(
        self,
        pull_request: Dict[str, Any],
        repository: Dict[str, Any],
        review: Dict[str, Any]
    ) -> None:
        """Handle changes requested on bot PR"""
        # TODO: Create task to address review feedback
        pass


# Event processor instance
event_processor = GitHubEventProcessor()


async def process_github_event(event: WebhookEvent) -> None:
    """Process GitHub webhook event"""
    await event_processor.process_event(event)
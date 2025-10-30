import asyncio
import logging
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, or_, desc
from sqlalchemy.orm import selectinload

from ..models.task import Task, TaskStatus, TaskPriority
from ..models.session import Session, SessionStatus
from ..models.user import User
from ..models.repository import Repository
from ..core.database import get_db
from .github_service import GitHubService
from .ai_service import AIOrchestrator
from .runner_service import RunnerService

logger = logging.getLogger(__name__)


class TaskService:
    def __init__(
        self,
        github_service: GitHubService,
        ai_service: AIOrchestrator,
        runner_service: RunnerService
    ):
        self.github_service = github_service
        self.ai_service = ai_service
        self.runner_service = runner_service
    
    async def create_task(
        self,
        user_id: str,
        repository_id: str,
        title: str,
        description: str,
        priority: TaskPriority = TaskPriority.NORMAL,
        agent_config_id: Optional[str] = None,
        github_event_type: Optional[str] = None,
        github_event_data: Optional[Dict[str, Any]] = None,
        issue_number: Optional[int] = None,
        pull_request_number: Optional[int] = None,
        base_branch: str = "main",
        auto_merge: bool = False,
        timeout_minutes: int = 60,
        db: AsyncSession = None
    ) -> Task:
        """Create a new coding task"""
        
        if db is None:
            db = await anext(get_db())
        
        try:
            # Create the task
            task = Task(
                title=title,
                description=description,
                status=TaskStatus.PENDING,
                priority=priority,
                repository_id=repository_id,
                user_id=user_id,
                github_event_type=github_event_type,
                github_event_data=github_event_data or {},
                issue_number=issue_number,
                pull_request_number=pull_request_number,
                base_branch=base_branch,
                auto_merge=auto_merge,
                timeout_minutes=timeout_minutes
            )
            
            db.add(task)
            await db.commit()
            await db.refresh(task)
            
            logger.info(f"Created task {task.id} for repository {repository_id}")
            
            # Queue task for execution
            await self._queue_task(task)
            
            return task
            
        except Exception as e:
            await db.rollback()
            logger.error(f"Error creating task: {e}")
            raise
    
    async def get_task(
        self,
        task_id: str,
        user_id: Optional[str] = None,
        db: AsyncSession = None
    ) -> Optional[Task]:
        """Get task by ID"""
        
        if db is None:
            db = await anext(get_db())
        
        query = select(Task).options(
            selectinload(Task.repository),
            selectinload(Task.user),
            selectinload(Task.sessions)
        ).where(Task.id == task_id)
        
        if user_id:
            query = query.where(Task.user_id == user_id)
        
        result = await db.execute(query)
        return result.scalar_one_or_none()
    
    async def create_task_from_github_event(
        self,
        event_type: str,
        event_data: Dict[str, Any],
        installation_id: int,
        db: AsyncSession = None
    ) -> Optional[Task]:
        """Create task from GitHub webhook event"""
        
        if db is None:
            db = await anext(get_db())
        
        try:
            # Extract task details based on event type
            task_data = await self._extract_task_from_event(event_type, event_data)
            if not task_data:
                return None
            
            # Find repository and user
            repository_data = event_data.get("repository", {})
            repo_full_name = repository_data.get("full_name")
            
            repo_result = await db.execute(
                select(Repository).where(Repository.full_name == repo_full_name)
            )
            repository = repo_result.scalar_one_or_none()
            
            if not repository or not repository.agent_enabled:
                return None
            
            # Find user
            user_data = event_data.get("sender", {})
            user_result = await db.execute(
                select(User).where(User.github_id == user_data.get("id"))
            )
            user = user_result.scalar_one_or_none()
            
            if not user:
                user = User(
                    github_id=user_data.get("id"),
                    username=user_data.get("login"),
                    avatar_url=user_data.get("avatar_url")
                )
                db.add(user)
                await db.commit()
                await db.refresh(user)
            
            # Create task
            task = await self.create_task(
                user_id=user.id,
                repository_id=repository.id,
                title=task_data["title"],
                description=task_data["description"],
                github_event_type=event_type,
                github_event_data=event_data,
                issue_number=task_data.get("issue_number"),
                pull_request_number=task_data.get("pull_request_number"),
                base_branch=task_data.get("base_branch", repository.default_branch),
                db=db
            )
            
            return task
            
        except Exception as e:
            logger.error(f"Error creating task from GitHub event: {e}")
            raise
    
    async def _extract_task_from_event(
        self,
        event_type: str,
        event_data: Dict[str, Any]
    ) -> Optional[Dict[str, Any]]:
        """Extract task information from GitHub event"""
        
        if event_type == "issues":
            action = event_data.get("action")
            issue = event_data.get("issue", {})
            
            if action == "assigned":
                assignee = event_data.get("assignee", {})
                if assignee.get("type") == "Bot":
                    return {
                        "title": f"Fix issue: {issue.get('title')}",
                        "description": issue.get("body", ""),
                        "issue_number": issue.get("number")
                    }
        
        elif event_type == "issue_comment":
            action = event_data.get("action")
            comment = event_data.get("comment", {})
            issue = event_data.get("issue", {})
            
            if action == "created":
                comment_body = comment.get("body", "")
                if "@autocodit-bot" in comment_body:
                    return {
                        "title": f"Handle comment on: {issue.get('title')}",
                        "description": comment_body,
                        "issue_number": issue.get("number")
                    }
        
        return None
    
    async def _queue_task(self, task: Task):
        """Queue task for background execution"""
        # This would integrate with Celery or similar task queue
        logger.info(f"Queuing task {task.id} for execution")
        # Implementation would go here
        pass
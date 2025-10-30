"""
AutoCodit Agent - Task Worker

Celery worker for executing coding tasks in isolated containers.
"""

import asyncio
from datetime import datetime, timezone
from typing import Dict, Any

import structlog
from celery import current_task

from app.workers.celery_app import celery_app
from app.services.task_service import TaskService
from app.services.runner_service import RunnerService
from app.services.ai_service import AIService
from app.services.github_service import GitHubService
from app.websocket.manager import broadcast_task_update
from app.models.task import TaskStatus

logger = structlog.get_logger()


@celery_app.task(bind=True, name="execute_coding_task", max_retries=3)
def execute_coding_task(self, task_id: str, task_config: Dict[str, Any]):
    """Execute coding task in isolated container"""
    try:
        # Run the async function
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        result = loop.run_until_complete(
            _execute_coding_task_async(self, task_id, task_config)
        )
        
        loop.close()
        return result
    
    except Exception as exc:
        logger.error(
            "Task execution failed",
            task_id=task_id,
            error=str(exc),
            retry_count=self.request.retries
        )
        
        # Retry with exponential backoff
        countdown = 60 * (2 ** self.request.retries)
        raise self.retry(countdown=countdown, exc=exc)


async def _execute_coding_task_async(celery_task, task_id: str, task_config: Dict[str, Any]):
    """Async implementation of task execution"""
    task_service = TaskService()
    runner_service = RunnerService()
    github_service = GitHubService()
    
    try:
        # Update task status to running
        await task_service.update_task_status(task_id, TaskStatus.RUNNING)
        
        # Broadcast task update
        await broadcast_task_update(task_id, {
            "status": "running",
            "progress": 0.1,
            "message": "Starting task execution..."
        })
        
        # Create runner session
        session = await runner_service.create_runner(task_id, task_config)
        
        logger.info(
            "Task execution started",
            task_id=task_id,
            session_id=session.id,
            repository=task_config.get("repository")
        )
        
        # Monitor session execution
        execution_result = await _monitor_task_execution(
            celery_task, task_id, session.id, task_config
        )
        
        # Update final status
        final_status = TaskStatus.COMPLETED if execution_result["success"] else TaskStatus.FAILED
        
        await task_service.update_task_status(
            task_id=task_id,
            status=final_status,
            progress=1.0 if execution_result["success"] else None,
            error_message=execution_result.get("error_message")
        )
        
        # Create GitHub PR if successful
        if execution_result["success"] and task_config.get("github_installation_id"):
            await _create_github_pr(task_id, task_config, execution_result)
        
        # Broadcast completion
        await broadcast_task_update(task_id, {
            "status": final_status.value,
            "progress": 1.0 if execution_result["success"] else None,
            "message": "Task completed" if execution_result["success"] else "Task failed",
            "execution_result": execution_result
        })
        
        return {
            "task_id": task_id,
            "success": execution_result["success"],
            "session_id": session.id,
            "execution_time": execution_result.get("execution_time", 0),
            "tokens_used": execution_result.get("tokens_used", 0),
            "cost": execution_result.get("cost", 0.0)
        }
    
    except Exception as e:
        # Update task status to failed
        await task_service.update_task_status(
            task_id=task_id,
            status=TaskStatus.FAILED,
            error_message=str(e)
        )
        
        # Broadcast failure
        await broadcast_task_update(task_id, {
            "status": "failed",
            "message": f"Task execution failed: {str(e)}"
        })
        
        logger.error(
            "Task execution failed",
            task_id=task_id,
            error=str(e)
        )
        
        raise


async def _monitor_task_execution(
    celery_task,
    task_id: str,
    session_id: str,
    task_config: Dict[str, Any]
) -> Dict[str, Any]:
    """Monitor task execution and provide progress updates"""
    runner_service = RunnerService()
    start_time = datetime.now(timezone.utc)
    
    # Monitoring loop
    while True:
        await asyncio.sleep(10)  # Check every 10 seconds
        
        # Get runner status
        status = await runner_service.get_runner_status(session_id)
        
        if not status:
            logger.warning("Lost connection to runner", session_id=session_id)
            return {
                "success": False,
                "error_message": "Lost connection to runner"
            }
        
        container_status = status.get("status")
        
        # Check if container finished
        if container_status in ["exited", "dead"]:
            exit_code = status.get("exit_code", -1)
            
            # Get final logs
            logs = await runner_service.get_runner_logs(session_id, tail=50)
            
            end_time = datetime.now(timezone.utc)
            execution_time = (end_time - start_time).total_seconds()
            
            if exit_code == 0:
                logger.info(
                    "Task execution completed successfully",
                    task_id=task_id,
                    session_id=session_id,
                    execution_time=execution_time
                )
                
                return {
                    "success": True,
                    "execution_time": execution_time,
                    "exit_code": exit_code,
                    "logs": logs,
                    "tokens_used": 0,  # TODO: Extract from logs
                    "cost": 0.0  # TODO: Calculate cost
                }
            else:
                logger.error(
                    "Task execution failed",
                    task_id=task_id,
                    session_id=session_id,
                    exit_code=exit_code
                )
                
                return {
                    "success": False,
                    "execution_time": execution_time,
                    "exit_code": exit_code,
                    "error_message": f"Container exited with code {exit_code}",
                    "logs": logs
                }
        
        # Update progress based on logs or time
        elapsed_time = (datetime.now(timezone.utc) - start_time).total_seconds()
        timeout = task_config.get("timeout_minutes", 60) * 60
        
        # Simple progress calculation based on time
        progress = min(0.9, elapsed_time / timeout)  # Cap at 90% until completion
        
        # Broadcast progress update
        await broadcast_task_update(task_id, {
            "status": "running",
            "progress": progress,
            "message": f"Task running... ({elapsed_time:.0f}s elapsed)",
            "resource_usage": status.get("resources", {})
        })
        
        # Check for timeout
        if elapsed_time > timeout:
            logger.error(
                "Task execution timeout",
                task_id=task_id,
                session_id=session_id,
                elapsed_time=elapsed_time,
                timeout=timeout
            )
            
            # Stop the runner
            await runner_service.cancel_runner(session_id)
            
            return {
                "success": False,
                "execution_time": elapsed_time,
                "error_message": f"Task timeout after {timeout} seconds"
            }


async def _create_github_pr(
    task_id: str,
    task_config: Dict[str, Any],
    execution_result: Dict[str, Any]
) -> None:
    """Create GitHub PR for successful task execution"""
    github_service = GitHubService()
    
    try:
        installation_id = task_config.get("github_installation_id")
        repository = task_config.get("repository")
        action_type = task_config.get("action_type", "fix")
        description = task_config.get("description", "")
        
        if not installation_id or not repository:
            logger.warning(
                "Missing GitHub context for PR creation",
                task_id=task_id,
                installation_id=installation_id,
                repository=repository
            )
            return
        
        # Generate branch name
        branch_name = f"autocodit/{action_type}-{task_id[:8]}"
        
        # Create PR
        pr_title = f"{action_type.title()}: {description[:100]}..."
        pr_body = f"""## AutoCodit Agent Task

**Task ID:** `{task_id}`
**Action:** {action_type.title()}
**Description:** {description}

### Changes Made

{execution_result.get('summary', 'Code changes applied by AutoCodit Agent.')}

### Execution Details

- **Execution Time:** {execution_result.get('execution_time', 0):.1f} seconds
- **Tokens Used:** {execution_result.get('tokens_used', 0):,}
- **Cost:** ${execution_result.get('cost', 0.0):.4f}

---
*This PR was created automatically by AutoCodit Agent*
"""
        
        pr = await github_service.create_pull_request(
            installation_id=installation_id,
            repository=repository,
            title=pr_title,
            body=pr_body,
            head_branch=branch_name,
            base_branch="main",
            draft=True
        )
        
        logger.info(
            "GitHub PR created",
            task_id=task_id,
            pr_number=pr["number"],
            pr_url=pr["html_url"]
        )
        
        # Update task with PR information
        task_service = TaskService()
        # TODO: Update task with PR number
        
    except Exception as e:
        logger.error(
            "Failed to create GitHub PR",
            task_id=task_id,
            error=str(e)
        )
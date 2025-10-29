"""
AutoCodit Agent - Task Worker

Celery worker for executing coding tasks in containers.
"""

import asyncio
from typing import Dict, Any
from datetime import datetime, timezone

from celery import current_task
import structlog

from workers.celery_app import celery_app
from app.services.runner_service import RunnerService
from app.services.task_service import TaskService
from app.models.task import TaskStatus
from app.websocket.manager import broadcast_task_update
from app.core.monitoring import metrics

logger = structlog.get_logger()


@celery_app.task(bind=True, name="execute_coding_task")
def execute_coding_task(self, task_id: str, task_config: Dict[str, Any]):
    """Execute coding task in isolated container"""
    
    # Create event loop for async operations
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    
    try:
        return loop.run_until_complete(
            _execute_coding_task_async(self, task_id, task_config)
        )
    finally:
        loop.close()


async def _execute_coding_task_async(task_instance, task_id: str, task_config: Dict[str, Any]):
    """Async implementation of coding task execution"""
    
    logger.info(
        "Starting coding task execution",
        task_id=task_id,
        action_type=task_config.get("action_type")
    )
    
    start_time = datetime.now(timezone.utc)
    
    # Initialize services
    runner_service = RunnerService()
    task_service = TaskService()
    
    try:
        # Update task status to running
        await task_service.update_task_status(
            task_id=task_id,
            status=TaskStatus.RUNNING,
            progress=0.0
        )
        
        # Broadcast status update
        await broadcast_task_update(task_id, {
            "status": "running",
            "progress": 0.0,
            "message": "Task execution started"
        })
        
        # Record metrics
        metrics.record_task_created(
            action_type=task_config.get("action_type", "unknown"),
            repository=task_config.get("repository", "unknown")
        )
        
        # Create and start runner
        session = await runner_service.create_runner(
            task_id=task_id,
            config=task_config
        )
        
        logger.info(
            "Runner created for task",
            task_id=task_id,
            session_id=session.id,
            container_id=session.container_id
        )
        
        # Monitor execution
        result = await _monitor_task_execution(
            task_instance,
            task_id,
            str(session.id),
            runner_service,
            task_service
        )
        
        # Calculate final metrics
        end_time = datetime.now(timezone.utc)
        duration_seconds = (end_time - start_time).total_seconds()
        
        # Record completion metrics
        final_status = result.get("status", "failed")
        metrics.record_task_completed(
            action_type=task_config.get("action_type", "unknown"),
            status=final_status,
            duration_seconds=duration_seconds
        )
        
        # Update final task status
        await task_service.update_task_status(
            task_id=task_id,
            status=TaskStatus.COMPLETED if result.get("success") else TaskStatus.FAILED,
            progress=1.0 if result.get("success") else result.get("progress", 0.0),
            error_message=result.get("error_message")
        )
        
        # Final status broadcast
        await broadcast_task_update(task_id, {
            "status": final_status,
            "progress": 1.0 if result.get("success") else result.get("progress", 0.0),
            "message": result.get("message", "Task completed"),
            "duration_seconds": duration_seconds,
            "artifacts": result.get("artifacts", []),
            "summary": result.get("summary")
        })
        
        logger.info(
            "Task execution completed",
            task_id=task_id,
            success=result.get("success"),
            duration_seconds=duration_seconds
        )
        
        return result
    
    except Exception as exc:
        end_time = datetime.now(timezone.utc)
        duration_seconds = (end_time - start_time).total_seconds()
        
        logger.error(
            "Task execution failed",
            task_id=task_id,
            error=str(exc),
            duration_seconds=duration_seconds
        )
        
        # Update task status to failed
        await task_service.update_task_status(
            task_id=task_id,
            status=TaskStatus.FAILED,
            error_message=str(exc)
        )
        
        # Broadcast failure
        await broadcast_task_update(task_id, {
            "status": "failed",
            "message": f"Task execution failed: {str(exc)}",
            "duration_seconds": duration_seconds
        })
        
        # Record failure metrics
        metrics.record_task_completed(
            action_type=task_config.get("action_type", "unknown"),
            status="failed",
            duration_seconds=duration_seconds
        )
        
        # Retry if configured
        if self.request.retries < self.max_retries:
            logger.info(
                "Retrying task execution",
                task_id=task_id,
                retry_count=self.request.retries + 1
            )
            
            raise self.retry(countdown=60 * (2 ** self.request.retries), exc=exc)
        
        return {
            "success": False,
            "error": str(exc),
            "task_id": task_id
        }


async def _monitor_task_execution(
    task_instance,
    task_id: str,
    session_id: str,
    runner_service: RunnerService,
    task_service: TaskService
) -> Dict[str, Any]:
    """Monitor task execution and provide progress updates"""
    
    import json
    
    logger.info(
        "Starting task monitoring",
        task_id=task_id,
        session_id=session_id
    )
    
    # Monitor container execution
    execution_result = {
        "success": False,
        "progress": 0.0,
        "artifacts": [],
        "logs": []
    }
    
    # Main monitoring loop
    max_iterations = 1800  # 30 minutes max (1 second intervals)
    iteration = 0
    
    while iteration < max_iterations:
        try:
            # Get runner status
            status = await runner_service.get_runner_status(session_id)
            
            if not status:
                logger.warning(
                    "Runner status not available",
                    session_id=session_id
                )
                break
            
            # Check container status
            container_status = status.get("status")
            
            if container_status == "exited":
                exit_code = status.get("exit_code", 1)
                
                if exit_code == 0:
                    execution_result["success"] = True
                    execution_result["progress"] = 1.0
                    execution_result["message"] = "Task completed successfully"
                else:
                    execution_result["success"] = False
                    execution_result["error_message"] = f"Container exited with code {exit_code}"
                
                logger.info(
                    "Container execution finished",
                    session_id=session_id,
                    exit_code=exit_code,
                    success=execution_result["success"]
                )
                break
            
            # Update progress based on logs (simple heuristic)
            if iteration > 0:  # Skip first iteration
                progress = min(0.9, iteration / 600)  # Reach 90% at 10 minutes
                execution_result["progress"] = progress
                
                # Periodic progress updates
                if iteration % 30 == 0:  # Every 30 seconds
                    await task_service.update_task_status(
                        task_id=task_id,
                        status=TaskStatus.RUNNING,
                        progress=progress
                    )
                    
                    await broadcast_task_update(task_id, {
                        "status": "running",
                        "progress": progress,
                        "message": f"Task in progress... ({progress:.1%})",
                        "resource_usage": status.get("resources", {})
                    })
            
            # Update resource metrics
            if status.get("resources"):
                resources = status["resources"]
                metrics.set_container_resource(
                    container_id=status.get("container_id", session_id),
                    resource_type="memory_mb",
                    value=resources.get("memory_usage", 0) / (1024 * 1024)
                )
                metrics.set_container_resource(
                    container_id=status.get("container_id", session_id),
                    resource_type="cpu_percent",
                    value=resources.get("cpu_usage", 0)
                )
            
            # Sleep before next check
            await asyncio.sleep(1)
            iteration += 1
        
        except Exception as e:
            logger.error(
                "Error during task monitoring",
                session_id=session_id,
                iteration=iteration,
                error=str(e)
            )
            await asyncio.sleep(5)  # Longer wait on errors
            iteration += 5
    
    # Handle timeout
    if iteration >= max_iterations:
        execution_result["success"] = False
        execution_result["error_message"] = "Task execution timeout"
        
        logger.warning(
            "Task execution timeout",
            task_id=task_id,
            session_id=session_id
        )
        
        # Cancel runner
        await runner_service.cancel_runner(session_id)
    
    # Get final logs
    try:
        final_logs = await runner_service.get_runner_logs(
            session_id=session_id,
            tail=1000
        )
        execution_result["logs"] = final_logs
    except Exception as e:
        logger.error(
            "Failed to retrieve final logs",
            session_id=session_id,
            error=str(e)
        )
    
    return execution_result
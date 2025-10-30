"""
AutoCodit Agent - Session Worker

Celery tasks for session monitoring and resource management.
"""

import asyncio
from datetime import datetime, timezone
from typing import Dict, Any

import structlog

from app.workers.celery_app import celery_app
from app.services.runner_service import RunnerService
from app.websocket.manager import broadcast_session_update

logger = structlog.get_logger()


@celery_app.task(name="monitor_session")
def monitor_session(session_id: str, task_id: str):
    """Monitor session execution and resource usage"""
    try:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        result = loop.run_until_complete(
            _monitor_session_async(session_id, task_id)
        )
        
        loop.close()
        return result
    
    except Exception as exc:
        logger.error(
            "Session monitoring failed",
            session_id=session_id,
            task_id=task_id,
            error=str(exc)
        )
        raise


async def _monitor_session_async(session_id: str, task_id: str) -> Dict[str, Any]:
    """Async implementation of session monitoring"""
    runner_service = RunnerService()
    
    try:
        while True:
            await asyncio.sleep(5)  # Check every 5 seconds
            
            status = await runner_service.get_runner_status(session_id)
            
            if not status:
                logger.warning("Session no longer exists", session_id=session_id)
                break
            
            # Broadcast resource updates
            await broadcast_session_update(session_id, {
                "status": status.get("status"),
                "resources": status.get("resources", {}),
                "timestamp": datetime.now(timezone.utc).isoformat()
            })
            
            # Check if session finished
            if status.get("status") in ["exited", "dead"]:
                logger.info(
                    "Session finished",
                    session_id=session_id,
                    task_id=task_id,
                    exit_code=status.get("exit_code")
                )
                break
        
        return {
            "session_id": session_id,
            "task_id": task_id,
            "status": "monitoring_completed"
        }
    
    except Exception as e:
        logger.error(
            "Session monitoring error",
            session_id=session_id,
            task_id=task_id,
            error=str(e)
        )
        raise


@celery_app.task(name="update_all_session_metrics")
def update_all_session_metrics():
    """Update metrics for all active sessions"""
    try:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        result = loop.run_until_complete(_update_all_session_metrics_async())
        
        loop.close()
        return result
    
    except Exception as exc:
        logger.error("Failed to update session metrics", error=str(exc))
        raise


async def _update_all_session_metrics_async() -> Dict[str, Any]:
    """Update metrics for all active sessions"""
    runner_service = RunnerService()
    
    try:
        # Get all active runners
        active_sessions = list(runner_service.active_runners.keys())
        
        metrics_updated = 0
        
        for session_id in active_sessions:
            try:
                status = await runner_service.get_runner_status(session_id)
                
                if status:
                    # TODO: Store metrics in database
                    metrics_updated += 1
                    
                    # Broadcast metrics update
                    await broadcast_session_update(session_id, {
                        "type": "metrics_update",
                        "metrics": status.get("resources", {}),
                        "timestamp": datetime.now(timezone.utc).isoformat()
                    })
            
            except Exception as e:
                logger.warning(
                    "Failed to update session metrics",
                    session_id=session_id,
                    error=str(e)
                )
        
        logger.debug(f"Updated metrics for {metrics_updated} sessions")
        
        return {
            "sessions_checked": len(active_sessions),
            "metrics_updated": metrics_updated
        }
    
    except Exception as e:
        logger.error("Failed to update session metrics", error=str(e))
        raise
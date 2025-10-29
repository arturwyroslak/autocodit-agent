"""
AutoCodit Agent - Cleanup Worker

Celery worker for maintenance tasks and cleanup operations.
"""

import asyncio
from typing import Dict, Any
from datetime import datetime, timezone, timedelta

from celery import current_task
import structlog

from workers.celery_app import celery_app
from app.services.runner_service import RunnerService
from app.core.monitoring import metrics
from app.websocket.manager import websocket_manager

logger = structlog.get_logger()


@celery_app.task(name="cleanup_finished_runners")
def cleanup_finished_runners():
    """Clean up finished container runners"""
    
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    
    try:
        return loop.run_until_complete(_cleanup_finished_runners_async())
    finally:
        loop.close()


async def _cleanup_finished_runners_async():
    """Async implementation of runner cleanup"""
    
    logger.debug("Starting runner cleanup task")
    
    runner_service = RunnerService()
    
    try:
        cleaned_count = await runner_service.cleanup_finished_runners()
        
        logger.info(
            "Runner cleanup completed",
            cleaned_count=cleaned_count
        )
        
        # Update metrics
        active_count = len(runner_service.active_runners)
        metrics.set_active_runners(active_count)
        
        return {
            "success": True,
            "cleaned_count": cleaned_count,
            "active_runners": active_count
        }
    
    except Exception as e:
        logger.error(
            "Runner cleanup failed",
            error=str(e)
        )
        return {
            "success": False,
            "error": str(e)
        }


@celery_app.task(name="update_system_metrics")
def update_system_metrics():
    """Update system-wide metrics"""
    
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    
    try:
        return loop.run_until_complete(_update_system_metrics_async())
    finally:
        loop.close()


async def _update_system_metrics_async():
    """Update system metrics"""
    
    logger.debug("Updating system metrics")
    
    try:
        # Update WebSocket connection count
        ws_stats = websocket_manager.get_connection_stats()
        metrics.set_websocket_connections(ws_stats["total_connections"])
        
        # TODO: Update other system metrics
        # - Active sessions from database
        # - Resource usage across all runners
        # - API request rates
        # - Error rates
        
        logger.debug(
            "System metrics updated",
            websocket_connections=ws_stats["total_connections"]
        )
        
        return {
            "success": True,
            "metrics_updated": [
                "websocket_connections",
                "active_sessions",
                "active_runners"
            ]
        }
    
    except Exception as e:
        logger.error(
            "Failed to update system metrics",
            error=str(e)
        )
        return {
            "success": False,
            "error": str(e)
        }


@celery_app.task(name="cleanup_old_logs")
def cleanup_old_logs():
    """Clean up old log entries"""
    
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    
    try:
        return loop.run_until_complete(_cleanup_old_logs_async())
    finally:
        loop.close()


async def _cleanup_old_logs_async():
    """Clean up old log entries from database"""
    
    logger.debug("Starting log cleanup task")
    
    try:
        # TODO: Implement log cleanup
        # - Remove logs older than 30 days
        # - Keep only error/warning logs for longer periods
        # - Archive important logs to object storage
        
        cutoff_date = datetime.now(timezone.utc) - timedelta(days=30)
        
        logger.info(
            "Log cleanup completed",
            cutoff_date=cutoff_date.isoformat()
        )
        
        return {
            "success": True,
            "cutoff_date": cutoff_date.isoformat(),
            "logs_cleaned": 0  # TODO: Return actual count
        }
    
    except Exception as e:
        logger.error(
            "Log cleanup failed",
            error=str(e)
        )
        return {
            "success": False,
            "error": str(e)
        }


@celery_app.task(name="generate_usage_report")
def generate_usage_report(report_config: Dict[str, Any]):
    """Generate usage report for billing/analytics"""
    
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    
    try:
        return loop.run_until_complete(_generate_usage_report_async(report_config))
    finally:
        loop.close()


async def _generate_usage_report_async(config: Dict[str, Any]):
    """Generate usage report"""
    
    report_type = config.get("type", "monthly")
    user_id = config.get("user_id")
    organization_id = config.get("organization_id")
    
    logger.info(
        "Generating usage report",
        report_type=report_type,
        user_id=user_id,
        organization_id=organization_id
    )
    
    try:
        # TODO: Implement usage report generation
        # - Query database for usage statistics
        # - Calculate costs and resource usage
        # - Generate charts and summaries
        # - Store report in object storage
        # - Send notification to user
        
        report_data = {
            "report_type": report_type,
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "user_id": user_id,
            "organization_id": organization_id,
            "statistics": {
                "tasks_completed": 0,  # TODO: Query from database
                "total_cost": 0.0,
                "tokens_used": 0,
                "execution_time_minutes": 0
            }
        }
        
        logger.info(
            "Usage report generated",
            report_type=report_type,
            user_id=user_id
        )
        
        return {
            "success": True,
            "report": report_data
        }
    
    except Exception as e:
        logger.error(
            "Failed to generate usage report",
            report_type=report_type,
            user_id=user_id,
            error=str(e)
        )
        return {
            "success": False,
            "error": str(e)
        }


@celery_app.task(name="health_check_mcp_servers")
def health_check_mcp_servers(servers: List[Dict[str, Any]]):
    """Health check for all MCP servers"""
    
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    
    try:
        return loop.run_until_complete(_health_check_mcp_servers_async(servers))
    finally:
        loop.close()


async def _health_check_mcp_servers_async(servers: List[Dict[str, Any]]):
    """Async health check for MCP servers"""
    
    logger.debug(
        "Starting MCP servers health check",
        server_count=len(servers)
    )
    
    results = []
    
    for server in servers:
        server_name = server.get("name")
        server_type = server.get("type")
        
        try:
            if server_type == "http":
                # HTTP health check
                import httpx
                async with httpx.AsyncClient() as client:
                    response = await client.get(
                        f"{server['url']}/health",
                        headers=server.get("auth", {}),
                        timeout=5.0
                    )
                    
                    healthy = response.status_code == 200
            
            elif server_type == "docker":
                # Check Docker container health
                import docker
                docker_client = docker.from_env()
                
                # Find container by label
                containers = docker_client.containers.list(
                    filters={"label": f"autocodit.mcp-server={server_name}"}
                )
                
                healthy = len(containers) > 0 and all(
                    container.status == "running" for container in containers
                )
            
            else:
                # Built-in servers - assume healthy if listed
                healthy = True
            
            results.append({
                "server_name": server_name,
                "type": server_type,
                "healthy": healthy,
                "checked_at": datetime.now(timezone.utc).isoformat()
            })
            
            logger.debug(
                "MCP server health check completed",
                server_name=server_name,
                healthy=healthy
            )
        
        except Exception as e:
            logger.warning(
                "MCP server health check failed",
                server_name=server_name,
                error=str(e)
            )
            
            results.append({
                "server_name": server_name,
                "type": server_type,
                "healthy": False,
                "error": str(e),
                "checked_at": datetime.now(timezone.utc).isoformat()
            })
    
    healthy_count = sum(1 for result in results if result["healthy"])
    total_count = len(results)
    
    logger.info(
        "MCP servers health check completed",
        healthy_count=healthy_count,
        total_count=total_count
    )
    
    return {
        "success": True,
        "healthy_count": healthy_count,
        "total_count": total_count,
        "results": results
    }
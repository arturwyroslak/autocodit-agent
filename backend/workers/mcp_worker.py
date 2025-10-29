"""
AutoCodit Agent - MCP Worker

Celery worker for managing MCP (Model Context Protocol) servers.
"""

import asyncio
from typing import Dict, Any, List, Optional
import json
import subprocess
import signal
import os

from celery import current_task
import structlog

from workers.celery_app import celery_app

logger = structlog.get_logger()


@celery_app.task(bind=True, name="start_mcp_server")
def start_mcp_server(self, server_config: Dict[str, Any]):
    """Start MCP server process"""
    
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    
    try:
        return loop.run_until_complete(
            _start_mcp_server_async(self, server_config)
        )
    finally:
        loop.close()


async def _start_mcp_server_async(task_instance, server_config: Dict[str, Any]):
    """Async implementation of MCP server startup"""
    
    server_type = server_config.get("type")
    server_name = server_config.get("name")
    
    logger.info(
        "Starting MCP server",
        server_name=server_name,
        server_type=server_type
    )
    
    try:
        if server_type == "builtin":
            return await _start_builtin_mcp_server(server_config)
        elif server_type == "docker":
            return await _start_docker_mcp_server(server_config)
        elif server_type == "http":
            return await _start_http_mcp_server(server_config)
        else:
            raise ValueError(f"Unknown MCP server type: {server_type}")
    
    except Exception as exc:
        logger.error(
            "Failed to start MCP server",
            server_name=server_name,
            error=str(exc)
        )
        
        if task_instance.request.retries < task_instance.max_retries:
            raise task_instance.retry(countdown=30, exc=exc)
        
        return {
            "success": False,
            "error": str(exc),
            "server_name": server_name
        }


async def _start_builtin_mcp_server(config: Dict[str, Any]) -> Dict[str, Any]:
    """Start built-in MCP server"""
    
    server_name = config["name"]
    command = config.get("command", [])
    args = config.get("args", [])
    env = config.get("env", {})
    
    # Build environment
    process_env = os.environ.copy()
    process_env.update(env)
    
    # Start process
    full_command = command + args
    
    logger.info(
        "Starting built-in MCP server process",
        server_name=server_name,
        command=full_command
    )
    
    try:
        process = await asyncio.create_subprocess_exec(
            *full_command,
            env=process_env,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        
        # Wait a bit to see if process starts successfully
        await asyncio.sleep(2)
        
        if process.returncode is not None:
            # Process already exited
            stdout, stderr = await process.communicate()
            raise RuntimeError(f"MCP server failed to start: {stderr.decode()}")
        
        logger.info(
            "Built-in MCP server started successfully",
            server_name=server_name,
            pid=process.pid
        )
        
        return {
            "success": True,
            "server_name": server_name,
            "pid": process.pid,
            "type": "builtin"
        }
    
    except Exception as e:
        logger.error(
            "Failed to start built-in MCP server",
            server_name=server_name,
            error=str(e)
        )
        raise


async def _start_docker_mcp_server(config: Dict[str, Any]) -> Dict[str, Any]:
    """Start Docker-based MCP server"""
    
    server_name = config["name"]
    image = config["image"]
    ports = config.get("ports", {})
    volumes = config.get("volumes", {})
    env = config.get("env", {})
    
    logger.info(
        "Starting Docker MCP server",
        server_name=server_name,
        image=image
    )
    
    import docker
    
    try:
        docker_client = docker.from_env()
        
        # Create and start container
        container = docker_client.containers.run(
            image=image,
            name=f"mcp-{server_name}-{int(datetime.now().timestamp())}",
            environment=env,
            ports=ports,
            volumes=volumes,
            detach=True,
            remove=True,  # Auto-remove when stopped
            network="autocodit-runners",
            labels={
                "autocodit.mcp-server": server_name,
                "autocodit.type": "mcp-server"
            }
        )
        
        # Wait for container to start
        await asyncio.sleep(3)
        
        # Check if container is still running
        container.reload()
        if container.status != "running":
            logs = container.logs().decode()
            raise RuntimeError(f"MCP server container failed to start: {logs}")
        
        logger.info(
            "Docker MCP server started successfully",
            server_name=server_name,
            container_id=container.short_id
        )
        
        return {
            "success": True,
            "server_name": server_name,
            "container_id": container.id,
            "type": "docker"
        }
    
    except Exception as e:
        logger.error(
            "Failed to start Docker MCP server",
            server_name=server_name,
            error=str(e)
        )
        raise


async def _start_http_mcp_server(config: Dict[str, Any]) -> Dict[str, Any]:
    """Start HTTP-based MCP server (validate connection)"""
    
    server_name = config["name"]
    url = config["url"]
    auth_headers = config.get("auth", {})
    
    logger.info(
        "Validating HTTP MCP server",
        server_name=server_name,
        url=url
    )
    
    import httpx
    
    try:
        async with httpx.AsyncClient() as client:
            # Test connection to MCP server
            response = await client.get(
                f"{url}/health",
                headers=auth_headers,
                timeout=10.0
            )
            
            if response.status_code != 200:
                raise RuntimeError(f"MCP server health check failed: {response.status_code}")
            
            logger.info(
                "HTTP MCP server validated successfully",
                server_name=server_name,
                url=url
            )
            
            return {
                "success": True,
                "server_name": server_name,
                "url": url,
                "type": "http"
            }
    
    except Exception as e:
        logger.error(
            "Failed to validate HTTP MCP server",
            server_name=server_name,
            url=url,
            error=str(e)
        )
        raise


@celery_app.task(name="stop_mcp_server")
def stop_mcp_server(server_info: Dict[str, Any]):
    """Stop MCP server"""
    
    server_name = server_info.get("server_name")
    server_type = server_info.get("type")
    
    logger.info(
        "Stopping MCP server",
        server_name=server_name,
        server_type=server_type
    )
    
    try:
        if server_type == "builtin" and "pid" in server_info:
            # Kill process
            try:
                os.kill(server_info["pid"], signal.SIGTERM)
                logger.info("Built-in MCP server stopped", server_name=server_name)
            except ProcessLookupError:
                logger.warning("MCP server process already terminated", server_name=server_name)
        
        elif server_type == "docker" and "container_id" in server_info:
            # Stop Docker container
            import docker
            docker_client = docker.from_env()
            
            try:
                container = docker_client.containers.get(server_info["container_id"])
                container.stop(timeout=10)
                logger.info("Docker MCP server stopped", server_name=server_name)
            except docker.errors.NotFound:
                logger.warning("MCP server container already removed", server_name=server_name)
        
        elif server_type == "http":
            # HTTP servers are external, just log
            logger.info("HTTP MCP server connection closed", server_name=server_name)
        
        return {"success": True, "server_name": server_name}
    
    except Exception as e:
        logger.error(
            "Failed to stop MCP server",
            server_name=server_name,
            error=str(e)
        )
        return {"success": False, "error": str(e), "server_name": server_name}
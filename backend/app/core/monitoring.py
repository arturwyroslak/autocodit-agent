"""
AutoCodit Agent - Monitoring and Metrics

Prometheus metrics, health checks, and observability.
"""

import time
from typing import Dict, Any

from prometheus_client import Counter, Histogram, Gauge, Info
import structlog

from app.core.config import get_settings

logger = structlog.get_logger()

# Prometheus metrics
REQUEST_COUNT = Counter(
    "http_requests_total",
    "Total HTTP requests",
    ["method", "endpoint", "status_code"]
)

REQUEST_DURATION = Histogram(
    "http_request_duration_seconds",
    "HTTP request duration in seconds",
    ["method", "endpoint"]
)

TASK_COUNT = Counter(
    "tasks_total",
    "Total tasks created",
    ["action_type", "repository", "status"]
)

TASK_DURATION = Histogram(
    "task_duration_seconds",
    "Task execution duration in seconds",
    ["action_type", "status"]
)

ACTIVE_TASKS = Gauge(
    "active_tasks",
    "Number of currently active tasks"
)

ACTIVE_SESSIONS = Gauge(
    "active_sessions",
    "Number of currently active sessions"
)

CONTAINER_MEMORY_USAGE = Gauge(
    "container_memory_usage_bytes",
    "Container memory usage in bytes",
    ["session_id", "task_id"]
)

CONTAINER_CPU_USAGE = Gauge(
    "container_cpu_usage_percent",
    "Container CPU usage percentage",
    ["session_id", "task_id"]
)

AI_TOKEN_USAGE = Counter(
    "ai_tokens_total",
    "Total AI tokens used",
    ["provider", "model", "task_type"]
)

AI_REQUEST_DURATION = Histogram(
    "ai_request_duration_seconds",
    "AI request duration in seconds",
    ["provider", "model"]
)

AI_COST = Counter(
    "ai_cost_total_usd",
    "Total AI cost in USD",
    ["provider", "model"]
)

WEBSOCKET_CONNECTIONS = Gauge(
    "websocket_connections_active",
    "Number of active WebSocket connections"
)

GITHUB_API_REQUESTS = Counter(
    "github_api_requests_total",
    "Total GitHub API requests",
    ["endpoint", "status_code", "installation_id"]
)

SECURITY_VIOLATIONS = Counter(
    "security_violations_total",
    "Total security violations detected",
    ["type", "severity"]
)

# System info
APP_INFO = Info("app_info", "Application information")


def setup_monitoring() -> None:
    """Initialize monitoring and metrics"""
    settings = get_settings()
    
    # Set application info
    APP_INFO.info({
        "version": "1.0.0",
        "service": "autocodit-agent",
        "environment": "development" if settings.DEBUG else "production"
    })
    
    logger.info("Monitoring initialized", metrics_enabled=settings.METRICS_ENABLED)


class MetricsCollector:
    """Utility class for collecting and recording metrics"""
    
    @staticmethod
    def record_http_request(
        method: str,
        endpoint: str,
        status_code: int,
        duration: float
    ) -> None:
        """Record HTTP request metrics"""
        REQUEST_COUNT.labels(
            method=method,
            endpoint=endpoint,
            status_code=status_code
        ).inc()
        
        REQUEST_DURATION.labels(
            method=method,
            endpoint=endpoint
        ).observe(duration)
    
    @staticmethod
    def record_task_created(
        action_type: str,
        repository: str
    ) -> None:
        """Record task creation"""
        TASK_COUNT.labels(
            action_type=action_type,
            repository=repository,
            status="created"
        ).inc()
        
        ACTIVE_TASKS.inc()
    
    @staticmethod
    def record_task_completed(
        action_type: str,
        repository: str,
        duration: float,
        success: bool
    ) -> None:
        """Record task completion"""
        status = "completed" if success else "failed"
        
        TASK_COUNT.labels(
            action_type=action_type,
            repository=repository,
            status=status
        ).inc()
        
        TASK_DURATION.labels(
            action_type=action_type,
            status=status
        ).observe(duration)
        
        ACTIVE_TASKS.dec()
    
    @staticmethod
    def record_session_started(session_id: str, task_id: str) -> None:
        """Record session start"""
        ACTIVE_SESSIONS.inc()
        
        logger.info(
            "Session metrics started",
            session_id=session_id,
            task_id=task_id
        )
    
    @staticmethod
    def record_session_finished(session_id: str, task_id: str) -> None:
        """Record session completion"""
        ACTIVE_SESSIONS.dec()
        
        # Clear container metrics
        CONTAINER_MEMORY_USAGE.remove(session_id, task_id)
        CONTAINER_CPU_USAGE.remove(session_id, task_id)
        
        logger.info(
            "Session metrics finished",
            session_id=session_id,
            task_id=task_id
        )
    
    @staticmethod
    def record_container_metrics(
        session_id: str,
        task_id: str,
        memory_usage: int,
        cpu_usage: float
    ) -> None:
        """Record container resource metrics"""
        CONTAINER_MEMORY_USAGE.labels(
            session_id=session_id,
            task_id=task_id
        ).set(memory_usage)
        
        CONTAINER_CPU_USAGE.labels(
            session_id=session_id,
            task_id=task_id
        ).set(cpu_usage)
    
    @staticmethod
    def record_ai_usage(
        provider: str,
        model: str,
        task_type: str,
        tokens: int,
        cost: float,
        duration: float
    ) -> None:
        """Record AI model usage"""
        AI_TOKEN_USAGE.labels(
            provider=provider,
            model=model,
            task_type=task_type
        ).inc(tokens)
        
        AI_REQUEST_DURATION.labels(
            provider=provider,
            model=model
        ).observe(duration)
        
        AI_COST.labels(
            provider=provider,
            model=model
        ).inc(cost)
    
    @staticmethod
    def record_websocket_connection(connected: bool) -> None:
        """Record WebSocket connection change"""
        if connected:
            WEBSOCKET_CONNECTIONS.inc()
        else:
            WEBSOCKET_CONNECTIONS.dec()
    
    @staticmethod
    def record_github_api_request(
        endpoint: str,
        status_code: int,
        installation_id: str
    ) -> None:
        """Record GitHub API request"""
        GITHUB_API_REQUESTS.labels(
            endpoint=endpoint,
            status_code=status_code,
            installation_id=installation_id
        ).inc()
    
    @staticmethod
    def record_security_violation(
        violation_type: str,
        severity: str = "medium"
    ) -> None:
        """Record security violation"""
        SECURITY_VIOLATIONS.labels(
            type=violation_type,
            severity=severity
        ).inc()
        
        logger.warning(
            "Security violation detected",
            type=violation_type,
            severity=severity
        )


# Global metrics collector
metrics = MetricsCollector()
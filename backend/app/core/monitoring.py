"""
AutoCodit Agent - Monitoring and Metrics

Prometheus metrics collection and health monitoring.
"""

import time
from typing import Dict, Any, Optional
from functools import wraps

from prometheus_client import Counter, Histogram, Gauge, Info, CollectorRegistry, REGISTRY
import structlog

from app.core.config import get_settings

logger = structlog.get_logger()

# Metrics definitions
HTTP_REQUESTS = Counter(
    "http_requests_total",
    "Total HTTP requests",
    ["method", "endpoint", "status_code"]
)

HTTP_REQUEST_DURATION = Histogram(
    "http_request_duration_seconds",
    "HTTP request duration in seconds",
    ["method", "endpoint"]
)

TASKS_TOTAL = Counter(
    "tasks_total",
    "Total tasks created",
    ["action_type", "status", "repository"]
)

TASKS_DURATION = Histogram(
    "tasks_duration_seconds",
    "Task execution duration in seconds",
    ["action_type", "status"]
)

SESSIONS_ACTIVE = Gauge(
    "sessions_active",
    "Currently active sessions"
)

RUNNERS_ACTIVE = Gauge(
    "runners_active",
    "Currently active runners"
)

AI_REQUESTS = Counter(
    "ai_requests_total",
    "Total AI API requests",
    ["provider", "model", "status"]
)

AI_TOKENS = Counter(
    "ai_tokens_total",
    "Total AI tokens used",
    ["provider", "model", "type"]
)

AI_COST = Counter(
    "ai_cost_total_usd",
    "Total AI cost in USD",
    ["provider", "model"]
)

WEBSOCKET_CONNECTIONS = Gauge(
    "websocket_connections_active",
    "Currently active WebSocket connections"
)

GITHUB_API_REQUESTS = Counter(
    "github_api_requests_total",
    "Total GitHub API requests",
    ["endpoint", "method", "status_code"]
)

CONTAINER_RESOURCES = Gauge(
    "container_resources",
    "Container resource usage",
    ["resource_type", "container_id"]
)

# Application info
APP_INFO = Info(
    "autocodit_agent_info",
    "AutoCodit Agent application information"
)


class MetricsCollector:
    """Centralized metrics collection"""
    
    def __init__(self):
        self.settings = get_settings()
    
    def record_http_request(
        self,
        method: str,
        endpoint: str,
        status_code: int,
        duration: float
    ) -> None:
        """Record HTTP request metrics"""
        HTTP_REQUESTS.labels(
            method=method,
            endpoint=endpoint,
            status_code=status_code
        ).inc()
        
        HTTP_REQUEST_DURATION.labels(
            method=method,
            endpoint=endpoint
        ).observe(duration)
    
    def record_task_created(
        self,
        action_type: str,
        repository: str
    ) -> None:
        """Record task creation"""
        TASKS_TOTAL.labels(
            action_type=action_type,
            status="created",
            repository=repository
        ).inc()
    
    def record_task_completed(
        self,
        action_type: str,
        status: str,
        duration_seconds: float
    ) -> None:
        """Record task completion"""
        TASKS_TOTAL.labels(
            action_type=action_type,
            status=status,
            repository=""
        ).inc()
        
        TASKS_DURATION.labels(
            action_type=action_type,
            status=status
        ).observe(duration_seconds)
    
    def set_active_sessions(self, count: int) -> None:
        """Update active sessions gauge"""
        SESSIONS_ACTIVE.set(count)
    
    def set_active_runners(self, count: int) -> None:
        """Update active runners gauge"""
        RUNNERS_ACTIVE.set(count)
    
    def record_ai_request(
        self,
        provider: str,
        model: str,
        status: str,
        tokens: Dict[str, int],
        cost: float
    ) -> None:
        """Record AI API request"""
        AI_REQUESTS.labels(
            provider=provider,
            model=model,
            status=status
        ).inc()
        
        # Record token usage
        for token_type, count in tokens.items():
            AI_TOKENS.labels(
                provider=provider,
                model=model,
                type=token_type
            ).inc(count)
        
        # Record cost
        AI_COST.labels(
            provider=provider,
            model=model
        ).inc(cost)
    
    def set_websocket_connections(self, count: int) -> None:
        """Update WebSocket connections gauge"""
        WEBSOCKET_CONNECTIONS.set(count)
    
    def record_github_api_request(
        self,
        endpoint: str,
        method: str,
        status_code: int
    ) -> None:
        """Record GitHub API request"""
        GITHUB_API_REQUESTS.labels(
            endpoint=endpoint,
            method=method,
            status_code=status_code
        ).inc()
    
    def set_container_resource(
        self,
        container_id: str,
        resource_type: str,
        value: float
    ) -> None:
        """Update container resource usage"""
        CONTAINER_RESOURCES.labels(
            resource_type=resource_type,
            container_id=container_id
        ).set(value)


# Global metrics collector
metrics = MetricsCollector()


def setup_monitoring() -> None:
    """Setup monitoring and metrics collection"""
    settings = get_settings()
    
    # Set application info
    APP_INFO.info({
        "version": "1.0.0",
        "environment": settings.DEBUG and "development" or "production",
        "features": {
            "github_app": str(bool(settings.GITHUB_APP_ID)),
            "openai": str(bool(settings.OPENAI_API_KEY)),
            "anthropic": str(bool(settings.ANTHROPIC_API_KEY)),
            "ollama": str(bool(settings.OLLAMA_BASE_URL)),
        }
    })
    
    logger.info("Metrics collection initialized")


def track_execution_time(metric_name: str):
    """Decorator to track function execution time"""
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            start_time = time.time()
            try:
                result = await func(*args, **kwargs)
                duration = time.time() - start_time
                
                # Record success
                if hasattr(metrics, f"record_{metric_name}"):
                    getattr(metrics, f"record_{metric_name}")(duration, "success")
                
                return result
            
            except Exception as e:
                duration = time.time() - start_time
                
                # Record failure
                if hasattr(metrics, f"record_{metric_name}"):
                    getattr(metrics, f"record_{metric_name}")(duration, "error")
                
                raise
        
        return wrapper
    return decorator
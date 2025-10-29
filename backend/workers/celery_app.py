"""
AutoCodit Agent - Celery Configuration

Celery app configuration for distributed task processing.
"""

from celery import Celery
from kombu import Queue
import structlog

from app.core.config import get_settings

logger = structlog.get_logger()
settings = get_settings()

# Create Celery app
celery_app = Celery(
    "autocodit_agent_worker",
    broker=settings.CELERY_BROKER_URL,
    backend=settings.CELERY_RESULT_BACKEND or settings.CELERY_BROKER_URL,
    include=[
        "workers.task_worker",
        "workers.mcp_worker",
        "workers.cleanup_worker"
    ]
)

# Configuration
celery_app.conf.update(
    # Serialization
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    result_accept_content=["json"],
    
    # Timezone
    timezone="UTC",
    enable_utc=True,
    
    # Task routing
    task_routes={
        "workers.task_worker.execute_coding_task": {"queue": "coding_tasks"},
        "workers.mcp_worker.start_mcp_server": {"queue": "mcp_services"},
        "workers.cleanup_worker.cleanup_finished_runners": {"queue": "maintenance"}
    },
    
    # Worker configuration
    worker_prefetch_multiplier=1,  # One task at a time per worker
    task_acks_late=True,  # Acknowledge after task completion
    worker_disable_rate_limits=False,
    
    # Task execution
    task_always_eager=False,  # Set to True for synchronous testing
    task_eager_propagates=True,
    task_ignore_result=False,
    
    # Result backend settings
    result_expires=3600,  # 1 hour
    result_persistent=True,
    
    # Retry configuration
    task_default_retry_delay=60,
    task_max_retries=3,
    
    # Monitoring
    worker_send_task_events=True,
    task_send_sent_event=True,
    
    # Security
    worker_hijack_root_logger=False,
    worker_log_color=False,
    
    # Beat schedule (for periodic tasks)
    beat_schedule={
        "cleanup-finished-runners": {
            "task": "workers.cleanup_worker.cleanup_finished_runners",
            "schedule": 300.0,  # Every 5 minutes
        },
        "update-metrics": {
            "task": "workers.cleanup_worker.update_system_metrics",
            "schedule": 60.0,  # Every minute
        },
        "cleanup-old-logs": {
            "task": "workers.cleanup_worker.cleanup_old_logs",
            "schedule": 3600.0,  # Every hour
        },
    },
)

# Task queues
celery_app.conf.task_routes = {
    # High priority queue for urgent tasks
    "workers.task_worker.execute_coding_task": {
        "queue": "coding_tasks",
        "routing_key": "coding_tasks"
    },
    
    # MCP server management
    "workers.mcp_worker.*": {
        "queue": "mcp_services",
        "routing_key": "mcp_services"
    },
    
    # Maintenance tasks
    "workers.cleanup_worker.*": {
        "queue": "maintenance",
        "routing_key": "maintenance"
    },
}

# Queue definitions
celery_app.conf.task_queues = (
    Queue("coding_tasks", routing_key="coding_tasks"),
    Queue("mcp_services", routing_key="mcp_services"), 
    Queue("maintenance", routing_key="maintenance"),
)

logger.info(
    "Celery app configured",
    broker=settings.CELERY_BROKER_URL,
    backend=settings.CELERY_RESULT_BACKEND
)
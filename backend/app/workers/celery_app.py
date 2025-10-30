"""
AutoCodit Agent - Celery Application

Celery configuration for distributed task execution.
"""

import os
from celery import Celery
from kombu import Queue

from app.core.config import get_settings

# Get settings
settings = get_settings()

# Create Celery app
celery_app = Celery(
    "autocodit_agent_worker",
    broker=settings.CELERY_BROKER_URL,
    backend=settings.CELERY_RESULT_BACKEND or settings.CELERY_BROKER_URL,
    include=[
        "app.workers.task_worker",
        "app.workers.session_worker",
        "app.workers.cleanup_worker"
    ]
)

# Celery configuration
celery_app.conf.update(
    # Serialization
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    
    # Timezone
    timezone="UTC",
    enable_utc=True,
    
    # Task routing
    task_routes={
        "app.workers.task_worker.execute_coding_task": {"queue": "coding_tasks"},
        "app.workers.session_worker.monitor_session": {"queue": "session_monitoring"},
        "app.workers.cleanup_worker.cleanup_resources": {"queue": "cleanup"},
    },
    
    # Worker configuration
    worker_prefetch_multiplier=1,
    task_acks_late=True,
    worker_max_tasks_per_child=100,
    
    # Task configuration
    task_time_limit=7200,  # 2 hours
    task_soft_time_limit=6900,  # 1 hour 55 minutes
    task_max_retries=3,
    task_default_retry_delay=60,
    
    # Result backend
    result_expires=3600,  # 1 hour
    result_backend_transport_options={
        "master_name": "mymaster"
    },
    
    # Monitoring
    worker_send_task_events=True,
    task_send_sent_event=True,
    
    # Beat schedule (for periodic tasks)
    beat_schedule={
        "cleanup-finished-sessions": {
            "task": "app.workers.cleanup_worker.cleanup_finished_sessions",
            "schedule": 300.0,  # Every 5 minutes
        },
        "cleanup-old-logs": {
            "task": "app.workers.cleanup_worker.cleanup_old_logs",
            "schedule": 3600.0,  # Every hour
        },
        "update-resource-metrics": {
            "task": "app.workers.session_worker.update_all_session_metrics",
            "schedule": 30.0,  # Every 30 seconds
        },
    },
)

# Queue definitions
celery_app.conf.task_queues = (
    Queue("coding_tasks", routing_key="coding_tasks"),
    Queue("session_monitoring", routing_key="session_monitoring"),
    Queue("cleanup", routing_key="cleanup"),
    Queue("celery", routing_key="celery"),  # Default queue
)
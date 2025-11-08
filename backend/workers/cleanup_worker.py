"""
AutoCodit Agent - Cleanup Worker

Celery worker for maintenance tasks and cleanup operations.
"""

import asyncio
from typing import Dict, Any, List
from datetime import datetime, timezone, timedelta

from celery import current_task
import structlog

from workers.celery_app import celery_app
from app.services.runner_service import RunnerService
from app.core.monitoring import metrics
from app.websocket.manager import manager

logger = structlog.get_logger()

# ... (pozostały kod bez zmian)

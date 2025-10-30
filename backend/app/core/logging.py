"""
AutoCodit Agent - Logging Configuration

Structured logging configuration with JSON formatting,
contextual information, and multiple output targets.
"""

import logging
import sys
from typing import Any, Dict

import structlog
from pythonjsonlogger import jsonlogger

from app.core.config import get_settings


def setup_logging() -> None:
    """Configure structured logging for the application"""
    settings = get_settings()
    
    # Configure standard library logging
    logging.basicConfig(
        format="%(message)s",
        stream=sys.stdout,
        level=getattr(logging, settings.LOG_LEVEL)
    )
    
    # Configure structlog
    structlog.configure(
        processors=[
            structlog.contextvars.merge_contextvars,
            structlog.processors.TimeStamper(fmt="ISO"),
            structlog.processors.add_log_level,
            structlog.processors.StackInfoRenderer(),
            structlog.dev.set_exc_info,
            _add_service_info,
            structlog.processors.JSONRenderer() if settings.STRUCTURED_LOGGING else structlog.dev.ConsoleRenderer(),
        ],
        wrapper_class=structlog.make_filtering_bound_logger(
            getattr(logging, settings.LOG_LEVEL)
        ),
        logger_factory=structlog.WriteLoggerFactory(),
        cache_logger_on_first_use=True,
    )
    
    # Silence noisy loggers in development
    if settings.DEBUG:
        logging.getLogger("httpx").setLevel(logging.WARNING)
        logging.getLogger("httpcore").setLevel(logging.WARNING)
        logging.getLogger("sqlalchemy.engine").setLevel(logging.WARNING)
    
    logger = structlog.get_logger()
    logger.info(
        "Logging configured",
        level=settings.LOG_LEVEL,
        structured=settings.STRUCTURED_LOGGING,
        debug=settings.DEBUG
    )


def _add_service_info(logger: Any, method_name: str, event_dict: Dict[str, Any]) -> Dict[str, Any]:
    """Add service information to log entries"""
    event_dict["service"] = "autocodit-agent"
    event_dict["component"] = event_dict.get("logger", "unknown")
    return event_dict


class RequestLoggingMiddleware:
    """Middleware for logging HTTP requests"""
    
    def __init__(self, app):
        self.app = app
    
    async def __call__(self, scope, receive, send):
        if scope["type"] == "http":
            logger = structlog.get_logger()
            
            # Log request start
            start_time = datetime.now(timezone.utc)
            
            logger.info(
                "Request started",
                method=scope["method"],
                path=scope["path"],
                query_string=scope["query_string"].decode(),
                client_ip=scope.get("client", ["", None])[0]
            )
            
            # Process request
            await self.app(scope, receive, send)
            
            # Log request completion
            end_time = datetime.now(timezone.utc)
            duration = (end_time - start_time).total_seconds()
            
            logger.info(
                "Request completed",
                method=scope["method"],
                path=scope["path"],
                duration_seconds=duration
            )
        else:
            await self.app(scope, receive, send)


class TaskLogHandler:
    """Custom log handler for task execution logs"""
    
    def __init__(self, task_id: str):
        self.task_id = task_id
        self.logs: List[Dict[str, Any]] = []
    
    def add_log(self, level: str, message: str, **kwargs) -> None:
        """Add log entry for the task"""
        log_entry = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "level": level,
            "message": message,
            "task_id": self.task_id,
            **kwargs
        }
        
        self.logs.append(log_entry)
        
        # Also log to structlog
        logger = structlog.get_logger()
        getattr(logger, level.lower())(message, task_id=self.task_id, **kwargs)
    
    def get_logs(self, limit: int = 100, offset: int = 0) -> List[Dict[str, Any]]:
        """Get task logs with pagination"""
        return self.logs[offset:offset + limit]
    
    def clear_logs(self) -> None:
        """Clear all logs for the task"""
        self.logs.clear()
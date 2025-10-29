"""
AutoCodit Agent - Logging Configuration

Structured logging setup with multiple output formats and levels.
"""

import logging
import sys
from typing import Any

import structlog
from opentelemetry import trace
from opentelemetry.exporter.jaeger.thrift import JaegerExporter
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
from opentelemetry.instrumentation.sqlalchemy import SQLAlchemyInstrumentor
from opentelemetry.instrumentation.httpx import HTTPXClientInstrumentor
from opentelemetry.sdk.resources import Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor

from app.core.config import get_settings


def setup_logging() -> None:
    """Setup application logging"""
    settings = get_settings()
    
    # Configure standard library logging
    logging.basicConfig(
        format="%(message)s",
        stream=sys.stdout,
        level=getattr(logging, settings.LOG_LEVEL.upper())
    )
    
    # Configure structlog
    processors = [
        structlog.contextvars.merge_contextvars,
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.add_log_level,
        structlog.processors.StackInfoRenderer(),
        structlog.dev.set_exc_info,
    ]
    
    if settings.STRUCTURED_LOGGING:
        # JSON output for production
        processors.append(structlog.processors.JSONRenderer())
    else:
        # Human-readable output for development
        processors.extend([
            structlog.dev.ConsoleRenderer(colors=True),
        ])
    
    structlog.configure(
        processors=processors,
        wrapper_class=structlog.make_filtering_bound_logger(
            getattr(logging, settings.LOG_LEVEL.upper())
        ),
        logger_factory=structlog.WriteLoggerFactory(),
        cache_logger_on_first_use=True,
    )
    
    # Setup OpenTelemetry tracing if enabled
    if settings.TRACING_ENABLED and settings.JAEGER_ENDPOINT:
        setup_tracing()


def setup_tracing() -> None:
    """Setup OpenTelemetry tracing"""
    settings = get_settings()
    
    # Create resource
    resource = Resource.create({
        "service.name": "autocodit-agent-api",
        "service.version": "1.0.0"
    })
    
    # Create tracer provider
    trace.set_tracer_provider(TracerProvider(resource=resource))
    tracer = trace.get_tracer_provider()
    
    # Create Jaeger exporter
    jaeger_exporter = JaegerExporter(
        agent_host_name="jaeger",
        agent_port=6831,
    )
    
    # Create span processor
    span_processor = BatchSpanProcessor(jaeger_exporter)
    tracer.add_span_processor(span_processor)
    
    # Auto-instrument frameworks
    FastAPIInstrumentor.instrument()
    SQLAlchemyInstrumentor.instrument()
    HTTPXClientInstrumentor.instrument()
    
    logger = structlog.get_logger()
    logger.info("OpenTelemetry tracing configured")


def get_logger(name: str = None) -> structlog.BoundLogger:
    """Get configured logger instance"""
    if name:
        return structlog.get_logger(name)
    return structlog.get_logger()
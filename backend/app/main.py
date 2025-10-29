"""
AutoCodit Agent - Main FastAPI Application

This is the core API server that handles:
- GitHub App webhook events
- Task management and orchestration
- Real-time WebSocket connections
- Authentication and authorization
- AI model integration
"""

import logging
from contextlib import asynccontextmanager
from typing import AsyncGenerator

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.responses import JSONResponse
from prometheus_client import make_asgi_app
import structlog

from app.core.config import get_settings
from app.core.database import database
from app.core.logging import setup_logging
from app.core.monitoring import setup_monitoring
from app.api.v1.router import api_router
from app.github.webhook import github_webhook_router
from app.websocket.manager import websocket_router
from app.core.exceptions import AutoCoditException


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Application lifespan events"""
    settings = get_settings()
    logger = structlog.get_logger()
    
    # Startup
    logger.info("Starting AutoCodit Agent API", version="1.0.0")
    
    # Initialize database
    await database.connect()
    logger.info("Database connected")
    
    # Initialize monitoring
    setup_monitoring()
    logger.info("Monitoring initialized")
    
    yield
    
    # Shutdown
    logger.info("Shutting down AutoCodit Agent API")
    await database.disconnect()
    logger.info("Database disconnected")


def create_app() -> FastAPI:
    """Create and configure the FastAPI application"""
    settings = get_settings()
    
    # Setup logging
    setup_logging()
    
    # Create FastAPI app
    app = FastAPI(
        title="AutoCodit Agent API",
        description="Self-hosted GitHub Copilot Coding Agent clone",
        version="1.0.0",
        docs_url="/docs" if settings.DEBUG else None,
        redoc_url="/redoc" if settings.DEBUG else None,
        lifespan=lifespan,
    )
    
    # Middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.CORS_ORIGINS,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    
    app.add_middleware(
        TrustedHostMiddleware,
        allowed_hosts=settings.ALLOWED_HOSTS,
    )
    
    # Exception handlers
    @app.exception_handler(AutoCoditException)
    async def autocodit_exception_handler(request: Request, exc: AutoCoditException):
        return JSONResponse(
            status_code=exc.status_code,
            content={"detail": exc.detail, "code": exc.code},
        )
    
    # Routes
    app.include_router(api_router, prefix="/api/v1")
    app.include_router(github_webhook_router, prefix="/github")
    app.include_router(websocket_router, prefix="/ws")
    
    # Health checks
    @app.get("/health", tags=["health"])
    async def health_check():
        return {"status": "healthy", "service": "autocodit-agent-api"}
    
    @app.get("/ready", tags=["health"])
    async def readiness_check():
        # Check database connection
        try:
            await database.execute("SELECT 1")
            return {"status": "ready", "database": "connected"}
        except Exception as e:
            return JSONResponse(
                status_code=503,
                content={"status": "not ready", "error": str(e)},
            )
    
    # Prometheus metrics
    if settings.METRICS_ENABLED:
        metrics_app = make_asgi_app()
        app.mount("/metrics", metrics_app)
    
    return app


# Create the app instance
app = create_app()


if __name__ == "__main__":
    import uvicorn
    
    settings = get_settings()
    
    uvicorn.run(
        "app.main:app",
        host=settings.API_HOST,
        port=settings.API_PORT,
        reload=settings.HOT_RELOAD,
        log_level=settings.LOG_LEVEL.lower(),
    )
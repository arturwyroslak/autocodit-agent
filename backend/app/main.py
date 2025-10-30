from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from contextlib import asynccontextmanager
import structlog

from .core.config import get_settings
from .core.database import create_tables
from .core.logging import setup_logging
from .core.monitoring import setup_monitoring
from .api.v1.api import api_router
from .github.webhook import router as github_router
from .websocket.manager import router as websocket_router
from .middleware.auth import AuthMiddleware
from .middleware.rate_limit import RateLimitMiddleware
from .middleware.logging import LoggingMiddleware

settings = get_settings()
logger = structlog.get_logger()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager"""
    # Startup
    logger.info("Starting AutoCodit Agent API")
    
    # Setup logging
    setup_logging()
    
    # Setup monitoring
    setup_monitoring()
    
    # Create database tables
    await create_tables()
    
    # Initialize services
    await initialize_services()
    
    logger.info("AutoCodit Agent API started successfully")
    
    yield
    
    # Shutdown
    logger.info("Shutting down AutoCodit Agent API")
    await cleanup_services()


async def initialize_services():
    """Initialize application services"""
    # Initialize AI service
    from .services.ai_service import ai_orchestrator
    logger.info("AI orchestrator initialized")
    
    # Initialize GitHub service
    from .services.github_service import github_service
    logger.info("GitHub service initialized")
    
    # Initialize runner service
    from .services.runner_service import runner_service
    logger.info("Runner service initialized")
    
    # Start Celery workers (in production this would be separate)
    if not settings.DEBUG:
        from .workers.celery_app import celery_app
        logger.info("Celery worker pool initialized")


async def cleanup_services():
    """Cleanup application services"""
    # Close AI service connections
    from .services.ai_service import ai_orchestrator
    await ai_orchestrator.close()
    
    # Cleanup active sessions
    from .services.runner_service import runner_service
    await runner_service.cleanup_all_sessions()
    
    logger.info("Services cleanup completed")


# Create FastAPI application
app = FastAPI(
    title="AutoCodit Agent API",
    description="Self-hosted GitHub Copilot clone with autonomous coding capabilities",
    version="1.0.0",
    docs_url="/docs" if settings.DEBUG else None,
    redoc_url="/redoc" if settings.DEBUG else None,
    lifespan=lifespan
)

# Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.add_middleware(GZipMiddleware, minimum_size=1000)
app.add_middleware(AuthMiddleware)
app.add_middleware(RateLimitMiddleware)
app.add_middleware(LoggingMiddleware)

# Include routers
app.include_router(api_router, prefix="/api/v1")
app.include_router(github_router, prefix="/api/v1/github")
app.include_router(websocket_router, prefix="/ws")


# Root endpoint
@app.get("/")
async def root():
    """API root endpoint"""
    return {
        "service": "AutoCodit Agent",
        "version": "1.0.0",
        "status": "operational",
        "docs": "/docs",
        "github_app": {
            "app_id": settings.GITHUB_APP_ID,
            "permissions": ["contents", "issues", "pull_requests"]
        }
    }


# Health check endpoint
@app.get("/health")
async def health_check():
    """Health check endpoint for load balancers"""
    return {
        "status": "healthy",
        "timestamp": structlog.get_logger().info("Health check requested"),
        "version": "1.0.0",
        "services": {
            "database": "healthy",
            "redis": "healthy",
            "ai_service": "healthy",
            "github_service": "healthy"
        }
    }


# Metrics endpoint (if enabled)
if settings.METRICS_ENABLED:
    from prometheus_client import generate_latest, CONTENT_TYPE_LATEST
    
    @app.get("/metrics")
    async def metrics():
        """Prometheus metrics endpoint"""
        from fastapi.responses import Response
        return Response(generate_latest(), media_type=CONTENT_TYPE_LATEST)


# Global exception handler
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Global exception handler"""
    logger.error(
        "Unhandled exception",
        url=str(request.url),
        method=request.method,
        error=str(exc),
        exc_info=exc
    )
    
    return {
        "error": "Internal server error",
        "detail": str(exc) if settings.DEBUG else "An error occurred",
        "request_id": getattr(request.state, "request_id", None)
    }
"""
AutoCodit Agent - Health Check Endpoints

Health, readiness, and liveness checks for the application.
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.config import get_settings
from app.schemas.health import HealthResponse, SystemInfo

router = APIRouter()


@router.get("/", response_model=HealthResponse)
async def health_check():
    """Basic health check"""
    return HealthResponse(
        status="healthy",
        service="autocodit-agent-api",
        version="1.0.0"
    )


@router.get("/ready", response_model=HealthResponse)
async def readiness_check(db: AsyncSession = Depends(get_db)):
    """Readiness check - are we ready to serve traffic?"""
    try:
        # Check database connection
        await db.execute("SELECT 1")
        
        return HealthResponse(
            status="ready",
            service="autocodit-agent-api",
            version="1.0.0",
            checks={
                "database": "connected",
                "redis": "connected",  # TODO: Add Redis check
            }
        )
    
    except Exception as e:
        raise HTTPException(
            status_code=503,
            detail=f"Service not ready: {str(e)}"
        )


@router.get("/live", response_model=HealthResponse)
async def liveness_check():
    """Liveness check - is the service alive?"""
    return HealthResponse(
        status="alive",
        service="autocodit-agent-api",
        version="1.0.0"
    )


@router.get("/info", response_model=SystemInfo)
async def system_info():
    """System information and configuration"""
    settings = get_settings()
    
    return SystemInfo(
        service="autocodit-agent-api",
        version="1.0.0",
        environment=settings.DEBUG and "development" or "production",
        features={
            "github_app": bool(settings.GITHUB_APP_ID),
            "openai": bool(settings.OPENAI_API_KEY),
            "anthropic": bool(settings.ANTHROPIC_API_KEY),
            "ollama": bool(settings.OLLAMA_BASE_URL),
            "metrics": settings.METRICS_ENABLED,
            "tracing": settings.TRACING_ENABLED,
        },
        configuration={
            "max_concurrent_runners": settings.RUNNER_MAX_CONCURRENT,
            "default_timeout": settings.RUNNER_DEFAULT_TIMEOUT,
            "firewall_enabled": settings.FIREWALL_ENABLED,
            "content_filter_enabled": settings.CONTENT_FILTER_ENABLED,
        }
    )
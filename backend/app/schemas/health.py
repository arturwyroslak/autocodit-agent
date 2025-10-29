"""
AutoCodit Agent - Health Check Schemas

Pydantic models for health check responses.
"""

from typing import Dict, Any, Optional
from pydantic import BaseModel


class HealthResponse(BaseModel):
    """Basic health response"""
    status: str
    service: str
    version: str
    checks: Optional[Dict[str, str]] = None
    
    class Config:
        json_schema_extra = {
            "example": {
                "status": "healthy",
                "service": "autocodit-agent-api",
                "version": "1.0.0",
                "checks": {
                    "database": "connected",
                    "redis": "connected"
                }
            }
        }


class SystemInfo(BaseModel):
    """System information response"""
    service: str
    version: str
    environment: str
    features: Dict[str, bool]
    configuration: Dict[str, Any]
    
    class Config:
        json_schema_extra = {
            "example": {
                "service": "autocodit-agent-api",
                "version": "1.0.0",
                "environment": "development",
                "features": {
                    "github_app": True,
                    "openai": True,
                    "anthropic": False,
                    "metrics": True
                },
                "configuration": {
                    "max_concurrent_runners": 10,
                    "default_timeout": 3600,
                    "firewall_enabled": True
                }
            }
        }

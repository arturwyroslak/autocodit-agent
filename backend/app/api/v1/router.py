"""
AutoCodit Agent - API v1 Router

Main router that includes all API endpoints for the application.
"""

from fastapi import APIRouter

from app.api.v1.endpoints import tasks, agents, sessions, github, users, health

api_router = APIRouter()

# Include all endpoint routers
api_router.include_router(health.router, prefix="/health", tags=["health"])
api_router.include_router(tasks.router, prefix="/tasks", tags=["tasks"])
api_router.include_router(agents.router, prefix="/agents", tags=["agents"])
api_router.include_router(sessions.router, prefix="/sessions", tags=["sessions"])
api_router.include_router(github.router, prefix="/github", tags=["github"])
api_router.include_router(users.router, prefix="/users", tags=["users"])
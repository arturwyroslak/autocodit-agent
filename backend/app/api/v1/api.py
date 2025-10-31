from fastapi import APIRouter

from .endpoints.tasks import router as tasks_router
from .endpoints.sessions import router as sessions_router
from .endpoints.agents import router as agents_router
from .endpoints.users import router as users_router
from .endpoints.repositories import router as repositories_router
from .endpoints.tasks_summary import router as tasks_summary_router
from .endpoints.sessions_summary import router as sessions_summary_router

api_router = APIRouter()

# Include all endpoint routers
api_router.include_router(
    tasks_router,
    prefix="/tasks",
    tags=["tasks"]
)

api_router.include_router(
    tasks_summary_router,
    prefix="/tasks",
    tags=["tasks"]
)

api_router.include_router(
    sessions_router,
    prefix="/sessions", 
    tags=["sessions"]
)

api_router.include_router(
    sessions_summary_router,
    prefix="/sessions",
    tags=["sessions"]
)

api_router.include_router(
    agents_router,
    prefix="/agents",
    tags=["agents"]
)

api_router.include_router(
    users_router,
    prefix="/users",
    tags=["users"]
)

api_router.include_router(
    repositories_router,
    prefix="/repositories",
    tags=["repositories"]
)


@api_router.get("/")
async def api_root():
    """API v1 root endpoint"""
    return {
        "message": "AutoCodit Agent API v1",
        "endpoints": {
            "tasks": "/api/v1/tasks",
            "sessions": "/api/v1/sessions",
            "agents": "/api/v1/agents", 
            "users": "/api/v1/users",
            "repositories": "/api/v1/repositories"
        },
        "documentation": "/docs"
    }

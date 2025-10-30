"""
AutoCodit Agent - User API Endpoints

API endpoints for user management and authentication.
"""

from typing import Optional
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
import structlog

from app.core.database import get_db
from app.core.auth import get_current_user
from app.models.user import User

logger = structlog.get_logger()
router = APIRouter()


@router.get("/me")
async def get_current_user_info(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get current user information"""
    return {
        "id": str(current_user.id),
        "username": current_user.username,
        "email": current_user.email,
        "full_name": current_user.full_name,
        "avatar_url": current_user.avatar_url,
        "github_login": current_user.github_login,
        "preferences": current_user.preferences,
        "timezone": current_user.timezone,
        "created_at": current_user.created_at,
        "last_login_at": current_user.last_login_at
    }


@router.get("/stats")
async def get_user_stats(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get user statistics"""
    # TODO: Implement user statistics
    return {
        "total_tasks": 0,
        "completed_tasks": 0,
        "failed_tasks": 0,
        "total_time_saved": 0,
        "tokens_used": 0,
        "cost_total": 0.0,
        "repositories_worked_on": 0,
        "lines_of_code_generated": 0
    }
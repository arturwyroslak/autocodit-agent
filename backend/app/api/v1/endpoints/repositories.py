"""
AutoCodit Agent - Repositories API Endpoints

API endpoints for listing and managing GitHub repositories.
"""

from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
import structlog

from app.core.auth import get_current_user
from app.models.user import User
# TODO: Replace with real github service
# from app.services.github_service import github_service

logger = structlog.get_logger()
router = APIRouter()


@router.get("/")
async def list_repositories(
    current_user: Optional[User] = Depends(get_current_user)
):
    """List accessible repositories (mock, replace with real GitHub integration)"""
    return {
        "items": [
            {"full_name": "arturwyroslak/autocodit-agent", "default_branch": "main"},
            {"full_name": "arturwyroslak/project-alpha", "default_branch": "main"},
            {"full_name": "arturwyroslak/project-beta", "default_branch": "main"}
        ]
    }

@router.get("/{owner}/{repo}/branches")
async def list_branches(
    owner: str,
    repo: str,
    current_user: Optional[User] = Depends(get_current_user)
):
    """List branches for a specific repository (mock, replace with real GitHub)"""
    branches_map = {
        "autocodit-agent": ["main", "develop", "feature/ui-improvements"],
        "project-alpha": ["main", "staging", "production"],
        "project-beta": ["main", "dev"]
    }
    repo_base = repo.split("/")[-1] if "/" in repo else repo
    branches = branches_map.get(repo_base, ["main"])
    return {"items": [{"name": b} for b in branches]}

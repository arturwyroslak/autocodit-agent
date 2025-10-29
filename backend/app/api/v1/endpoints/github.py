"""
AutoCodit Agent - GitHub Integration API Endpoints

RESTful API endpoints for GitHub-related operations.
"""

from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.services.github_service import GitHubService
from app.schemas.github import (
    GitHubInstallation,
    GitHubRepository,
    CreateIssueCommentRequest,
    CreatePullRequestRequest,
    CreateCheckRunRequest
)
from app.core.auth import get_current_user
from app.models.user import User

router = APIRouter()
github_service = GitHubService()


@router.get("/installations", response_model=List[GitHubInstallation])
async def get_github_installations(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get GitHub App installations accessible to user"""
    
    try:
        installations = await github_service.get_installations()
        
        # TODO: Filter installations based on user access
        # For now, return all installations
        
        return [
            GitHubInstallation(
                id=install["id"],
                account=install["account"],
                permissions=install["permissions"],
                repository_selection=install["repository_selection"]
            )
            for install in installations
        ]
    
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to fetch installations: {str(e)}"
        )


@router.get("/installations/{installation_id}/repositories", response_model=List[GitHubRepository])
async def get_installation_repositories(
    installation_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get repositories for GitHub App installation"""
    
    try:
        repositories = await github_service.get_installation_repositories(installation_id)
        
        return [
            GitHubRepository(
                id=repo["id"],
                name=repo["name"],
                full_name=repo["full_name"],
                private=repo["private"],
                default_branch=repo["default_branch"],
                permissions=repo["permissions"]
            )
            for repo in repositories
        ]
    
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to fetch repositories: {str(e)}"
        )


@router.post("/comments")
async def create_issue_comment(
    request: CreateIssueCommentRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Create comment on GitHub issue or PR"""
    
    try:
        comment = await github_service.create_issue_comment(
            installation_id=request.installation_id,
            repository=request.repository,
            issue_number=request.issue_number,
            body=request.body
        )
        
        return comment
    
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to create comment: {str(e)}"
        )


@router.post("/pull-requests")
async def create_pull_request(
    request: CreatePullRequestRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Create GitHub pull request"""
    
    try:
        pr = await github_service.create_pull_request(
            installation_id=request.installation_id,
            repository=request.repository,
            title=request.title,
            body=request.body,
            head_branch=request.head_branch,
            base_branch=request.base_branch,
            draft=request.draft
        )
        
        return pr
    
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to create pull request: {str(e)}"
        )


@router.post("/check-runs")
async def create_check_run(
    request: CreateCheckRunRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Create GitHub check run"""
    
    try:
        check_run = await github_service.create_check_run(
            installation_id=request.installation_id,
            repository=request.repository,
            commit_sha=request.commit_sha,
            name=request.name,
            status=request.status,
            conclusion=request.conclusion,
            output=request.output
        )
        
        return check_run
    
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to create check run: {str(e)}"
        )


@router.get("/repositories/{owner}/{repo}/issues")
async def get_repository_issues(
    owner: str,
    repo: str,
    installation_id: int = Query(..., description="GitHub installation ID"),
    state: str = Query("open", description="Issue state"),
    labels: Optional[str] = Query(None, description="Comma-separated labels"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get repository issues"""
    
    # TODO: Implement issue retrieval using GitHub client
    raise HTTPException(status_code=501, detail="Not implemented")


@router.get("/repositories/{owner}/{repo}/pulls")
async def get_repository_pull_requests(
    owner: str,
    repo: str,
    installation_id: int = Query(..., description="GitHub installation ID"),
    state: str = Query("open", description="PR state"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get repository pull requests"""
    
    # TODO: Implement PR retrieval using GitHub client
    raise HTTPException(status_code=501, detail="Not implemented")


@router.post("/repositories/{owner}/{repo}/branches")
async def create_branch(
    owner: str,
    repo: str,
    branch_data: dict,
    installation_id: int = Query(..., description="GitHub installation ID"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Create new branch in repository"""
    
    try:
        branch = await github_service.create_agent_branch(
            installation_id=installation_id,
            repository=f"{owner}/{repo}",
            branch_name=branch_data["name"],
            base_branch=branch_data.get("base_branch", "main")
        )
        
        return branch
    
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to create branch: {str(e)}"
        )


@router.post("/repositories/{owner}/{repo}/commits")
async def commit_changes(
    owner: str,
    repo: str,
    commit_data: dict,
    installation_id: int = Query(..., description="GitHub installation ID"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Commit changes to repository"""
    
    try:
        commit = await github_service.commit_changes(
            installation_id=installation_id,
            repository=f"{owner}/{repo}",
            branch_name=commit_data["branch"],
            files=commit_data["files"],
            commit_message=commit_data["message"]
        )
        
        return commit
    
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to commit changes: {str(e)}"
        )
"""
AutoCodit Agent - GitHub Schemas

Pydantic models for GitHub webhook events and API responses.
"""

from typing import Dict, Any, Optional, List
from datetime import datetime
from pydantic import BaseModel, Field


class WebhookEvent(BaseModel):
    """GitHub webhook event"""
    event_type: str = Field(..., description="GitHub event type")
    delivery_id: str = Field(..., description="GitHub delivery ID")
    payload: Dict[str, Any] = Field(..., description="Event payload")
    processed_at: Optional[datetime] = Field(None, description="When event was processed")
    
    class Config:
        json_schema_extra = {
            "example": {
                "event_type": "issues",
                "delivery_id": "12345678-1234-1234-1234-123456789012",
                "payload": {
                    "action": "assigned",
                    "issue": {
                        "number": 1,
                        "title": "Bug in authentication",
                        "body": "There's a bug in the authentication module..."
                    },
                    "repository": {
                        "full_name": "owner/repo"
                    }
                }
            }
        }


class GitHubRepository(BaseModel):
    """GitHub repository information"""
    id: int
    name: str
    full_name: str
    private: bool
    default_branch: str
    permissions: Dict[str, bool]
    

class GitHubInstallation(BaseModel):
    """GitHub App installation"""
    id: int
    account: Dict[str, Any]
    permissions: Dict[str, str]
    repository_selection: str
    repositories: Optional[List[GitHubRepository]] = None


class GitHubUser(BaseModel):
    """GitHub user information"""
    id: int
    login: str
    avatar_url: str
    type: str


class GitHubIssue(BaseModel):
    """GitHub issue"""
    id: int
    number: int
    title: str
    body: Optional[str] = None
    state: str
    assignees: List[GitHubUser]
    labels: List[Dict[str, Any]]
    html_url: str
    created_at: datetime
    updated_at: datetime


class GitHubPullRequest(BaseModel):
    """GitHub pull request"""
    id: int
    number: int
    title: str
    body: Optional[str] = None
    state: str
    draft: bool
    html_url: str
    head: Dict[str, Any]
    base: Dict[str, Any]
    user: GitHubUser
    created_at: datetime
    updated_at: datetime


class GitHubComment(BaseModel):
    """GitHub comment"""
    id: int
    body: str
    user: GitHubUser
    html_url: str
    created_at: datetime
    updated_at: datetime


class GitHubCheckRun(BaseModel):
    """GitHub check run"""
    id: int
    name: str
    status: str
    conclusion: Optional[str] = None
    html_url: str
    output: Optional[Dict[str, Any]] = None


class GitHubBranch(BaseModel):
    """GitHub branch"""
    name: str
    commit: Dict[str, Any]
    protected: bool


class CreateIssueCommentRequest(BaseModel):
    """Request to create issue comment"""
    installation_id: int
    repository: str
    issue_number: int
    body: str
    
    class Config:
        json_schema_extra = {
            "example": {
                "installation_id": 12345,
                "repository": "owner/repo",
                "issue_number": 1,
                "body": "Starting work on this issue..."
            }
        }


class CreatePullRequestRequest(BaseModel):
    """Request to create pull request"""
    installation_id: int
    repository: str
    title: str
    body: str
    head_branch: str
    base_branch: str = "main"
    draft: bool = True
    
    class Config:
        json_schema_extra = {
            "example": {
                "installation_id": 12345,
                "repository": "owner/repo",
                "title": "Fix authentication bug",
                "body": "This PR fixes the authentication bug described in issue #1",
                "head_branch": "agent/fix-auth-bug",
                "base_branch": "main",
                "draft": True
            }
        }


class CreateCheckRunRequest(BaseModel):
    """Request to create check run"""
    installation_id: int
    repository: str
    commit_sha: str
    name: str
    status: str = "in_progress"
    conclusion: Optional[str] = None
    output: Optional[Dict[str, Any]] = None
    
    class Config:
        json_schema_extra = {
            "example": {
                "installation_id": 12345,
                "repository": "owner/repo",
                "commit_sha": "abc123def456",
                "name": "AutoCodit Agent",
                "status": "completed",
                "conclusion": "success",
                "output": {
                    "title": "Task completed successfully",
                    "summary": "All tests passed and code was successfully refactored."
                }
            }
        }
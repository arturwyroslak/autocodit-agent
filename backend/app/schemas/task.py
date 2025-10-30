"""
AutoCodit Agent - Task Schemas

Pydantic models for task-related API operations.
"""

from datetime import datetime
from typing import Dict, Any, Optional, List
from pydantic import BaseModel, Field, validator

from app.models.task import TaskStatus, TaskPriority, ActionType


class TaskBase(BaseModel):
    """Base task schema"""
    title: str = Field(..., min_length=1, max_length=500, description="Task title")
    description: Optional[str] = Field(None, description="Task description")
    repository: str = Field(..., description="Repository full name (owner/repo)")
    action_type: ActionType = Field(ActionType.PLAN, description="Type of action to perform")
    priority: TaskPriority = Field(TaskPriority.NORMAL, description="Task priority")
    agent_config: Dict[str, Any] = Field(default_factory=dict, description="Agent configuration")
    timeout_minutes: int = Field(60, ge=1, le=480, description="Task timeout in minutes")
    
    @validator("repository")
    def validate_repository(cls, v):
        if "/" not in v:
            raise ValueError("Repository must be in format 'owner/repo'")
        parts = v.split("/")
        if len(parts) != 2 or not all(parts):
            raise ValueError("Repository must be in format 'owner/repo'")
        return v


class CreateTaskRequest(TaskBase):
    """Request to create a new task"""
    issue_number: Optional[int] = Field(None, description="GitHub issue number")
    pr_number: Optional[int] = Field(None, description="GitHub PR number")
    comment_id: Optional[str] = Field(None, description="GitHub comment ID")
    branch_name: Optional[str] = Field(None, description="Target branch name")
    github_installation_id: Optional[int] = Field(None, description="GitHub App installation ID")
    triggered_by: Optional[str] = Field(None, description="How the task was triggered")
    
    class Config:
        json_schema_extra = {
            "example": {
                "title": "Fix authentication bug",
                "description": "Fix the JWT token validation issue in the auth module",
                "repository": "myorg/myrepo",
                "action_type": "fix",
                "priority": "high",
                "issue_number": 123,
                "timeout_minutes": 120,
                "agent_config": {
                    "model": "gpt-4-turbo",
                    "temperature": 0.1,
                    "tools": ["github-mcp", "test-runner"]
                }
            }
        }


class UpdateTaskRequest(BaseModel):
    """Request to update a task"""
    title: Optional[str] = Field(None, min_length=1, max_length=500)
    description: Optional[str] = None
    priority: Optional[TaskPriority] = None
    agent_config: Optional[Dict[str, Any]] = None
    timeout_minutes: Optional[int] = Field(None, ge=1, le=480)


class TaskResponse(BaseModel):
    """Task response schema"""
    id: str
    title: str
    description: Optional[str]
    repository: str
    issue_number: Optional[int]
    pr_number: Optional[int]
    comment_id: Optional[str]
    branch_name: Optional[str]
    action_type: ActionType
    status: TaskStatus
    priority: TaskPriority
    progress: float = Field(..., ge=0.0, le=1.0)
    error_message: Optional[str]
    retry_count: int
    max_retries: int
    github_installation_id: Optional[int]
    triggered_by: Optional[str]
    agent_config: Dict[str, Any]
    tokens_used: int
    cost: float
    estimated_duration: Optional[int]
    timeout_minutes: int
    created_at: datetime
    updated_at: datetime
    started_at: Optional[datetime]
    completed_at: Optional[datetime]
    user_id: Optional[str]
    session_id: Optional[str]
    
    # Computed properties
    duration: Optional[int] = None
    is_finished: bool = False
    can_retry: bool = False
    
    class Config:
        from_attributes = True
        json_encoders = {
            datetime: lambda v: v.isoformat() if v else None
        }
        json_schema_extra = {
            "example": {
                "id": "123e4567-e89b-12d3-a456-426614174000",
                "title": "Fix authentication bug",
                "description": "Fix the JWT token validation issue",
                "repository": "myorg/myrepo",
                "action_type": "fix",
                "status": "completed",
                "priority": "high",
                "progress": 1.0,
                "tokens_used": 15000,
                "cost": 0.25,
                "duration": 1800,
                "created_at": "2023-01-01T12:00:00Z",
                "completed_at": "2023-01-01T12:30:00Z"
            }
        }


class TaskListResponse(BaseModel):
    """Response for listing tasks"""
    items: List[TaskResponse]
    total: int
    page: int
    per_page: int
    has_next: bool
    has_prev: bool


class TaskMetrics(BaseModel):
    """Task execution metrics"""
    execution_time: int = Field(..., description="Execution time in seconds")
    tokens_used: int = Field(..., description="Total tokens consumed")
    cost: float = Field(..., description="Total cost in USD")
    files_changed: int = Field(..., description="Number of files modified")
    lines_added: int = Field(..., description="Lines of code added")
    lines_removed: int = Field(..., description="Lines of code removed")
    commits_created: int = Field(..., description="Number of commits created")
    tests_run: int = Field(..., description="Number of tests executed")
    tests_passed: int = Field(..., description="Number of tests passed")
    coverage_change: float = Field(..., description="Code coverage change percentage")
    
    class Config:
        json_schema_extra = {
            "example": {
                "execution_time": 1800,
                "tokens_used": 15000,
                "cost": 0.25,
                "files_changed": 3,
                "lines_added": 45,
                "lines_removed": 12,
                "commits_created": 2,
                "tests_run": 25,
                "tests_passed": 23,
                "coverage_change": 2.5
            }
        }


class TaskLog(BaseModel):
    """Task log entry"""
    timestamp: datetime
    level: str = Field(..., description="Log level (DEBUG, INFO, WARNING, ERROR)")
    message: str = Field(..., description="Log message")
    component: Optional[str] = Field(None, description="Component that generated the log")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional metadata")
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class TaskArtifact(BaseModel):
    """Task artifact (file, screenshot, etc.)"""
    id: str
    name: str
    type: str = Field(..., description="Artifact type (file, screenshot, report, etc.)")
    size: int = Field(..., description="Size in bytes")
    url: str = Field(..., description="Download URL")
    created_at: datetime
    metadata: Dict[str, Any] = Field(default_factory=dict)
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }
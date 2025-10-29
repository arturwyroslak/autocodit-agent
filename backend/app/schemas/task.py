"""
AutoCodit Agent - Task Schemas

Pydantic models for task-related API requests and responses.
"""

from datetime import datetime
from typing import Dict, Any, List, Optional
from uuid import UUID

from pydantic import BaseModel, Field, validator

from app.models.task import TaskStatus, TaskPriority, ActionType


class CreateTaskRequest(BaseModel):
    """Request to create a new task"""
    title: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = Field(None, max_length=10000)
    repository: str = Field(..., min_length=1, max_length=255)
    issue_number: Optional[int] = Field(None, ge=1)
    pr_number: Optional[int] = Field(None, ge=1)
    comment_id: Optional[str] = Field(None, max_length=50)
    action_type: ActionType = Field(default=ActionType.PLAN)
    priority: TaskPriority = Field(default=TaskPriority.NORMAL)
    agent_config: Optional[Dict[str, Any]] = Field(default_factory=dict)
    github_installation_id: Optional[int] = Field(None, ge=1)
    
    class Config:
        json_schema_extra = {
            "example": {
                "title": "Fix authentication bug",
                "description": "There's a bug in the JWT token validation that allows expired tokens to pass through",
                "repository": "myorg/myapp",
                "issue_number": 123,
                "action_type": "fix",
                "priority": "high",
                "agent_config": {
                    "model": "gpt-4-turbo",
                    "temperature": 0.1,
                    "max_tokens": 4000
                },
                "github_installation_id": 12345
            }
        }


class UpdateTaskRequest(BaseModel):
    """Request to update a task"""
    title: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = Field(None, max_length=10000)
    priority: Optional[TaskPriority] = None
    agent_config: Optional[Dict[str, Any]] = None
    
    class Config:
        json_schema_extra = {
            "example": {
                "title": "Fix authentication and add tests",
                "priority": "urgent",
                "agent_config": {
                    "include_tests": True,
                    "test_framework": "pytest"
                }
            }
        }


class TaskResponse(BaseModel):
    """Task response model"""
    id: UUID
    title: str
    description: Optional[str]
    repository: str
    issue_number: Optional[int]
    pr_number: Optional[int]
    comment_id: Optional[str]
    action_type: ActionType
    status: TaskStatus
    priority: TaskPriority
    progress: float
    
    # Timing
    created_at: datetime
    updated_at: datetime
    started_at: Optional[datetime]
    completed_at: Optional[datetime]
    
    # Configuration and metadata
    agent_config: Dict[str, Any]
    triggered_by: Optional[str]
    github_installation_id: Optional[int]
    user_id: Optional[str]
    organization_id: Optional[str]
    
    # Resource usage
    tokens_used: int
    cost: float
    execution_time_seconds: int
    
    # Results
    result_data: Dict[str, Any]
    artifacts_url: Optional[str]
    error_message: Optional[str]
    
    # Computed properties
    is_active: bool
    is_finished: bool
    duration_seconds: Optional[int]
    
    class Config:
        from_attributes = True
        json_schema_extra = {
            "example": {
                "id": "123e4567-e89b-12d3-a456-426614174000",
                "title": "Fix authentication bug",
                "description": "JWT token validation issue",
                "repository": "myorg/myapp",
                "issue_number": 123,
                "action_type": "fix",
                "status": "running",
                "priority": "high",
                "progress": 0.6,
                "created_at": "2025-10-29T20:00:00Z",
                "updated_at": "2025-10-29T20:15:00Z",
                "started_at": "2025-10-29T20:01:00Z",
                "tokens_used": 2500,
                "cost": 0.05,
                "execution_time_seconds": 900,
                "is_active": True,
                "is_finished": False,
                "duration_seconds": 840
            }
        }


class TaskListResponse(BaseModel):
    """Response for task list queries"""
    tasks: List[TaskResponse]
    total: int
    page: int = Field(ge=1)
    per_page: int = Field(ge=1, le=100)
    total_pages: int = Field(ge=1)
    
    class Config:
        json_schema_extra = {
            "example": {
                "tasks": ["..."],  # TaskResponse objects
                "total": 42,
                "page": 1,
                "per_page": 20,
                "total_pages": 3
            }
        }


class TaskLogEntry(BaseModel):
    """Task log entry"""
    id: UUID
    level: str
    message: str
    component: Optional[str]
    data: Dict[str, Any]
    created_at: datetime
    
    class Config:
        from_attributes = True
        json_schema_extra = {
            "example": {
                "id": "123e4567-e89b-12d3-a456-426614174000",
                "level": "INFO",
                "message": "Started analyzing repository structure",
                "component": "agent",
                "data": {
                    "files_found": 42,
                    "languages": ["python", "javascript"]
                },
                "created_at": "2025-10-29T20:05:00Z"
            }
        }


class TaskLogsResponse(BaseModel):
    """Response for task logs"""
    logs: List[TaskLogEntry]
    total: int
    page: int = Field(ge=1)
    per_page: int = Field(ge=1, le=1000)
    
    class Config:
        json_schema_extra = {
            "example": {
                "logs": ["..."],  # TaskLogEntry objects
                "total": 150,
                "page": 1,
                "per_page": 100
            }
        }


class TaskMetricEntry(BaseModel):
    """Task metric entry"""
    metric_name: str
    metric_value: float
    metric_unit: Optional[str]
    tags: Dict[str, Any]
    recorded_at: datetime
    
    class Config:
        from_attributes = True


class TaskMetricsResponse(BaseModel):
    """Response for task metrics"""
    metrics: List[TaskMetricEntry]
    summary: Dict[str, Any]
    
    class Config:
        json_schema_extra = {
            "example": {
                "metrics": [
                    {
                        "metric_name": "tokens_used",
                        "metric_value": 2500.0,
                        "metric_unit": "tokens",
                        "tags": {"provider": "openai", "model": "gpt-4-turbo"},
                        "recorded_at": "2025-10-29T20:15:00Z"
                    }
                ],
                "summary": {
                    "total_cost": 0.05,
                    "total_tokens": 2500,
                    "execution_time": 900,
                    "files_changed": 3
                }
            }
        }


class AgentProfileResponse(BaseModel):
    """Agent profile response"""
    id: UUID
    name: str
    description: Optional[str]
    model_config: Dict[str, Any]
    system_prompt: Optional[str]
    behavior_config: Dict[str, Any]
    tools_config: Dict[str, Any]
    mcp_servers: List[Dict[str, Any]]
    security_config: Dict[str, Any]
    resource_limits: Dict[str, Any]
    is_public: bool
    usage_count: int
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True
        json_schema_extra = {
            "example": {
                "id": "123e4567-e89b-12d3-a456-426614174000",
                "name": "Frontend Specialist",
                "description": "Expert in React, TypeScript, and modern frontend practices",
                "model_config": {
                    "primary_model": "gpt-4-turbo",
                    "fallback_model": "claude-3-sonnet",
                    "temperature": 0.2,
                    "max_tokens": 4000
                },
                "system_prompt": "You are a frontend development expert...",
                "tools_config": {
                    "enabled_tools": ["npm", "playwright", "jest"]
                },
                "is_public": False,
                "usage_count": 25,
                "created_at": "2025-10-29T10:00:00Z"
            }
        }
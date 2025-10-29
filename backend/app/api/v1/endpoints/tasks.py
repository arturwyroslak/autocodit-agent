"""
AutoCodit Agent - Tasks API Endpoints

RESTful API endpoints for task management.
"""

from typing import List, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.services.task_service import TaskService
from app.models.task import TaskStatus, TaskPriority, ActionType
from app.schemas.task import (
    CreateTaskRequest,
    UpdateTaskRequest,
    TaskResponse,
    TaskListResponse,
    TaskLogsResponse,
    TaskMetricsResponse
)
from app.core.auth import get_current_user
from app.models.user import User

router = APIRouter()
task_service = TaskService()


@router.post("/", response_model=TaskResponse, status_code=201)
async def create_task(
    request: CreateTaskRequest,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Create a new coding task"""
    
    # Check user's task limits
    if current_user.monthly_task_limit > 0:  # -1 means unlimited
        # TODO: Check current month's task count
        pass
    
    # Prepare task data
    task_data = request.dict()
    task_data["user_id"] = str(current_user.github_id)
    
    # Create task
    task = await task_service.create_task(task_data)
    
    return task


@router.get("/", response_model=TaskListResponse)
async def list_tasks(
    status: Optional[TaskStatus] = Query(None, description="Filter by task status"),
    repository: Optional[str] = Query(None, description="Filter by repository"),
    action_type: Optional[ActionType] = Query(None, description="Filter by action type"),
    priority: Optional[TaskPriority] = Query(None, description="Filter by priority"),
    page: int = Query(1, ge=1, description="Page number"),
    per_page: int = Query(20, ge=1, le=100, description="Tasks per page"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """List tasks for current user"""
    
    offset = (page - 1) * per_page
    
    # Get tasks
    tasks = await task_service.list_tasks(
        user_id=str(current_user.github_id),
        status=status,
        repository=repository,
        limit=per_page,
        offset=offset
    )
    
    # Get total count (TODO: implement in service)
    total = len(tasks)  # Simplified for now
    total_pages = (total + per_page - 1) // per_page
    
    return TaskListResponse(
        tasks=tasks,
        total=total,
        page=page,
        per_page=per_page,
        total_pages=total_pages
    )


@router.get("/{task_id}", response_model=TaskResponse)
async def get_task(
    task_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get task by ID"""
    
    task = await task_service.get_task(
        task_id=str(task_id),
        user_id=str(current_user.github_id)
    )
    
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    
    return task


@router.patch("/{task_id}", response_model=TaskResponse)
async def update_task(
    task_id: UUID,
    request: UpdateTaskRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Update task"""
    
    # Check if task exists and belongs to user
    task = await task_service.get_task(
        task_id=str(task_id),
        user_id=str(current_user.github_id)
    )
    
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    
    if task.is_finished:
        raise HTTPException(
            status_code=400,
            detail="Cannot update finished task"
        )
    
    # TODO: Implement update in service
    return task


@router.delete("/{task_id}", status_code=204)
async def cancel_task(
    task_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Cancel a running task"""
    
    success = await task_service.cancel_task(
        task_id=str(task_id),
        user_id=str(current_user.github_id)
    )
    
    if not success:
        raise HTTPException(
            status_code=404,
            detail="Task not found or cannot be cancelled"
        )


@router.get("/{task_id}/logs", response_model=TaskLogsResponse)
async def get_task_logs(
    task_id: UUID,
    level: Optional[str] = Query(None, description="Filter by log level"),
    component: Optional[str] = Query(None, description="Filter by component"),
    page: int = Query(1, ge=1, description="Page number"),
    per_page: int = Query(100, ge=1, le=1000, description="Logs per page"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get task execution logs"""
    
    # Check if task exists and belongs to user
    task = await task_service.get_task(
        task_id=str(task_id),
        user_id=str(current_user.github_id)
    )
    
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    
    offset = (page - 1) * per_page
    
    logs = await task_service.get_task_logs(
        task_id=str(task_id),
        limit=per_page,
        offset=offset
    )
    
    return TaskLogsResponse(
        logs=logs,
        total=len(logs),  # Simplified
        page=page,
        per_page=per_page
    )


@router.get("/{task_id}/metrics", response_model=TaskMetricsResponse)
async def get_task_metrics(
    task_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get task execution metrics"""
    
    # Check if task exists and belongs to user
    task = await task_service.get_task(
        task_id=str(task_id),
        user_id=str(current_user.github_id)
    )
    
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    
    metrics = await task_service.get_task_metrics(str(task_id))
    
    return TaskMetricsResponse(
        metrics=[],  # TODO: Implement
        summary=metrics
    )


@router.post("/{task_id}/retry", response_model=TaskResponse)
async def retry_task(
    task_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Retry a failed task"""
    
    # Check if task exists and belongs to user
    task = await task_service.get_task(
        task_id=str(task_id),
        user_id=str(current_user.github_id)
    )
    
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    
    if task.status != TaskStatus.FAILED:
        raise HTTPException(
            status_code=400,
            detail="Only failed tasks can be retried"
        )
    
    # TODO: Implement retry logic
    return task
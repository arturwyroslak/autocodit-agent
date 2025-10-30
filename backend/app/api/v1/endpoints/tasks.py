"""
AutoCodit Agent - Task API Endpoints

API endpoints for task management and monitoring.
"""

from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession
import structlog

from app.core.database import get_db
from app.services.task_service import TaskService
from app.schemas.task import (
    CreateTaskRequest,
    UpdateTaskRequest,
    TaskResponse,
    TaskListResponse,
    TaskMetrics,
    TaskLog,
    TaskArtifact
)
from app.models.task import TaskStatus, TaskPriority, ActionType
from app.core.auth import get_current_user
from app.models.user import User

logger = structlog.get_logger()
router = APIRouter()


@router.post("/", response_model=TaskResponse, status_code=201)
async def create_task(
    task_request: CreateTaskRequest,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
    current_user: Optional[User] = Depends(get_current_user)
):
    """Create a new coding task"""
    task_service = TaskService()
    
    try:
        # Add user context if authenticated
        task_data = task_request.dict()
        if current_user:
            task_data["user_id"] = str(current_user.id)
        
        task = await task_service.create_task(task_data)
        
        logger.info(
            "Task created via API",
            task_id=task.id,
            repository=task.repository,
            action_type=task.action_type,
            user_id=current_user.id if current_user else None
        )
        
        return task
    
    except Exception as e:
        logger.error("Failed to create task", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/", response_model=TaskListResponse)
async def list_tasks(
    status: Optional[TaskStatus] = Query(None, description="Filter by status"),
    repository: Optional[str] = Query(None, description="Filter by repository"),
    action_type: Optional[ActionType] = Query(None, description="Filter by action type"),
    priority: Optional[TaskPriority] = Query(None, description="Filter by priority"),
    page: int = Query(1, ge=1, description="Page number"),
    per_page: int = Query(50, ge=1, le=100, description="Items per page"),
    db: AsyncSession = Depends(get_db),
    current_user: Optional[User] = Depends(get_current_user)
):
    """List tasks with filtering and pagination"""
    task_service = TaskService()
    
    try:
        user_id = str(current_user.id) if current_user else None
        offset = (page - 1) * per_page
        
        tasks = await task_service.list_tasks(
            user_id=user_id,
            status=status,
            repository=repository,
            limit=per_page,
            offset=offset
        )
        
        # Get total count (simplified for now)
        total = len(tasks) + offset if len(tasks) == per_page else len(tasks) + offset
        
        return TaskListResponse(
            items=tasks,
            total=total,
            page=page,
            per_page=per_page,
            has_next=len(tasks) == per_page,
            has_prev=page > 1
        )
    
    except Exception as e:
        logger.error("Failed to list tasks", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{task_id}", response_model=TaskResponse)
async def get_task(
    task_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: Optional[User] = Depends(get_current_user)
):
    """Get task by ID"""
    task_service = TaskService()
    
    try:
        user_id = str(current_user.id) if current_user else None
        task = await task_service.get_task(task_id, user_id)
        
        if not task:
            raise HTTPException(status_code=404, detail="Task not found")
        
        return task
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Failed to get task", task_id=task_id, error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


@router.patch("/{task_id}", response_model=TaskResponse)
async def update_task(
    task_id: str,
    task_update: UpdateTaskRequest,
    db: AsyncSession = Depends(get_db),
    current_user: Optional[User] = Depends(get_current_user)
):
    """Update task"""
    # TODO: Implement task updates
    raise HTTPException(status_code=501, detail="Task updates not yet implemented")


@router.post("/{task_id}/cancel")
async def cancel_task(
    task_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: Optional[User] = Depends(get_current_user)
):
    """Cancel a running task"""
    task_service = TaskService()
    
    try:
        user_id = str(current_user.id) if current_user else None
        success = await task_service.cancel_task(task_id, user_id)
        
        if not success:
            raise HTTPException(status_code=404, detail="Task not found or cannot be cancelled")
        
        logger.info("Task cancelled", task_id=task_id, user_id=user_id)
        
        return {"message": "Task cancelled successfully"}
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Failed to cancel task", task_id=task_id, error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/{task_id}/retry")
async def retry_task(
    task_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: Optional[User] = Depends(get_current_user)
):
    """Retry a failed task"""
    # TODO: Implement task retry
    raise HTTPException(status_code=501, detail="Task retry not yet implemented")


@router.get("/{task_id}/logs", response_model=List[TaskLog])
async def get_task_logs(
    task_id: str,
    limit: int = Query(100, ge=1, le=1000, description="Number of log entries"),
    offset: int = Query(0, ge=0, description="Offset for pagination"),
    level: Optional[str] = Query(None, description="Filter by log level"),
    db: AsyncSession = Depends(get_db),
    current_user: Optional[User] = Depends(get_current_user)
):
    """Get task execution logs"""
    task_service = TaskService()
    
    try:
        # Verify task exists and user has access
        user_id = str(current_user.id) if current_user else None
        task = await task_service.get_task(task_id, user_id)
        
        if not task:
            raise HTTPException(status_code=404, detail="Task not found")
        
        logs = await task_service.get_task_logs(task_id, limit, offset)
        
        return logs
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Failed to get task logs", task_id=task_id, error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{task_id}/metrics", response_model=TaskMetrics)
async def get_task_metrics(
    task_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: Optional[User] = Depends(get_current_user)
):
    """Get task execution metrics"""
    task_service = TaskService()
    
    try:
        # Verify task exists and user has access
        user_id = str(current_user.id) if current_user else None
        task = await task_service.get_task(task_id, user_id)
        
        if not task:
            raise HTTPException(status_code=404, detail="Task not found")
        
        metrics = await task_service.get_task_metrics(task_id)
        
        return TaskMetrics(**metrics)
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Failed to get task metrics", task_id=task_id, error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{task_id}/artifacts", response_model=List[TaskArtifact])
async def get_task_artifacts(
    task_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: Optional[User] = Depends(get_current_user)
):
    """Get task artifacts"""
    task_service = TaskService()
    
    try:
        # Verify task exists and user has access
        user_id = str(current_user.id) if current_user else None
        task = await task_service.get_task(task_id, user_id)
        
        if not task:
            raise HTTPException(status_code=404, detail="Task not found")
        
        artifacts = await task_service.get_task_artifacts(task_id)
        
        return artifacts
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Failed to get task artifacts", task_id=task_id, error=str(e))
        raise HTTPException(status_code=500, detail=str(e))
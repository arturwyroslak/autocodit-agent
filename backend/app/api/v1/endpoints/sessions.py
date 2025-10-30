"""
AutoCodit Agent - Session API Endpoints

API endpoints for session management and monitoring.
"""

from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
import structlog

from app.core.database import get_db
from app.services.runner_service import RunnerService
from app.schemas.session import (
    CreateSessionRequest,
    SessionResponse,
    SessionListResponse,
    SessionMetrics,
    SessionLog,
    SessionCommand,
    SessionCommandResult
)
from app.models.session import SessionStatus
from app.core.auth import get_current_user
from app.models.user import User

logger = structlog.get_logger()
router = APIRouter()


@router.post("/", response_model=SessionResponse, status_code=201)
async def create_session(
    session_request: CreateSessionRequest,
    db: AsyncSession = Depends(get_db),
    current_user: Optional[User] = Depends(get_current_user)
):
    """Create a new execution session"""
    runner_service = RunnerService()
    
    try:
        config = session_request.dict()
        if current_user:
            config["user_id"] = str(current_user.id)
        
        session = await runner_service.create_runner(
            task_id=session_request.task_id,
            config=config
        )
        
        logger.info(
            "Session created via API",
            session_id=session.id,
            task_id=session_request.task_id,
            user_id=current_user.id if current_user else None
        )
        
        return session
    
    except Exception as e:
        logger.error("Failed to create session", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/", response_model=SessionListResponse)
async def list_sessions(
    status: Optional[SessionStatus] = Query(None, description="Filter by status"),
    page: int = Query(1, ge=1, description="Page number"),
    per_page: int = Query(50, ge=1, le=100, description="Items per page"),
    db: AsyncSession = Depends(get_db),
    current_user: Optional[User] = Depends(get_current_user)
):
    """List sessions with filtering and pagination"""
    # TODO: Implement session listing
    return SessionListResponse(
        items=[],
        total=0,
        page=page,
        per_page=per_page,
        has_next=False,
        has_prev=False
    )


@router.get("/{session_id}", response_model=SessionResponse)
async def get_session(
    session_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: Optional[User] = Depends(get_current_user)
):
    """Get session by ID"""
    # TODO: Implement session retrieval
    raise HTTPException(status_code=404, detail="Session not found")


@router.delete("/{session_id}")
async def cancel_session(
    session_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: Optional[User] = Depends(get_current_user)
):
    """Cancel and stop a running session"""
    runner_service = RunnerService()
    
    try:
        success = await runner_service.cancel_runner(session_id)
        
        if not success:
            raise HTTPException(status_code=404, detail="Session not found or cannot be cancelled")
        
        logger.info("Session cancelled", session_id=session_id)
        
        return {"message": "Session cancelled successfully"}
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Failed to cancel session", session_id=session_id, error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{session_id}/status")
async def get_session_status(
    session_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: Optional[User] = Depends(get_current_user)
):
    """Get session status and resource usage"""
    runner_service = RunnerService()
    
    try:
        status = await runner_service.get_runner_status(session_id)
        
        if not status:
            raise HTTPException(status_code=404, detail="Session not found")
        
        return status
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Failed to get session status", session_id=session_id, error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{session_id}/logs", response_model=List[str])
async def get_session_logs(
    session_id: str,
    tail: int = Query(100, ge=1, le=1000, description="Number of log lines"),
    follow: bool = Query(False, description="Follow logs (streaming)"),
    db: AsyncSession = Depends(get_db),
    current_user: Optional[User] = Depends(get_current_user)
):
    """Get session logs"""
    runner_service = RunnerService()
    
    try:
        logs = await runner_service.get_runner_logs(
            session_id=session_id,
            tail=tail,
            follow=follow
        )
        
        return logs
    
    except Exception as e:
        logger.error("Failed to get session logs", session_id=session_id, error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{session_id}/metrics", response_model=SessionMetrics)
async def get_session_metrics(
    session_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: Optional[User] = Depends(get_current_user)
):
    """Get session resource metrics"""
    runner_service = RunnerService()
    
    try:
        status = await runner_service.get_runner_status(session_id)
        
        if not status:
            raise HTTPException(status_code=404, detail="Session not found")
        
        resources = status.get("resources", {})
        
        return SessionMetrics(
            memory_usage=resources.get("memory_usage", 0),
            memory_limit=resources.get("memory_limit", 0),
            memory_percentage=(resources.get("memory_usage", 0) / max(resources.get("memory_limit", 1), 1)) * 100,
            cpu_usage=resources.get("cpu_usage", 0.0),
            network_rx=resources.get("network_io", {}).get("rx_bytes", 0),
            network_tx=resources.get("network_io", {}).get("tx_bytes", 0),
            disk_read=resources.get("block_io", {}).get("read", 0),
            disk_write=resources.get("block_io", {}).get("write", 0),
            uptime=0  # TODO: Calculate from started_at
        )
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Failed to get session metrics", session_id=session_id, error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/{session_id}/exec", response_model=SessionCommandResult)
async def execute_command(
    session_id: str,
    command: SessionCommand,
    db: AsyncSession = Depends(get_db),
    current_user: Optional[User] = Depends(get_current_user)
):
    """Execute command in session"""
    # TODO: Implement command execution in container
    raise HTTPException(status_code=501, detail="Command execution not yet implemented")
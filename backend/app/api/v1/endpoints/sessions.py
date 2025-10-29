"""
AutoCodit Agent - Sessions API Endpoints

RESTful API endpoints for session monitoring and management.
"""

from typing import List, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, WebSocket, WebSocketDisconnect
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.services.runner_service import RunnerService
from app.schemas.session import (
    SessionResponse,
    SessionStepsResponse,
    SessionArtifactsResponse,
    SessionEventsResponse,
    ResourceUsageResponse
)
from app.core.auth import get_current_user
from app.models.user import User
from app.websocket.manager import websocket_manager

router = APIRouter()
runner_service = RunnerService()


@router.get("/{session_id}", response_model=SessionResponse)
async def get_session(
    session_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get session details"""
    
    # TODO: Implement session retrieval with user validation
    raise HTTPException(status_code=501, detail="Not implemented")


@router.get("/{session_id}/steps", response_model=SessionStepsResponse)
async def get_session_steps(
    session_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get session execution steps"""
    
    # TODO: Implement steps retrieval
    return SessionStepsResponse(steps=[], total=0)


@router.get("/{session_id}/artifacts", response_model=SessionArtifactsResponse)
async def get_session_artifacts(
    session_id: UUID,
    artifact_type: Optional[str] = Query(None, description="Filter by artifact type"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get session artifacts (screenshots, files, etc.)"""
    
    # TODO: Implement artifacts retrieval
    return SessionArtifactsResponse(artifacts=[], total=0)


@router.get("/{session_id}/events", response_model=SessionEventsResponse)
async def get_session_events(
    session_id: UUID,
    event_type: Optional[str] = Query(None, description="Filter by event type"),
    level: Optional[str] = Query(None, description="Filter by level"),
    page: int = Query(1, ge=1, description="Page number"),
    per_page: int = Query(50, ge=1, le=1000, description="Events per page"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get session events"""
    
    # TODO: Implement events retrieval with pagination
    return SessionEventsResponse(
        events=[],
        total=0,
        page=page,
        per_page=per_page
    )


@router.get("/{session_id}/resource-usage", response_model=ResourceUsageResponse)
async def get_session_resource_usage(
    session_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get real-time resource usage for session"""
    
    # Get runner status
    status = await runner_service.get_runner_status(str(session_id))
    
    if not status:
        raise HTTPException(status_code=404, detail="Session not found")
    
    from datetime import datetime, timezone
    
    # Convert to response format
    return ResourceUsageResponse(
        session_id=session_id,
        cpu_usage_percent=status["resources"].get("cpu_usage", 0.0),
        memory_usage_mb=status["resources"].get("memory_usage", 0) // (1024 * 1024),
        memory_limit_mb=status["resources"].get("memory_limit", 0) // (1024 * 1024),
        network_io=status["resources"].get("network_io", {}),
        total_cpu_time_seconds=0.0,  # TODO: Calculate from stats
        peak_memory_mb=0,  # TODO: Track peak usage
        total_network_bytes=0,  # TODO: Calculate total
        measured_at=datetime.now(timezone.utc)
    )


@router.get("/{session_id}/logs")
async def get_session_logs(
    session_id: UUID,
    tail: int = Query(100, ge=1, le=10000, description="Number of lines to tail"),
    follow: bool = Query(False, description="Follow log stream"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get session logs"""
    
    logs = await runner_service.get_runner_logs(
        session_id=str(session_id),
        tail=tail,
        follow=follow
    )
    
    if follow:
        # TODO: Implement streaming response
        pass
    
    return {"logs": logs}


@router.delete("/{session_id}", status_code=204)
async def cancel_session(
    session_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Cancel running session"""
    
    success = await runner_service.cancel_runner(str(session_id))
    
    if not success:
        raise HTTPException(
            status_code=404,
            detail="Session not found or cannot be cancelled"
        )


@router.websocket("/{session_id}/ws")
async def session_websocket(
    websocket: WebSocket,
    session_id: UUID
):
    """WebSocket endpoint for real-time session updates"""
    
    await websocket_manager.connect(websocket, f"session:{session_id}")
    
    try:
        while True:
            # Keep connection alive
            data = await websocket.receive_text()
            
            # Handle client messages if needed
            import json
            try:
                message = json.loads(data)
                if message.get("type") == "ping":
                    await websocket.send_json({"type": "pong"})
            except json.JSONDecodeError:
                pass
                
    except WebSocketDisconnect:
        websocket_manager.disconnect(f"session:{session_id}")


@router.post("/{session_id}/steer", response_model=dict)
async def steer_session(
    session_id: UUID,
    action: dict,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Steer running session (pause, resume, modify parameters)"""
    
    # TODO: Implement session steering
    # This would allow users to:
    # - Pause/resume execution
    # - Modify agent parameters mid-execution
    # - Provide feedback or corrections
    # - Approve/reject changes
    
    action_type = action.get("type")
    
    if action_type == "pause":
        # Pause execution
        pass
    elif action_type == "resume":
        # Resume execution
        pass
    elif action_type == "feedback":
        # Provide feedback to agent
        pass
    elif action_type == "approve":
        # Approve current changes
        pass
    elif action_type == "reject":
        # Reject current changes
        pass
    else:
        raise HTTPException(status_code=400, detail="Unknown action type")
    
    return {"status": "accepted", "action": action_type}
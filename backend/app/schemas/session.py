"""
AutoCodit Agent - Session Schemas

Pydantic models for session-related API requests and responses.
"""

from datetime import datetime
from typing import Dict, Any, List, Optional
from uuid import UUID

from pydantic import BaseModel, Field

from app.models.session import SessionStatus, StepStatus


class SessionResponse(BaseModel):
    """Session response model"""
    id: UUID
    task_id: UUID
    status: SessionStatus
    
    # Container and execution details
    container_id: Optional[str]
    runner_image: Optional[str]
    runner_config: Dict[str, Any]
    
    # Timing
    created_at: datetime
    updated_at: datetime
    started_at: Optional[datetime]
    completed_at: Optional[datetime]
    timeout_at: Optional[datetime]
    
    # Progress
    progress: float
    current_step: Optional[str]
    total_steps: int
    completed_steps: int
    
    # Resource usage
    max_memory_mb: int
    cpu_time_seconds: float
    network_bytes_sent: int
    network_bytes_received: int
    
    # AI and cost tracking
    tokens_used: int
    ai_requests_count: int
    estimated_cost: float
    
    # Results
    output_summary: Optional[str]
    artifacts_urls: List[str]
    final_result: Dict[str, Any]
    
    # Error handling
    error_message: Optional[str]
    retry_count: int
    
    # Computed properties
    is_active: bool
    is_finished: bool
    duration_seconds: Optional[int]
    success_rate: float
    
    class Config:
        from_attributes = True
        json_schema_extra = {
            "example": {
                "id": "123e4567-e89b-12d3-a456-426614174000",
                "task_id": "987fcdeb-51a2-43d7-8f9e-123456789abc",
                "status": "running",
                "container_id": "abc123def456",
                "progress": 0.65,
                "current_step": "Running tests",
                "total_steps": 8,
                "completed_steps": 5,
                "tokens_used": 1200,
                "estimated_cost": 0.024,
                "is_active": True,
                "is_finished": False,
                "success_rate": 0.875
            }
        }


class SessionStepResponse(BaseModel):
    """Session step response model"""
    id: UUID
    session_id: UUID
    step_name: str
    step_type: str
    step_order: int
    status: StepStatus
    
    # Input and output
    input_data: Dict[str, Any]
    parameters: Dict[str, Any]
    output_data: Dict[str, Any]
    result_summary: Optional[str]
    
    # Timing
    created_at: datetime
    updated_at: datetime
    started_at: Optional[datetime]
    completed_at: Optional[datetime]
    
    # Resource usage
    tokens_used: int
    execution_time_ms: int
    memory_peak_mb: int
    
    # Error handling
    error_message: Optional[str]
    retry_count: int
    
    # Computed properties
    duration_ms: Optional[int]
    
    class Config:
        from_attributes = True
        json_schema_extra = {
            "example": {
                "id": "123e4567-e89b-12d3-a456-426614174000",
                "session_id": "987fcdeb-51a2-43d7-8f9e-123456789abc",
                "step_name": "Analyze code structure",
                "step_type": "ai_request",
                "step_order": 1,
                "status": "completed",
                "result_summary": "Found 5 Python modules with potential issues",
                "tokens_used": 450,
                "execution_time_ms": 2500,
                "duration_ms": 2500
            }
        }


class SessionStepsResponse(BaseModel):
    """Response for session steps list"""
    steps: List[SessionStepResponse]
    total: int
    
    class Config:
        json_schema_extra = {
            "example": {
                "steps": ["..."],  # SessionStepResponse objects
                "total": 8
            }
        }


class SessionArtifactResponse(BaseModel):
    """Session artifact response"""
    id: UUID
    session_id: UUID
    step_id: Optional[UUID]
    artifact_type: str
    artifact_name: str
    file_path: Optional[str]
    file_size_bytes: Optional[int]
    content_type: Optional[str]
    metadata: Dict[str, Any]
    storage_backend: str
    storage_url: Optional[str]
    created_at: datetime
    
    class Config:
        from_attributes = True
        json_schema_extra = {
            "example": {
                "id": "123e4567-e89b-12d3-a456-426614174000",
                "session_id": "987fcdeb-51a2-43d7-8f9e-123456789abc",
                "artifact_type": "screenshot",
                "artifact_name": "test_results.png",
                "file_size_bytes": 125680,
                "content_type": "image/png",
                "storage_backend": "s3",
                "storage_url": "https://artifacts.autocodit.com/screenshots/test_results.png",
                "created_at": "2025-10-29T20:15:00Z"
            }
        }


class SessionArtifactsResponse(BaseModel):
    """Response for session artifacts"""
    artifacts: List[SessionArtifactResponse]
    total: int
    
    class Config:
        json_schema_extra = {
            "example": {
                "artifacts": ["..."],  # SessionArtifactResponse objects
                "total": 5
            }
        }


class SessionEventResponse(BaseModel):
    """Session event response"""
    id: UUID
    session_id: UUID
    event_type: str
    event_data: Dict[str, Any]
    message: Optional[str]
    level: str
    created_at: datetime
    
    class Config:
        from_attributes = True
        json_schema_extra = {
            "example": {
                "id": "123e4567-e89b-12d3-a456-426614174000",
                "session_id": "987fcdeb-51a2-43d7-8f9e-123456789abc",
                "event_type": "step_completed",
                "event_data": {
                    "step_name": "Run tests",
                    "duration_ms": 5000,
                    "tests_passed": 42,
                    "tests_failed": 1
                },
                "message": "Test step completed with 1 failure",
                "level": "warning",
                "created_at": "2025-10-29T20:15:00Z"
            }
        }


class SessionEventsResponse(BaseModel):
    """Response for session events"""
    events: List[SessionEventResponse]
    total: int
    page: int = Field(ge=1)
    per_page: int = Field(ge=1, le=1000)
    
    class Config:
        json_schema_extra = {
            "example": {
                "events": ["..."],  # SessionEventResponse objects
                "total": 25,
                "page": 1,
                "per_page": 50
            }
        }


class ResourceUsageResponse(BaseModel):
    """Real-time resource usage response"""
    session_id: UUID
    
    # Current resource usage
    cpu_usage_percent: float
    memory_usage_mb: int
    memory_limit_mb: int
    network_io: Dict[str, int]
    
    # Cumulative usage
    total_cpu_time_seconds: float
    peak_memory_mb: int
    total_network_bytes: int
    
    # Timestamps
    measured_at: datetime
    
    class Config:
        json_schema_extra = {
            "example": {
                "session_id": "123e4567-e89b-12d3-a456-426614174000",
                "cpu_usage_percent": 45.2,
                "memory_usage_mb": 512,
                "memory_limit_mb": 2048,
                "network_io": {
                    "bytes_sent": 1024000,
                    "bytes_received": 2048000
                },
                "total_cpu_time_seconds": 125.5,
                "peak_memory_mb": 768,
                "total_network_bytes": 3072000,
                "measured_at": "2025-10-29T20:15:00Z"
            }
        }
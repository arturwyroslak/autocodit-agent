"""
AutoCodit Agent - Session Schemas

Pydantic models for session-related API operations.
"""

from datetime import datetime
from typing import Dict, Any, Optional, List
from pydantic import BaseModel, Field

from app.models.session import SessionStatus


class SessionBase(BaseModel):
    """Base session schema"""
    name: Optional[str] = Field(None, description="Session name")
    runner_config: Dict[str, Any] = Field(default_factory=dict, description="Runner configuration")
    environment_vars: Dict[str, Any] = Field(default_factory=dict, description="Environment variables")
    memory_limit: Optional[str] = Field(None, description="Memory limit (e.g., '2GB')")
    cpu_limit: Optional[str] = Field(None, description="CPU limit (e.g., '1000m')")
    network_name: Optional[str] = Field(None, description="Docker network name")
    volumes: List[str] = Field(default_factory=list, description="Volume mounts")


class CreateSessionRequest(SessionBase):
    """Request to create a new session"""
    task_id: str = Field(..., description="Associated task ID")
    image_name: str = Field("autocodit-agent-runner:latest", description="Container image")
    
    class Config:
        json_schema_extra = {
            "example": {
                "task_id": "123e4567-e89b-12d3-a456-426614174000",
                "name": "Fix Auth Bug Session",
                "image_name": "autocodit-agent-runner:latest",
                "memory_limit": "2GB",
                "cpu_limit": "1000m",
                "environment_vars": {
                    "TASK_TYPE": "fix",
                    "DEBUG": "true"
                },
                "runner_config": {
                    "timeout": 3600,
                    "model": "gpt-4-turbo"
                }
            }
        }


class SessionResponse(BaseModel):
    """Session response schema"""
    id: str
    name: Optional[str]
    status: SessionStatus
    container_id: Optional[str]
    container_name: Optional[str]
    image_name: Optional[str]
    runner_config: Dict[str, Any]
    environment_vars: Dict[str, Any]
    memory_limit: Optional[str]
    cpu_limit: Optional[str]
    memory_used: int
    cpu_used: float
    network_name: Optional[str]
    volumes: List[str]
    exit_code: Optional[int]
    error_message: Optional[str]
    log_file_path: Optional[str]
    output_files: List[str]
    artifacts: List[str]
    last_heartbeat: Optional[datetime]
    health_check_failures: int
    security_violations: List[Dict[str, Any]]
    firewall_blocks: int
    created_at: datetime
    updated_at: datetime
    started_at: Optional[datetime]
    finished_at: Optional[datetime]
    user_id: Optional[str]
    
    # Computed properties
    duration: Optional[int] = None
    is_running: bool = False
    is_finished: bool = False
    memory_usage_mb: float = 0.0
    
    class Config:
        from_attributes = True
        json_encoders = {
            datetime: lambda v: v.isoformat() if v else None
        }
        json_schema_extra = {
            "example": {
                "id": "123e4567-e89b-12d3-a456-426614174000",
                "name": "Fix Auth Bug Session",
                "status": "running",
                "container_id": "abc123def456",
                "image_name": "autocodit-agent-runner:latest",
                "memory_used": 1073741824,
                "cpu_used": 45.2,
                "duration": 1200,
                "is_running": True,
                "memory_usage_mb": 1024.0,
                "created_at": "2023-01-01T12:00:00Z",
                "started_at": "2023-01-01T12:01:00Z"
            }
        }


class SessionListResponse(BaseModel):
    """Response for listing sessions"""
    items: List[SessionResponse]
    total: int
    page: int
    per_page: int
    has_next: bool
    has_prev: bool


class SessionMetrics(BaseModel):
    """Session resource metrics"""
    memory_usage: int = Field(..., description="Memory usage in bytes")
    memory_limit: int = Field(..., description="Memory limit in bytes")
    memory_percentage: float = Field(..., description="Memory usage percentage")
    cpu_usage: float = Field(..., description="CPU usage percentage")
    network_rx: int = Field(..., description="Network bytes received")
    network_tx: int = Field(..., description="Network bytes transmitted")
    disk_read: int = Field(..., description="Disk bytes read")
    disk_write: int = Field(..., description="Disk bytes written")
    uptime: int = Field(..., description="Uptime in seconds")
    
    class Config:
        json_schema_extra = {
            "example": {
                "memory_usage": 1073741824,
                "memory_limit": 2147483648,
                "memory_percentage": 50.0,
                "cpu_usage": 45.2,
                "network_rx": 1048576,
                "network_tx": 524288,
                "disk_read": 2097152,
                "disk_write": 1048576,
                "uptime": 1800
            }
        }


class SessionLog(BaseModel):
    """Session log entry"""
    timestamp: datetime
    level: str = Field(..., description="Log level")
    message: str = Field(..., description="Log message")
    source: str = Field(..., description="Log source (stdout, stderr, system)")
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class SessionCommand(BaseModel):
    """Command to execute in session"""
    command: str = Field(..., description="Command to execute")
    timeout: int = Field(300, description="Command timeout in seconds")
    capture_output: bool = Field(True, description="Capture command output")
    
    class Config:
        json_schema_extra = {
            "example": {
                "command": "npm test",
                "timeout": 600,
                "capture_output": True
            }
        }


class SessionCommandResult(BaseModel):
    """Result of session command execution"""
    exit_code: int = Field(..., description="Command exit code")
    stdout: str = Field(..., description="Standard output")
    stderr: str = Field(..., description="Standard error")
    execution_time: float = Field(..., description="Execution time in seconds")
    
    class Config:
        json_schema_extra = {
            "example": {
                "exit_code": 0,
                "stdout": "All tests passed!",
                "stderr": "",
                "execution_time": 15.2
            }
        }
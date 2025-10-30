"""
AutoCodit Agent - Session Model

Execution session tracking for containerized runners.
"""

from datetime import datetime, timezone
from enum import Enum
from typing import Optional

from sqlalchemy import Column, String, Text, DateTime, Float, Integer, Boolean, JSON, ForeignKey
from sqlalchemy.dialects.postgresql import UUID, ENUM
from sqlalchemy.orm import relationship
import uuid

from app.models.base import Base


class SessionStatus(str, Enum):
    """Session execution status"""
    INITIALIZING = "initializing"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    TIMEOUT = "timeout"
    CLEANUP = "cleanup"


class Session(Base):
    """Execution session model for container runners"""
    
    __tablename__ = "sessions"
    
    # Primary key
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # Session information
    name = Column(String(255), nullable=True)
    status = Column(ENUM(SessionStatus), default=SessionStatus.INITIALIZING, nullable=False, index=True)
    
    # Container details
    container_id = Column(String(255), nullable=True, index=True)
    container_name = Column(String(255), nullable=True)
    image_name = Column(String(255), nullable=True)
    
    # Runtime configuration
    runner_config = Column(JSON, default=dict, nullable=False)
    environment_vars = Column(JSON, default=dict, nullable=False)
    
    # Resource usage
    memory_limit = Column(String(20), nullable=True)  # e.g., "2GB"
    cpu_limit = Column(String(20), nullable=True)     # e.g., "1000m"
    memory_used = Column(Integer, default=0, nullable=False)  # bytes
    cpu_used = Column(Float, default=0.0, nullable=False)     # percentage
    
    # Network and storage
    network_name = Column(String(255), nullable=True)
    volumes = Column(JSON, default=list, nullable=False)
    
    # Execution details
    exit_code = Column(Integer, nullable=True)
    error_message = Column(Text, nullable=True)
    
    # Logs and output
    log_file_path = Column(String(500), nullable=True)
    output_files = Column(JSON, default=list, nullable=False)
    artifacts = Column(JSON, default=list, nullable=False)
    
    # Health monitoring
    last_heartbeat = Column(DateTime(timezone=True), nullable=True)
    health_check_failures = Column(Integer, default=0, nullable=False)
    
    # Security
    security_violations = Column(JSON, default=list, nullable=False)
    firewall_blocks = Column(Integer, default=0, nullable=False)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc), nullable=False)
    started_at = Column(DateTime(timezone=True), nullable=True)
    finished_at = Column(DateTime(timezone=True), nullable=True)
    
    # Foreign keys
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True, index=True)
    
    # Relationships
    user = relationship("User", back_populates="sessions")
    task = relationship("Task", back_populates="session", uselist=False)
    
    def __repr__(self) -> str:
        return f"<Session(id={self.id}, status={self.status}, container_id={self.container_id})>"
    
    @property
    def duration(self) -> Optional[int]:
        """Get session duration in seconds"""
        if self.started_at and self.finished_at:
            return int((self.finished_at - self.started_at).total_seconds())
        elif self.started_at:
            return int((datetime.now(timezone.utc) - self.started_at).total_seconds())
        return None
    
    @property
    def is_running(self) -> bool:
        """Check if session is currently running"""
        return self.status == SessionStatus.RUNNING
    
    @property
    def is_finished(self) -> bool:
        """Check if session is in a finished state"""
        return self.status in [SessionStatus.COMPLETED, SessionStatus.FAILED, SessionStatus.CANCELLED, SessionStatus.TIMEOUT]
    
    @property
    def memory_usage_mb(self) -> float:
        """Get memory usage in MB"""
        return self.memory_used / (1024 * 1024) if self.memory_used else 0.0
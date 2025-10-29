"""
AutoCodit Agent - Session Models

SQLAlchemy models for execution sessions and related entities.
"""

from datetime import datetime, timezone
from typing import Dict, Any, Optional
from enum import Enum

from sqlalchemy import Column, String, Integer, Float, DateTime, Text, JSON, Boolean, ForeignKey
from sqlalchemy.dialects.postgresql import UUID, ENUM
from sqlalchemy.orm import relationship
import uuid

from app.core.database import Base


class SessionStatus(str, Enum):
    """Session execution status"""
    INITIALIZING = "initializing"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    TIMEOUT = "timeout"


class StepStatus(str, Enum):
    """Individual step status"""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    SKIPPED = "skipped"


class Session(Base):
    """Execution session model"""
    
    __tablename__ = "sessions"
    
    # Primary fields
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    task_id = Column(UUID(as_uuid=True), ForeignKey("tasks.id"), nullable=False, index=True)
    
    # Session details
    status = Column(ENUM(SessionStatus), nullable=False, default=SessionStatus.INITIALIZING, index=True)
    
    # Container and execution details
    container_id = Column(String(64), nullable=True, index=True)  # Docker container ID
    runner_image = Column(String(255), nullable=True)
    runner_config = Column(JSON, default=dict)
    
    # Execution tracking
    started_at = Column(DateTime(timezone=True), nullable=True)
    completed_at = Column(DateTime(timezone=True), nullable=True)
    timeout_at = Column(DateTime(timezone=True), nullable=True)
    
    # Progress and results
    progress = Column(Float, default=0.0)  # 0.0 to 1.0
    current_step = Column(String(100), nullable=True)
    total_steps = Column(Integer, default=0)
    completed_steps = Column(Integer, default=0)
    
    # Resource usage
    max_memory_mb = Column(Integer, default=0)
    cpu_time_seconds = Column(Float, default=0.0)
    network_bytes_sent = Column(Integer, default=0)
    network_bytes_received = Column(Integer, default=0)
    
    # AI and cost tracking
    tokens_used = Column(Integer, default=0)
    ai_requests_count = Column(Integer, default=0)
    estimated_cost = Column(Float, default=0.0)
    
    # Results and artifacts
    output_summary = Column(Text, nullable=True)
    artifacts_urls = Column(JSON, default=list)  # List of artifact URLs
    final_result = Column(JSON, default=dict)
    
    # Error handling
    error_message = Column(Text, nullable=True)
    error_traceback = Column(Text, nullable=True)
    retry_count = Column(Integer, default=0)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))
    
    # Relationships
    task = relationship("Task", back_populates="sessions")
    steps = relationship("SessionStep", back_populates="session", cascade="all, delete-orphan", order_by="SessionStep.step_order")
    logs = relationship("TaskLog", back_populates="session")
    
    def __repr__(self):
        return f"<Session(id={self.id}, task_id={self.task_id}, status={self.status})>"
    
    @property
    def is_active(self) -> bool:
        """Check if session is currently active"""
        return self.status in [SessionStatus.INITIALIZING, SessionStatus.RUNNING]
    
    @property
    def is_finished(self) -> bool:
        """Check if session is finished"""
        return self.status in [SessionStatus.COMPLETED, SessionStatus.FAILED, SessionStatus.CANCELLED, SessionStatus.TIMEOUT]
    
    @property
    def duration_seconds(self) -> Optional[int]:
        """Calculate session duration in seconds"""
        if self.started_at and self.completed_at:
            return int((self.completed_at - self.started_at).total_seconds())
        elif self.started_at:
            return int((datetime.now(timezone.utc) - self.started_at).total_seconds())
        return None
    
    @property
    def success_rate(self) -> float:
        """Calculate step success rate"""
        if self.total_steps == 0:
            return 0.0
        return self.completed_steps / self.total_steps


class SessionStep(Base):
    """Individual step within a session"""
    
    __tablename__ = "session_steps"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    session_id = Column(UUID(as_uuid=True), ForeignKey("sessions.id"), nullable=False, index=True)
    
    # Step details
    step_name = Column(String(100), nullable=False)
    step_type = Column(String(50), nullable=False)  # "tool_call", "ai_request", "file_operation", etc.
    step_order = Column(Integer, nullable=False)
    
    # Status and execution
    status = Column(ENUM(StepStatus), nullable=False, default=StepStatus.PENDING, index=True)
    
    # Step configuration and input
    input_data = Column(JSON, default=dict)
    parameters = Column(JSON, default=dict)
    
    # Execution details
    started_at = Column(DateTime(timezone=True), nullable=True)
    completed_at = Column(DateTime(timezone=True), nullable=True)
    
    # Results and output
    output_data = Column(JSON, default=dict)
    result_summary = Column(Text, nullable=True)
    
    # Resource usage for this step
    tokens_used = Column(Integer, default=0)
    execution_time_ms = Column(Integer, default=0)
    memory_peak_mb = Column(Integer, default=0)
    
    # Error handling
    error_message = Column(Text, nullable=True)
    retry_count = Column(Integer, default=0)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))
    
    # Relationships
    session = relationship("Session", back_populates="steps")
    
    def __repr__(self):
        return f"<SessionStep(id={self.id}, name='{self.step_name}', status={self.status})>"
    
    @property
    def duration_ms(self) -> Optional[int]:
        """Calculate step duration in milliseconds"""
        if self.started_at and self.completed_at:
            return int((self.completed_at - self.started_at).total_seconds() * 1000)
        return None


class SessionArtifact(Base):
    """Artifacts generated during session execution"""
    
    __tablename__ = "session_artifacts"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    session_id = Column(UUID(as_uuid=True), ForeignKey("sessions.id"), nullable=False, index=True)
    step_id = Column(UUID(as_uuid=True), ForeignKey("session_steps.id"), nullable=True, index=True)
    
    # Artifact details
    artifact_type = Column(String(50), nullable=False)  # "screenshot", "file", "log", "diff", etc.
    artifact_name = Column(String(255), nullable=False)
    file_path = Column(String(500), nullable=True)  # Local or S3 path
    file_size_bytes = Column(Integer, nullable=True)
    
    # Content and metadata
    content_type = Column(String(100), nullable=True)  # MIME type
    metadata = Column(JSON, default=dict)
    
    # Storage details
    storage_backend = Column(String(20), default="local")  # "local", "s3", "gcs"
    storage_url = Column(String(500), nullable=True)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)
    
    def __repr__(self):
        return f"<SessionArtifact(id={self.id}, type={self.artifact_type}, name='{self.artifact_name}')>"


class SessionEvent(Base):
    """Real-time events during session execution"""
    
    __tablename__ = "session_events"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    session_id = Column(UUID(as_uuid=True), ForeignKey("sessions.id"), nullable=False, index=True)
    
    # Event details
    event_type = Column(String(50), nullable=False, index=True)  # "step_started", "progress_update", "error", etc.
    event_data = Column(JSON, default=dict)
    message = Column(Text, nullable=True)
    
    # Importance level
    level = Column(String(10), default="info")  # "debug", "info", "warning", "error"
    
    # Timestamp
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)
    
    def __repr__(self):
        return f"<SessionEvent(id={self.id}, type={self.event_type}, level={self.level})>"
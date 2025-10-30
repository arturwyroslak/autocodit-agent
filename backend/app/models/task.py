"""
AutoCodit Agent - Task Model

Task management and execution tracking model.
"""

from datetime import datetime, timezone
from enum import Enum
from typing import Optional

from sqlalchemy import Column, String, Text, DateTime, Float, Integer, Boolean, JSON, ForeignKey
from sqlalchemy.dialects.postgresql import UUID, ENUM
from sqlalchemy.orm import relationship
import uuid

from app.models.base import Base


class TaskStatus(str, Enum):
    """Task execution status"""
    QUEUED = "queued"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    TIMEOUT = "timeout"


class TaskPriority(str, Enum):
    """Task priority levels"""
    LOW = "low"
    NORMAL = "normal"
    HIGH = "high"
    URGENT = "urgent"


class ActionType(str, Enum):
    """Types of actions the agent can perform"""
    PLAN = "plan"
    APPLY = "apply"
    FIX = "fix"
    REVIEW = "review"
    TEST = "test"
    REFACTOR = "refactor"
    DOCUMENT = "document"
    OPTIMIZE = "optimize"


class Task(Base):
    """Task model for coding agent work"""
    
    __tablename__ = "tasks"
    
    # Primary key
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # Basic information
    title = Column(String(500), nullable=False)
    description = Column(Text, nullable=True)
    
    # GitHub context
    repository = Column(String(255), nullable=False, index=True)
    issue_number = Column(Integer, nullable=True, index=True)
    pr_number = Column(Integer, nullable=True, index=True)
    comment_id = Column(String(255), nullable=True)
    branch_name = Column(String(255), nullable=True)
    
    # Task configuration
    action_type = Column(ENUM(ActionType), default=ActionType.PLAN, nullable=False)
    status = Column(ENUM(TaskStatus), default=TaskStatus.QUEUED, nullable=False, index=True)
    priority = Column(ENUM(TaskPriority), default=TaskPriority.NORMAL, nullable=False)
    
    # Progress tracking
    progress = Column(Float, default=0.0, nullable=False)  # 0.0 to 1.0
    
    # Error handling
    error_message = Column(Text, nullable=True)
    retry_count = Column(Integer, default=0, nullable=False)
    max_retries = Column(Integer, default=3, nullable=False)
    
    # GitHub App context
    github_installation_id = Column(Integer, nullable=True)
    triggered_by = Column(String(50), nullable=True)  # issue_assignment, comment_command, api_request
    
    # Agent configuration
    agent_config = Column(JSON, default=dict, nullable=False)
    
    # Resource usage
    tokens_used = Column(Integer, default=0, nullable=False)
    cost = Column(Float, default=0.0, nullable=False)
    
    # Timing
    estimated_duration = Column(Integer, nullable=True)  # seconds
    timeout_minutes = Column(Integer, default=60, nullable=False)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc), nullable=False)
    started_at = Column(DateTime(timezone=True), nullable=True)
    completed_at = Column(DateTime(timezone=True), nullable=True)
    
    # Foreign keys
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True, index=True)
    session_id = Column(UUID(as_uuid=True), ForeignKey("sessions.id"), nullable=True, index=True)
    
    # Relationships
    user = relationship("User", back_populates="tasks")
    session = relationship("Session", back_populates="task", uselist=False)
    
    def __repr__(self) -> str:
        return f"<Task(id={self.id}, title={self.title}, status={self.status})>"
    
    @property
    def duration(self) -> Optional[int]:
        """Get task duration in seconds"""
        if self.started_at and self.completed_at:
            return int((self.completed_at - self.started_at).total_seconds())
        return None
    
    @property
    def is_finished(self) -> bool:
        """Check if task is in a finished state"""
        return self.status in [TaskStatus.COMPLETED, TaskStatus.FAILED, TaskStatus.CANCELLED, TaskStatus.TIMEOUT]
    
    @property
    def can_retry(self) -> bool:
        """Check if task can be retried"""
        return self.status == TaskStatus.FAILED and self.retry_count < self.max_retries
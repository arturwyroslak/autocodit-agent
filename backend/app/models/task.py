"""
AutoCodit Agent - Task Models

SQLAlchemy models for coding tasks and related entities.
"""

from datetime import datetime, timezone
from typing import Dict, Any, Optional
from enum import Enum

from sqlalchemy import Column, String, Integer, Float, DateTime, Text, JSON, Boolean, ForeignKey
from sqlalchemy.dialects.postgresql import UUID, ENUM
from sqlalchemy.orm import relationship
import uuid

from app.core.database import Base


class TaskStatus(str, Enum):
    """Task execution status"""
    QUEUED = "queued"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    PAUSED = "paused"


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
    """Coding task model"""
    
    __tablename__ = "tasks"
    
    # Primary fields
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    title = Column(String(255), nullable=False)
    description = Column(Text)
    
    # GitHub integration
    repository = Column(String(255), nullable=False, index=True)
    issue_number = Column(Integer, nullable=True, index=True)
    pr_number = Column(Integer, nullable=True, index=True)
    comment_id = Column(String(50), nullable=True)
    github_installation_id = Column(Integer, nullable=True)
    
    # Task configuration
    action_type = Column(ENUM(ActionType), nullable=False, default=ActionType.PLAN)
    status = Column(ENUM(TaskStatus), nullable=False, default=TaskStatus.QUEUED, index=True)
    priority = Column(ENUM(TaskPriority), nullable=False, default=TaskPriority.NORMAL)
    
    # Execution details
    progress = Column(Float, default=0.0)  # 0.0 to 1.0
    started_at = Column(DateTime(timezone=True), nullable=True)
    completed_at = Column(DateTime(timezone=True), nullable=True)
    error_message = Column(Text, nullable=True)
    
    # Configuration and metadata
    agent_config = Column(JSON, default=dict)
    triggered_by = Column(String(50), nullable=True)  # "issue_assignment", "comment_command", etc.
    
    # User and organization
    user_id = Column(String(50), nullable=True, index=True)  # GitHub user ID
    organization_id = Column(String(50), nullable=True, index=True)
    
    # Resource usage tracking
    tokens_used = Column(Integer, default=0)
    cost = Column(Float, default=0.0)
    execution_time_seconds = Column(Integer, default=0)
    
    # Results and artifacts
    result_data = Column(JSON, default=dict)
    artifacts_url = Column(String(500), nullable=True)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))
    
    # Relationships
    sessions = relationship("Session", back_populates="task", cascade="all, delete-orphan")
    logs = relationship("TaskLog", back_populates="task", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<Task(id={self.id}, title='{self.title}', status={self.status})>"
    
    @property
    def is_active(self) -> bool:
        """Check if task is currently active"""
        return self.status in [TaskStatus.QUEUED, TaskStatus.RUNNING, TaskStatus.PAUSED]
    
    @property
    def is_finished(self) -> bool:
        """Check if task is finished (completed, failed, or cancelled)"""
        return self.status in [TaskStatus.COMPLETED, TaskStatus.FAILED, TaskStatus.CANCELLED]
    
    @property
    def duration_seconds(self) -> Optional[int]:
        """Calculate task duration in seconds"""
        if self.started_at and self.completed_at:
            return int((self.completed_at - self.started_at).total_seconds())
        elif self.started_at:
            return int((datetime.now(timezone.utc) - self.started_at).total_seconds())
        return None


class TaskLog(Base):
    """Task execution logs"""
    
    __tablename__ = "task_logs"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    task_id = Column(UUID(as_uuid=True), ForeignKey("tasks.id"), nullable=False, index=True)
    session_id = Column(UUID(as_uuid=True), ForeignKey("sessions.id"), nullable=True, index=True)
    
    # Log entry details
    level = Column(String(10), nullable=False, index=True)  # DEBUG, INFO, WARNING, ERROR
    message = Column(Text, nullable=False)
    component = Column(String(50), nullable=True)  # "agent", "mcp", "tool", "ai"
    
    # Structured log data
    data = Column(JSON, default=dict)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)
    
    # Relationships
    task = relationship("Task", back_populates="logs")
    session = relationship("Session", back_populates="logs")
    
    def __repr__(self):
        return f"<TaskLog(id={self.id}, level={self.level}, message='{self.message[:50]}...')>"


class TaskMetric(Base):
    """Task performance metrics"""
    
    __tablename__ = "task_metrics"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    task_id = Column(UUID(as_uuid=True), ForeignKey("tasks.id"), nullable=False, index=True)
    
    # Metric details
    metric_name = Column(String(100), nullable=False, index=True)
    metric_value = Column(Float, nullable=False)
    metric_unit = Column(String(20), nullable=True)  # "seconds", "tokens", "bytes", etc.
    
    # Metadata
    tags = Column(JSON, default=dict)
    
    # Timestamp
    recorded_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)
    
    def __repr__(self):
        return f"<TaskMetric(task_id={self.task_id}, name={self.metric_name}, value={self.metric_value})>"


class AgentProfile(Base):
    """Agent configuration profiles"""
    
    __tablename__ = "agent_profiles"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(100), nullable=False, unique=True, index=True)
    description = Column(Text, nullable=True)
    
    # AI Model configuration
    model_config = Column(JSON, nullable=False, default=dict)
    
    # System prompt and behavior
    system_prompt = Column(Text, nullable=True)
    behavior_config = Column(JSON, default=dict)
    
    # Tool and MCP configuration
    tools_config = Column(JSON, default=dict)
    mcp_servers = Column(JSON, default=list)
    
    # Security and resource limits
    security_config = Column(JSON, default=dict)
    resource_limits = Column(JSON, default=dict)
    
    # Usage and permissions
    is_public = Column(Boolean, default=False)
    created_by = Column(String(50), nullable=True)  # User ID who created this profile
    organization_id = Column(String(50), nullable=True, index=True)
    
    # Usage statistics
    usage_count = Column(Integer, default=0)
    last_used_at = Column(DateTime(timezone=True), nullable=True)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))
    
    def __repr__(self):
        return f"<AgentProfile(id={self.id}, name='{self.name}')>"
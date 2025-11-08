"""
AutoCodit Agent - Repository Model

Database model for GitHub repositories.
"""

from sqlalchemy import Column, String, Boolean, Integer, JSON, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime

from .base import Base, TimestampMixin


class Repository(Base, TimestampMixin):
    """Repository model for storing GitHub repository information"""
    
    __tablename__ = "repositories"
    
    id = Column(String, primary_key=True)
    
    # GitHub information
    github_id = Column(Integer, unique=True, nullable=False, index=True)
    full_name = Column(String, unique=True, nullable=False, index=True)
    name = Column(String, nullable=False)
    owner = Column(String, nullable=False)
    
    # Repository details
    description = Column(String, nullable=True)
    html_url = Column(String, nullable=False)
    clone_url = Column(String, nullable=False)
    ssh_url = Column(String, nullable=False)
    default_branch = Column(String, default="main", nullable=False)
    
    # Repository status
    private = Column(Boolean, default=False, nullable=False)
    archived = Column(Boolean, default=False, nullable=False)
    disabled = Column(Boolean, default=False, nullable=False)
    
    # Agent configuration
    agent_enabled = Column(Boolean, default=False, nullable=False)
    agent_config_id = Column(String, ForeignKey("agent_configs.id"), nullable=True)
    
    # Installation information
    installation_id = Column(Integer, nullable=True, index=True)
    
    # Statistics
    stars_count = Column(Integer, default=0)
    forks_count = Column(Integer, default=0)
    open_issues_count = Column(Integer, default=0)
    
    # Additional metadata
    language = Column(String, nullable=True)
    topics = Column(JSON, default=list)
    metadata = Column(JSON, default=dict)
    
    # Relationships
    agent_config = relationship("AgentConfig", back_populates="repositories")
    tasks = relationship("Task", back_populates="repository", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<Repository {self.full_name}>"
    
    def to_dict(self):
        """Convert repository to dictionary"""
        return {
            "id": self.id,
            "github_id": self.github_id,
            "full_name": self.full_name,
            "name": self.name,
            "owner": self.owner,
            "description": self.description,
            "html_url": self.html_url,
            "default_branch": self.default_branch,
            "private": self.private,
            "archived": self.archived,
            "disabled": self.disabled,
            "agent_enabled": self.agent_enabled,
            "installation_id": self.installation_id,
            "stars_count": self.stars_count,
            "forks_count": self.forks_count,
            "open_issues_count": self.open_issues_count,
            "language": self.language,
            "topics": self.topics,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }

from sqlalchemy import String, Text, JSON, Boolean, Float, Integer, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from typing import Optional, Dict, Any, List
from .base import Base


class AgentConfig(Base):
    """Agent configuration profiles for different coding tasks"""
    
    # Basic information
    name: Mapped[str] = mapped_column(String(255))
    description: Mapped[Optional[str]] = mapped_column(Text)
    
    # AI model configuration
    system_prompt: Mapped[str] = mapped_column(Text)
    model_primary: Mapped[str] = mapped_column(String(100), default="gpt-4-turbo")
    model_fallback: Mapped[Optional[str]] = mapped_column(String(100))
    
    # Generation parameters
    temperature: Mapped[float] = mapped_column(Float, default=0.1)
    max_tokens: Mapped[int] = mapped_column(Integer, default=4096)
    
    # Tools and capabilities
    enabled_tools: Mapped[List[str]] = mapped_column(JSON, default=list)
    mcp_servers: Mapped[List[Dict[str, Any]]] = mapped_column(JSON, default=list)
    
    # Execution settings
    max_iterations: Mapped[int] = mapped_column(Integer, default=20)
    timeout_minutes: Mapped[int] = mapped_column(Integer, default=60)
    auto_commit: Mapped[bool] = mapped_column(Boolean, default=False)
    
    # Metadata
    is_default: Mapped[bool] = mapped_column(Boolean, default=False)
    is_public: Mapped[bool] = mapped_column(Boolean, default=False)
    
    # Owner relationship
    user_id: Mapped[Optional[str]] = mapped_column(ForeignKey("user.id"))
    user: Mapped[Optional["User"]] = relationship("User", back_populates="agent_configs")
    
    def __repr__(self) -> str:
        return f"<AgentConfig(name='{self.name}', model='{self.model_primary}')>"
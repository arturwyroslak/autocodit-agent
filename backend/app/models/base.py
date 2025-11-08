"""
AutoCodit Agent - Base Model

Base SQLAlchemy model with common fields and utilities.
"""

from datetime import datetime, timezone
from typing import Any

from sqlalchemy import Column, DateTime, String, Text
from sqlalchemy.ext.declarative import declared_attr
from sqlalchemy.orm import as_declarative, Mapped, mapped_column


@as_declarative()
class Base:
    """Base class for all database models"""
    
    id: Any
    __name__: str
    
    # Generate __tablename__ automatically
    @declared_attr
    def __tablename__(cls) -> str:
        return cls.__name__.lower()
    
    def dict(self) -> dict:
        """Convert model to dictionary"""
        return {c.name: getattr(self, c.name) for c in self.__table__.columns}
    
    def __repr__(self) -> str:
        return f"<{self.__class__.__name__}(id={self.id})>"


class TimestampMixin:
    """Mixin for adding created_at and updated_at timestamps"""
    
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False
    )
    
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False
    )

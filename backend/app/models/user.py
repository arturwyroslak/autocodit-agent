"""
AutoCodit Agent - User Models

SQLAlchemy models for users, organizations, and access control.
"""

from datetime import datetime, timezone
from typing import Dict, Any, Optional
from enum import Enum

from sqlalchemy import Column, String, Integer, DateTime, Text, JSON, Boolean, ForeignKey, Table
from sqlalchemy.dialects.postgresql import UUID, ENUM
from sqlalchemy.orm import relationship
import uuid

from app.core.database import Base


class UserRole(str, Enum):
    """User roles within an organization"""
    OWNER = "owner"
    ADMIN = "admin"
    MEMBER = "member"
    VIEWER = "viewer"


class SubscriptionTier(str, Enum):
    """Subscription tiers"""
    FREE = "free"
    STARTER = "starter"
    PROFESSIONAL = "professional"
    ENTERPRISE = "enterprise"


# Association table for user-organization relationships
user_organization_association = Table(
    'user_organizations',
    Base.metadata,
    Column('user_id', UUID(as_uuid=True), ForeignKey('users.id'), primary_key=True),
    Column('organization_id', UUID(as_uuid=True), ForeignKey('organizations.id'), primary_key=True),
    Column('role', ENUM(UserRole), nullable=False, default=UserRole.MEMBER),
    Column('joined_at', DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
)


class User(Base):
    """User account model"""
    
    __tablename__ = "users"
    
    # Primary fields
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # GitHub integration
    github_id = Column(String(20), unique=True, nullable=False, index=True)
    github_login = Column(String(100), nullable=False, index=True)
    github_name = Column(String(200), nullable=True)
    github_email = Column(String(255), nullable=True)
    github_avatar_url = Column(String(500), nullable=True)
    
    # Account status
    is_active = Column(Boolean, default=True, nullable=False)
    is_verified = Column(Boolean, default=False, nullable=False)
    
    # Subscription and billing
    subscription_tier = Column(ENUM(SubscriptionTier), default=SubscriptionTier.FREE, nullable=False)
    subscription_expires_at = Column(DateTime(timezone=True), nullable=True)
    
    # Usage tracking
    tasks_created = Column(Integer, default=0)
    tokens_used_monthly = Column(Integer, default=0)
    last_task_created_at = Column(DateTime(timezone=True), nullable=True)
    
    # Preferences and settings
    preferences = Column(JSON, default=dict)
    notification_settings = Column(JSON, default=dict)
    
    # Access tokens (encrypted)
    github_access_token = Column(Text, nullable=True)  # Encrypted
    api_keys = Column(JSON, default=list)  # List of API keys
    
    # Last activity tracking
    last_login_at = Column(DateTime(timezone=True), nullable=True)
    last_active_at = Column(DateTime(timezone=True), nullable=True)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))
    
    # Relationships
    organizations = relationship(
        "Organization",
        secondary=user_organization_association,
        back_populates="users"
    )
    
    def __repr__(self):
        return f"<User(id={self.id}, github_login='{self.github_login}')>"
    
    @property
    def is_premium(self) -> bool:
        """Check if user has premium subscription"""
        return self.subscription_tier in [SubscriptionTier.PROFESSIONAL, SubscriptionTier.ENTERPRISE]
    
    @property
    def monthly_task_limit(self) -> int:
        """Get monthly task limit based on subscription"""
        limits = {
            SubscriptionTier.FREE: 10,
            SubscriptionTier.STARTER: 100,
            SubscriptionTier.PROFESSIONAL: 1000,
            SubscriptionTier.ENTERPRISE: -1  # Unlimited
        }
        return limits.get(self.subscription_tier, 10)
    
    @property
    def monthly_token_limit(self) -> int:
        """Get monthly token limit based on subscription"""
        limits = {
            SubscriptionTier.FREE: 50000,
            SubscriptionTier.STARTER: 500000,
            SubscriptionTier.PROFESSIONAL: 2000000,
            SubscriptionTier.ENTERPRISE: -1  # Unlimited
        }
        return limits.get(self.subscription_tier, 50000)


class Organization(Base):
    """Organization model"""
    
    __tablename__ = "organizations"
    
    # Primary fields
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # Organization details
    name = Column(String(200), nullable=False)
    slug = Column(String(100), unique=True, nullable=False, index=True)
    description = Column(Text, nullable=True)
    
    # GitHub integration
    github_id = Column(String(20), unique=True, nullable=True, index=True)
    github_login = Column(String(100), nullable=True, index=True)
    github_installation_id = Column(Integer, nullable=True, index=True)
    
    # Subscription and billing
    subscription_tier = Column(ENUM(SubscriptionTier), default=SubscriptionTier.FREE, nullable=False)
    subscription_expires_at = Column(DateTime(timezone=True), nullable=True)
    billing_email = Column(String(255), nullable=True)
    
    # Settings and configuration
    settings = Column(JSON, default=dict)
    agent_profiles = Column(JSON, default=list)  # List of custom agent profile IDs
    
    # Usage tracking
    total_tasks = Column(Integer, default=0)
    total_tokens_used = Column(Integer, default=0)
    monthly_tasks = Column(Integer, default=0)
    monthly_tokens_used = Column(Integer, default=0)
    
    # Status
    is_active = Column(Boolean, default=True, nullable=False)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))
    
    # Relationships
    users = relationship(
        "User",
        secondary=user_organization_association,
        back_populates="organizations"
    )
    
    def __repr__(self):
        return f"<Organization(id={self.id}, name='{self.name}', slug='{self.slug}')>"
    
    @property
    def is_premium(self) -> bool:
        """Check if organization has premium subscription"""
        return self.subscription_tier in [SubscriptionTier.PROFESSIONAL, SubscriptionTier.ENTERPRISE]


class APIKey(Base):
    """API keys for programmatic access"""
    
    __tablename__ = "api_keys"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # Key details
    name = Column(String(100), nullable=False)
    key_hash = Column(String(128), nullable=False, unique=True, index=True)  # Hashed key
    key_prefix = Column(String(10), nullable=False)  # First few chars for identification
    
    # Owner
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False, index=True)
    organization_id = Column(UUID(as_uuid=True), ForeignKey("organizations.id"), nullable=True, index=True)
    
    # Permissions and scope
    scopes = Column(JSON, default=list)  # List of permissions
    
    # Usage tracking
    last_used_at = Column(DateTime(timezone=True), nullable=True)
    usage_count = Column(Integer, default=0)
    
    # Status and expiry
    is_active = Column(Boolean, default=True, nullable=False)
    expires_at = Column(DateTime(timezone=True), nullable=True)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)
    
    def __repr__(self):
        return f"<APIKey(id={self.id}, name='{self.name}', prefix='{self.key_prefix}')>"
    
    @property
    def is_expired(self) -> bool:
        """Check if API key is expired"""
        if self.expires_at:
            return datetime.now(timezone.utc) > self.expires_at
        return False


class UserSession(Base):
    """User login sessions"""
    
    __tablename__ = "user_sessions"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False, index=True)
    
    # Session details
    session_token = Column(String(128), nullable=False, unique=True, index=True)
    
    # Client information
    ip_address = Column(String(45), nullable=True)  # IPv6 compatible
    user_agent = Column(Text, nullable=True)
    
    # Status and expiry
    is_active = Column(Boolean, default=True, nullable=False)
    expires_at = Column(DateTime(timezone=True), nullable=False)
    
    # Activity tracking
    last_activity_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)
    
    def __repr__(self):
        return f"<UserSession(id={self.id}, user_id={self.user_id})>"
    
    @property
    def is_expired(self) -> bool:
        """Check if session is expired"""
        return datetime.now(timezone.utc) > self.expires_at
"""
AutoCodit Agent - User Schemas

Pydantic models for user-related API requests and responses.
"""

from datetime import datetime
from typing import Dict, Any, List, Optional
from uuid import UUID

from pydantic import BaseModel, Field

from app.models.user import SubscriptionTier, UserRole


class UserResponse(BaseModel):
    """User profile response"""
    id: UUID
    github_id: str
    github_login: str
    github_name: Optional[str]
    github_email: Optional[str]
    github_avatar_url: Optional[str]
    
    is_active: bool
    is_verified: bool
    
    subscription_tier: SubscriptionTier
    subscription_expires_at: Optional[datetime]
    
    tasks_created: int
    tokens_used_monthly: int
    last_task_created_at: Optional[datetime]
    
    preferences: Dict[str, Any]
    notification_settings: Dict[str, Any]
    
    last_login_at: Optional[datetime]
    last_active_at: Optional[datetime]
    
    created_at: datetime
    updated_at: datetime
    
    # Computed properties
    is_premium: bool
    monthly_task_limit: int
    monthly_token_limit: int
    
    class Config:
        from_attributes = True
        json_schema_extra = {
            "example": {
                "id": "123e4567-e89b-12d3-a456-426614174000",
                "github_id": "12345",
                "github_login": "johndoe",
                "github_name": "John Doe",
                "github_email": "john@example.com",
                "subscription_tier": "professional",
                "tasks_created": 25,
                "tokens_used_monthly": 15000,
                "is_premium": True,
                "monthly_task_limit": 1000,
                "monthly_token_limit": 2000000,
                "created_at": "2025-10-01T10:00:00Z"
            }
        }


class UpdateUserPreferences(BaseModel):
    """Update user preferences request"""
    preferences: Optional[Dict[str, Any]] = None
    notification_settings: Optional[Dict[str, Any]] = None
    
    class Config:
        json_schema_extra = {
            "example": {
                "preferences": {
                    "theme": "dark",
                    "default_model": "gpt-4-turbo",
                    "auto_approve_safe_changes": True
                },
                "notification_settings": {
                    "task_completed": True,
                    "task_failed": True,
                    "weekly_summary": False
                }
            }
        }


class OrganizationResponse(BaseModel):
    """Organization response"""
    id: UUID
    name: str
    slug: str
    description: Optional[str]
    
    github_id: Optional[str]
    github_login: Optional[str]
    github_installation_id: Optional[int]
    
    subscription_tier: SubscriptionTier
    subscription_expires_at: Optional[datetime]
    
    total_tasks: int
    total_tokens_used: int
    monthly_tasks: int
    monthly_tokens_used: int
    
    is_active: bool
    
    created_at: datetime
    updated_at: datetime
    
    # User's role in this organization
    user_role: Optional[UserRole] = None
    
    class Config:
        from_attributes = True
        json_schema_extra = {
            "example": {
                "id": "123e4567-e89b-12d3-a456-426614174000",
                "name": "Acme Corporation",
                "slug": "acme-corp",
                "subscription_tier": "enterprise",
                "total_tasks": 500,
                "user_role": "admin",
                "created_at": "2025-10-01T10:00:00Z"
            }
        }


class APIKeyResponse(BaseModel):
    """API key response (without revealing the actual key)"""
    id: UUID
    name: str
    key_prefix: str
    scopes: List[str]
    last_used_at: Optional[datetime]
    usage_count: int
    is_active: bool
    expires_at: Optional[datetime]
    created_at: datetime
    
    class Config:
        from_attributes = True
        json_schema_extra = {
            "example": {
                "id": "123e4567-e89b-12d3-a456-426614174000",
                "name": "Production API Key",
                "key_prefix": "ac_prod_",
                "scopes": ["tasks:read", "tasks:write", "sessions:read"],
                "last_used_at": "2025-10-29T15:30:00Z",
                "usage_count": 142,
                "is_active": True,
                "expires_at": null,
                "created_at": "2025-10-01T10:00:00Z"
            }
        }


class CreateAPIKeyRequest(BaseModel):
    """Create API key request"""
    name: str = Field(..., min_length=1, max_length=100)
    scopes: List[str] = Field(..., min_items=1)
    expires_in_days: Optional[int] = Field(None, ge=1, le=365)
    
    class Config:
        json_schema_extra = {
            "example": {
                "name": "Production API Key",
                "scopes": ["tasks:read", "tasks:write", "sessions:read"],
                "expires_in_days": 90
            }
        }


class UsageStatsResponse(BaseModel):
    """Usage statistics response"""
    subscription: Dict[str, Any]
    limits: Dict[str, int]
    current_usage: Dict[str, Any]
    remaining: Dict[str, Any]
    
    class Config:
        json_schema_extra = {
            "example": {
                "subscription": {
                    "tier": "professional",
                    "expires_at": "2025-11-01T00:00:00Z",
                    "is_premium": True
                },
                "limits": {
                    "monthly_tasks": 1000,
                    "monthly_tokens": 2000000
                },
                "current_usage": {
                    "tasks_created": 25,
                    "tokens_used_monthly": 15000,
                    "last_task_created_at": "2025-10-29T14:30:00Z"
                },
                "remaining": {
                    "tasks": 975,
                    "tokens": 1985000
                }
            }
        }


class ActivityResponse(BaseModel):
    """User activity response"""
    recent_tasks: List[Dict[str, Any]]
    recent_logins: List[Dict[str, Any]]
    api_usage: Dict[str, int]
    
    class Config:
        json_schema_extra = {
            "example": {
                "recent_tasks": [
                    {
                        "id": "123e4567-e89b-12d3-a456-426614174000",
                        "title": "Fix authentication bug",
                        "status": "completed",
                        "created_at": "2025-10-29T10:00:00Z"
                    }
                ],
                "recent_logins": [
                    {
                        "timestamp": "2025-10-29T09:00:00Z",
                        "ip_address": "192.168.1.100",
                        "user_agent": "Mozilla/5.0..."
                    }
                ],
                "api_usage": {
                    "last_7_days": 15,
                    "last_30_days": 89
                }
            }
        }
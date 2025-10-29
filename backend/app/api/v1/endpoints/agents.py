"""
AutoCodit Agent - Agents API Endpoints

RESTful API endpoints for agent profiles and configuration.
"""

from typing import List, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.schemas.task import AgentProfileResponse
from app.core.auth import get_current_user
from app.models.user import User

router = APIRouter()


@router.get("/profiles", response_model=List[AgentProfileResponse])
async def list_agent_profiles(
    public_only: bool = Query(False, description="Show only public profiles"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """List available agent profiles"""
    
    # TODO: Implement profile listing from database
    # Should include:
    # - User's own profiles
    # - Public profiles
    # - Organization profiles (if user is member)
    
    return []


@router.get("/profiles/{profile_id}", response_model=AgentProfileResponse)
async def get_agent_profile(
    profile_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get agent profile by ID"""
    
    # TODO: Implement profile retrieval with access control
    raise HTTPException(status_code=404, detail="Profile not found")


@router.post("/profiles", response_model=AgentProfileResponse, status_code=201)
async def create_agent_profile(
    profile_data: dict,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Create new agent profile"""
    
    # TODO: Implement profile creation
    # Validate configuration
    # Save to database
    # Return created profile
    
    raise HTTPException(status_code=501, detail="Not implemented")


@router.patch("/profiles/{profile_id}", response_model=AgentProfileResponse)
async def update_agent_profile(
    profile_id: UUID,
    update_data: dict,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Update agent profile"""
    
    # TODO: Implement profile updates with ownership validation
    raise HTTPException(status_code=501, detail="Not implemented")


@router.delete("/profiles/{profile_id}", status_code=204)
async def delete_agent_profile(
    profile_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Delete agent profile"""
    
    # TODO: Implement profile deletion with ownership validation
    # Check if profile is being used by any tasks
    raise HTTPException(status_code=501, detail="Not implemented")


@router.get("/capabilities")
async def get_agent_capabilities(
    current_user: User = Depends(get_current_user)
):
    """Get available agent capabilities and tools"""
    
    return {
        "models": {
            "openai": ["gpt-4-turbo", "gpt-4", "gpt-3.5-turbo"],
            "anthropic": ["claude-3-opus", "claude-3-sonnet", "claude-3-haiku"],
            "local": ["codellama", "deepseek-coder"]
        },
        "tools": {
            "builtin": ["file_operations", "git_operations", "test_runner"],
            "mcp_servers": ["github", "playwright", "sentry", "notion"]
        },
        "languages": [
            "python", "javascript", "typescript", "java", "go", 
            "rust", "c++", "c#", "php", "ruby", "swift", "kotlin"
        ],
        "frameworks": {
            "web": ["react", "vue", "angular", "svelte", "next.js"],
            "backend": ["fastapi", "django", "flask", "express", "spring"],
            "mobile": ["react-native", "flutter", "swift-ui", "compose"],
            "testing": ["jest", "pytest", "junit", "cypress", "playwright"]
        },
        "security_modes": ["permissive", "moderate", "strict"],
        "resource_limits": {
            "memory": ["1Gi", "2Gi", "4Gi", "8Gi"],
            "cpu": ["500m", "1000m", "2000m"],
            "timeout": ["30m", "60m", "120m", "240m"]
        }
    }


@router.get("/templates")
async def get_agent_templates(
    category: Optional[str] = Query(None, description="Filter by category"),
    current_user: User = Depends(get_current_user)
):
    """Get pre-built agent profile templates"""
    
    templates = {
        "frontend": {
            "name": "Frontend Specialist",
            "description": "Expert in React, TypeScript, and modern frontend practices",
            "model_config": {
                "primary_model": "gpt-4-turbo",
                "temperature": 0.2,
                "max_tokens": 4000
            },
            "system_prompt": "You are a frontend development expert...",
            "tools_config": {
                "enabled_tools": ["npm", "playwright", "jest"]
            },
            "security_config": {
                "firewall_mode": "strict",
                "allowed_domains": ["npmjs.org", "unpkg.com"]
            }
        },
        "backend": {
            "name": "Backend Developer",
            "description": "Expert in API development, databases, and server architecture",
            "model_config": {
                "primary_model": "gpt-4-turbo",
                "temperature": 0.1,
                "max_tokens": 4000
            },
            "system_prompt": "You are a backend development expert...",
            "tools_config": {
                "enabled_tools": ["docker", "database", "api_testing"]
            }
        },
        "devops": {
            "name": "DevOps Engineer",
            "description": "Expert in CI/CD, infrastructure, and deployment",
            "model_config": {
                "primary_model": "gpt-4-turbo",
                "temperature": 0.1,
                "max_tokens": 4000
            },
            "system_prompt": "You are a DevOps expert...",
            "tools_config": {
                "enabled_tools": ["kubernetes", "terraform", "ansible"]
            }
        },
        "security": {
            "name": "Security Specialist",
            "description": "Expert in security auditing and vulnerability assessment",
            "model_config": {
                "primary_model": "gpt-4-turbo",
                "temperature": 0.05,  # Very conservative
                "max_tokens": 4000
            },
            "system_prompt": "You are a cybersecurity expert...",
            "tools_config": {
                "enabled_tools": ["security_scanner", "code_analysis"]
            },
            "security_config": {
                "firewall_mode": "strict",
                "content_filter": "strict"
            }
        },
        "documentation": {
            "name": "Documentation Writer",
            "description": "Expert in technical writing and documentation",
            "model_config": {
                "primary_model": "gpt-4-turbo",
                "temperature": 0.3,  # More creative for writing
                "max_tokens": 4000
            },
            "system_prompt": "You are a technical documentation expert...",
            "tools_config": {
                "enabled_tools": ["markdown", "diagram_generation"]
            }
        }
    }
    
    if category:
        return {category: templates.get(category)}
    
    return templates


@router.post("/validate-config")
async def validate_agent_config(
    config: dict,
    current_user: User = Depends(get_current_user)
):
    """Validate agent configuration before saving"""
    
    errors = []
    warnings = []
    
    # Validate model configuration
    model_config = config.get("model_config", {})
    if not model_config.get("primary_model"):
        errors.append("Primary model is required")
    
    # Validate temperature
    temperature = model_config.get("temperature", 0.1)
    if not 0 <= temperature <= 2:
        errors.append("Temperature must be between 0 and 2")
    
    # Validate system prompt
    system_prompt = config.get("system_prompt", "")
    if len(system_prompt) > 10000:
        errors.append("System prompt is too long (max 10,000 characters)")
    
    # Validate resource limits
    resource_limits = config.get("resource_limits", {})
    memory = resource_limits.get("memory", "2Gi")
    if memory not in ["1Gi", "2Gi", "4Gi", "8Gi"]:
        warnings.append("Unusual memory limit specified")
    
    # Validate tools configuration
    tools_config = config.get("tools_config", {})
    enabled_tools = tools_config.get("enabled_tools", [])
    
    # Check for potentially dangerous tool combinations
    if "shell_access" in enabled_tools and "network_access" in enabled_tools:
        warnings.append("Shell and network access combination may pose security risks")
    
    return {
        "valid": len(errors) == 0,
        "errors": errors,
        "warnings": warnings,
        "recommendations": [
            "Consider enabling structured logging for better debugging",
            "Add resource limits to prevent runaway executions",
            "Enable firewall rules for security"
        ]
    }
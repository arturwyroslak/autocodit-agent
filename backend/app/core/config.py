"""
AutoCodit Agent - Configuration Management

Centralized configuration using Pydantic Settings for type safety
and environment variable validation.
"""

from functools import lru_cache
from typing import List, Optional, Union

from pydantic import Field, field_validator, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables"""
    
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
    )
    
    # API Configuration
    API_HOST: str = Field(default="0.0.0.0", description="API host")
    API_PORT: int = Field(default=8000, description="API port")
    API_BASE_URL: str = Field(default="http://localhost:8000", description="Base API URL")
    FRONTEND_URL: str = Field(default="http://localhost:3000", description="Frontend URL")
    
    # Security - Now with defaults for development
    JWT_SECRET: str = Field(default="development-jwt-secret-change-in-production", description="JWT secret key")
    ENCRYPTION_KEY: str = Field(default="development-encryption-key-32ch", description="Encryption key for sensitive data")
    WEBHOOK_VERIFICATION_TOKEN: str = Field(default="development-webhook-token", description="Webhook verification token")
    
    # GitHub App Configuration - Now with defaults
    GITHUB_APP_ID: Union[int, str] = Field(default=0, description="GitHub App ID")
    GITHUB_PRIVATE_KEY: str = Field(default="", description="GitHub App private key")
    GITHUB_WEBHOOK_SECRET: str = Field(default="development-webhook-secret", description="GitHub webhook secret")
    GITHUB_BOT_LOGIN: str = Field(default="autocodit-bot", description="GitHub bot username")
    GITHUB_API_URL: str = Field(default="https://api.github.com", description="GitHub API URL")
    
    # Database
    DATABASE_URL: str = Field(default="postgresql://autocodit:password@localhost:5432/autocodit_agent", description="PostgreSQL database URL")
    REDIS_URL: str = Field(default="redis://localhost:6379/0", description="Redis URL")
    
    # Task Queue
    CELERY_BROKER_URL: str = Field(default="redis://localhost:6379/1", description="Celery broker URL")
    CELERY_RESULT_BACKEND: Optional[str] = Field(default="redis://localhost:6379/1", description="Celery result backend")
    
    # AI Models
    OPENAI_API_KEY: Optional[str] = Field(default=None, description="OpenAI API key")
    OPENAI_MODEL_PRIMARY: str = Field(default="gpt-4-turbo-preview", description="Primary OpenAI model")
    OPENAI_MODEL_FALLBACK: str = Field(default="gpt-3.5-turbo-16k", description="Fallback OpenAI model")
    OPENAI_MAX_TOKENS: int = Field(default=4096, description="Max tokens for OpenAI")
    OPENAI_TEMPERATURE: float = Field(default=0.1, description="Temperature for OpenAI")
    
    ANTHROPIC_API_KEY: Optional[str] = Field(default=None, description="Anthropic API key")
    ANTHROPIC_MODEL_PRIMARY: str = Field(default="claude-3-sonnet-20240229", description="Primary Anthropic model")
    ANTHROPIC_MAX_TOKENS: int = Field(default=4096, description="Max tokens for Anthropic")
    ANTHROPIC_TEMPERATURE: float = Field(default=0.1, description="Temperature for Anthropic")
    
    # Local LLM (optional)
    OLLAMA_BASE_URL: Optional[str] = Field(default=None, description="Ollama base URL")
    OLLAMA_MODEL: str = Field(default="codellama:34b", description="Ollama model")
    
    # Runner Configuration
    RUNNER_MAX_CONCURRENT: int = Field(default=10, description="Max concurrent runners")
    RUNNER_DEFAULT_TIMEOUT: int = Field(default=3600, description="Default runner timeout (seconds)")
    RUNNER_DEFAULT_MEMORY: str = Field(default="2Gi", description="Default runner memory limit")
    RUNNER_DEFAULT_CPU: str = Field(default="1000m", description="Default runner CPU limit")
    RUNNER_NETWORK_NAME: str = Field(default="autocodit-runners", description="Runner network name")
    
    # Container Configuration
    DOCKER_HOST: str = Field(default="unix:///var/run/docker.sock", description="Docker host")
    DOCKER_REGISTRY: str = Field(default="autocodit", description="Docker registry")
    DOCKER_IMAGE_TAG: str = Field(default="latest", description="Docker image tag")
    CONTAINER_ISOLATION_MODE: str = Field(default="docker", description="Container isolation mode")
    
    # Security & Firewall
    FIREWALL_ENABLED: bool = Field(default=True, description="Enable firewall")
    FIREWALL_MODE: str = Field(default="strict", description="Firewall mode")
    FIREWALL_LOG_BLOCKED: bool = Field(default=True, description="Log blocked requests")
    FIREWALL_ALLOWLIST_DOMAINS: Union[str, List[str]] = Field(
        default="github.com,npmjs.org,pypi.org,docker.io",
        description="Comma-separated list of allowed domains"
    )
    
    # Content Filtering
    CONTENT_FILTER_ENABLED: bool = Field(default=True, description="Enable content filtering")
    CONTENT_FILTER_MODE: str = Field(default="strict", description="Content filter mode")
    HIDDEN_CHAR_FILTER: bool = Field(default=True, description="Filter hidden characters")
    
    # Monitoring & Observability
    LOG_LEVEL: str = Field(default="INFO", description="Log level")
    STRUCTURED_LOGGING: bool = Field(default=True, description="Enable structured logging")
    METRICS_ENABLED: bool = Field(default=True, description="Enable metrics")
    METRICS_PORT: int = Field(default=9090, description="Metrics port")
    TRACING_ENABLED: bool = Field(default=True, description="Enable tracing")
    JAEGER_ENDPOINT: Optional[str] = Field(default=None, description="Jaeger endpoint")
    
    # Session Management
    SESSION_TIMEOUT_MINUTES: int = Field(default=60, description="Session timeout in minutes")
    SESSION_CLEANUP_INTERVAL: int = Field(default=300, description="Session cleanup interval (seconds)")
    SESSION_MAX_CONCURRENT_PER_USER: int = Field(default=5, description="Max concurrent sessions per user")
    
    # Rate Limiting
    RATE_LIMIT_ENABLED: bool = Field(default=True, description="Enable rate limiting")
    RATE_LIMIT_REQUESTS_PER_MINUTE: int = Field(default=60, description="Requests per minute")
    RATE_LIMIT_BURST_SIZE: int = Field(default=10, description="Rate limit burst size")
    
    # Cost Management
    COST_TRACKING_ENABLED: bool = Field(default=True, description="Enable cost tracking")
    TOKEN_BUDGET_PER_TASK: int = Field(default=50000, description="Token budget per task")
    DAILY_TOKEN_LIMIT: int = Field(default=1000000, description="Daily token limit")
    COST_ALERT_THRESHOLD: float = Field(default=100.0, description="Cost alert threshold")
    
    # Development Settings
    DEBUG: bool = Field(default=False, description="Debug mode")
    HOT_RELOAD: bool = Field(default=False, description="Hot reload")
    DEV_MODE: bool = Field(default=False, description="Development mode")
    PROFILING_ENABLED: bool = Field(default=False, description="Enable profiling")
    
    # CORS and Security
    CORS_ORIGINS: List[str] = Field(default=["*"], description="CORS allowed origins")
    ALLOWED_HOSTS: List[str] = Field(default=["*"], description="Allowed hosts")
    
    @field_validator("GITHUB_APP_ID", mode="before")
    @classmethod
    def parse_github_app_id(cls, v):
        """Parse GITHUB_APP_ID, handling empty strings"""
        if v == "" or v is None:
            return 0
        try:
            return int(v)
        except (ValueError, TypeError):
            return 0
    
    @field_validator("CORS_ORIGINS", "ALLOWED_HOSTS", mode="before")
    @classmethod
    def parse_cors_origins(cls, v):
        if isinstance(v, str):
            return [origin.strip() for origin in v.split(",")]
        return v
    
    @field_validator("FIREWALL_ALLOWLIST_DOMAINS", mode="before")
    @classmethod
    def parse_allowlist_domains(cls, v):
        """Parse allowlist domains from string or list"""
        if isinstance(v, list):
            # If it's already a list, convert back to string
            return ",".join(v)
        return v
    
    @field_validator("LOG_LEVEL")
    @classmethod
    def validate_log_level(cls, v):
        valid_levels = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
        if v.upper() not in valid_levels:
            raise ValueError(f"Invalid log level. Must be one of: {valid_levels}")
        return v.upper()
    
    @field_validator("FIREWALL_MODE", "CONTENT_FILTER_MODE")
    @classmethod
    def validate_security_mode(cls, v):
        valid_modes = ["permissive", "moderate", "strict"]
        if v.lower() not in valid_modes:
            raise ValueError(f"Invalid security mode. Must be one of: {valid_modes}")
        return v.lower()
    
    @field_validator("CONTAINER_ISOLATION_MODE")
    @classmethod
    def validate_isolation_mode(cls, v):
        valid_modes = ["docker", "gvisor", "firecracker"]
        if v.lower() not in valid_modes:
            raise ValueError(f"Invalid isolation mode. Must be one of: {valid_modes}")
        return v.lower()


@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance"""
    return Settings()

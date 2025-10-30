"""
AutoCodit Agent - Custom Exceptions

Application-specific exception classes with proper status codes
and error details for API responses.
"""

from typing import Optional, Dict, Any


class AutoCoditException(Exception):
    """Base exception for AutoCodit Agent"""
    
    def __init__(
        self,
        detail: str,
        status_code: int = 500,
        code: Optional[str] = None,
        context: Optional[Dict[str, Any]] = None
    ):
        self.detail = detail
        self.status_code = status_code
        self.code = code or self.__class__.__name__
        self.context = context or {}
        super().__init__(detail)


class TaskNotFoundException(AutoCoditException):
    """Task not found exception"""
    
    def __init__(self, task_id: str):
        super().__init__(
            detail=f"Task not found: {task_id}",
            status_code=404,
            code="TASK_NOT_FOUND",
            context={"task_id": task_id}
        )


class SessionNotFoundException(AutoCoditException):
    """Session not found exception"""
    
    def __init__(self, session_id: str):
        super().__init__(
            detail=f"Session not found: {session_id}",
            status_code=404,
            code="SESSION_NOT_FOUND",
            context={"session_id": session_id}
        )


class GitHubIntegrationException(AutoCoditException):
    """GitHub integration exception"""
    
    def __init__(self, detail: str, github_error: Optional[str] = None):
        super().__init__(
            detail=f"GitHub integration error: {detail}",
            status_code=422,
            code="GITHUB_INTEGRATION_ERROR",
            context={"github_error": github_error} if github_error else {}
        )


class RunnerException(AutoCoditException):
    """Runner/container exception"""
    
    def __init__(self, detail: str, container_id: Optional[str] = None):
        super().__init__(
            detail=f"Runner error: {detail}",
            status_code=500,
            code="RUNNER_ERROR",
            context={"container_id": container_id} if container_id else {}
        )


class AIProviderException(AutoCoditException):
    """AI provider exception"""
    
    def __init__(self, detail: str, provider: str, retryable: bool = True):
        super().__init__(
            detail=f"AI provider error ({provider}): {detail}",
            status_code=502 if retryable else 422,
            code="AI_PROVIDER_ERROR",
            context={"provider": provider, "retryable": retryable}
        )


class ResourceLimitException(AutoCoditException):
    """Resource limit exceeded exception"""
    
    def __init__(self, resource_type: str, limit: str, current: str):
        super().__init__(
            detail=f"Resource limit exceeded: {resource_type} (limit: {limit}, current: {current})",
            status_code=429,
            code="RESOURCE_LIMIT_EXCEEDED",
            context={
                "resource_type": resource_type,
                "limit": limit,
                "current": current
            }
        )


class SecurityViolationException(AutoCoditException):
    """Security violation exception"""
    
    def __init__(self, detail: str, violation_type: str):
        super().__init__(
            detail=f"Security violation: {detail}",
            status_code=403,
            code="SECURITY_VIOLATION",
            context={"violation_type": violation_type}
        )


class ConfigurationException(AutoCoditException):
    """Configuration exception"""
    
    def __init__(self, detail: str):
        super().__init__(
            detail=f"Configuration error: {detail}",
            status_code=500,
            code="CONFIGURATION_ERROR"
        )


class ValidationException(AutoCoditException):
    """Validation exception"""
    
    def __init__(self, detail: str, field: Optional[str] = None):
        super().__init__(
            detail=f"Validation error: {detail}",
            status_code=422,
            code="VALIDATION_ERROR",
            context={"field": field} if field else {}
        )
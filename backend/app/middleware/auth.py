from fastapi import Request, Response
from fastapi.responses import JSONResponse
import structlog
import time

logger = structlog.get_logger()


class AuthMiddleware:
    """Authentication middleware"""
    
    def __init__(self, app):
        self.app = app
    
    async def __call__(self, scope, receive, send):
        if scope["type"] == "http":
            request = Request(scope, receive)
            
            # Skip auth for health checks and webhooks
            if request.url.path in ["/health", "/metrics"] or request.url.path.startswith("/api/v1/github/webhook"):
                await self.app(scope, receive, send)
                return
            
            # Add request ID for tracing
            import uuid
            request.state.request_id = str(uuid.uuid4())
            
            # Add authentication context
            await self._add_auth_context(request)
        
        await self.app(scope, receive, send)
    
    async def _add_auth_context(self, request: Request):
        """Add authentication context to request"""
        # This would integrate with the auth system
        request.state.user = None
        request.state.authenticated = False
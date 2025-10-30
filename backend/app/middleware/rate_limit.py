import time
from typing import Dict
from collections import defaultdict, deque
from fastapi import Request, HTTPException
from fastapi.responses import JSONResponse
import structlog

logger = structlog.get_logger()


class RateLimitMiddleware:
    """Rate limiting middleware"""
    
    def __init__(self, app):
        self.app = app
        self.requests: Dict[str, deque] = defaultdict(deque)
        self.limits = {
            "/api/v1/tasks": (60, 60),  # 60 requests per minute
            "/api/v1/sessions": (120, 60),  # 120 requests per minute
            "default": (300, 60)  # 300 requests per minute for other endpoints
        }
    
    async def __call__(self, scope, receive, send):
        if scope["type"] == "http":
            request = Request(scope, receive)
            
            # Skip rate limiting for certain paths
            if request.url.path in ["/health", "/metrics"] or request.url.path.startswith("/ws"):
                await self.app(scope, receive, send)
                return
            
            # Check rate limits
            if not await self._check_rate_limit(request):
                response = JSONResponse(
                    status_code=429,
                    content={
                        "error": "Rate limit exceeded",
                        "detail": "Too many requests. Please try again later."
                    }
                )
                await response(scope, receive, send)
                return
        
        await self.app(scope, receive, send)
    
    async def _check_rate_limit(self, request: Request) -> bool:
        """Check if request is within rate limits"""
        client_ip = request.client.host if request.client else "unknown"
        current_time = time.time()
        
        # Determine rate limit for this path
        path_prefix = self._get_path_prefix(request.url.path)
        max_requests, window_seconds = self.limits.get(path_prefix, self.limits["default"])
        
        # Get request queue for this client
        key = f"{client_ip}:{path_prefix}"
        request_times = self.requests[key]
        
        # Remove old requests outside the window
        cutoff_time = current_time - window_seconds
        while request_times and request_times[0] < cutoff_time:
            request_times.popleft()
        
        # Check if within limits
        if len(request_times) >= max_requests:
            logger.warning(
                "Rate limit exceeded",
                client_ip=client_ip,
                path_prefix=path_prefix,
                requests=len(request_times),
                limit=max_requests
            )
            return False
        
        # Add current request
        request_times.append(current_time)
        
        return True
    
    def _get_path_prefix(self, path: str) -> str:
        """Extract path prefix for rate limiting"""
        for prefix in self.limits:
            if prefix != "default" and path.startswith(prefix):
                return prefix
        return "default"
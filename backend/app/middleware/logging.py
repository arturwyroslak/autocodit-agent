import time
from fastapi import Request
import structlog

logger = structlog.get_logger()


class LoggingMiddleware:
    """Request logging middleware"""
    
    def __init__(self, app):
        self.app = app
    
    async def __call__(self, scope, receive, send):
        if scope["type"] == "http":
            request = Request(scope, receive)
            start_time = time.time()
            
            # Log request start
            logger.info(
                "Request started",
                method=request.method,
                url=str(request.url),
                client_ip=request.client.host if request.client else None,
                user_agent=request.headers.get("user-agent"),
                request_id=getattr(request.state, "request_id", None)
            )
            
            # Process request
            response_started = False
            status_code = 500
            
            async def send_wrapper(message):
                nonlocal response_started, status_code
                if message["type"] == "http.response.start":
                    response_started = True
                    status_code = message["status"]
                await send(message)
            
            try:
                await self.app(scope, receive, send_wrapper)
            except Exception as e:
                logger.error(
                    "Request failed with exception",
                    method=request.method,
                    url=str(request.url),
                    error=str(e),
                    request_id=getattr(request.state, "request_id", None)
                )
                raise
            finally:
                # Log request completion
                end_time = time.time()
                duration = end_time - start_time
                
                logger.info(
                    "Request completed",
                    method=request.method,
                    url=str(request.url),
                    status_code=status_code,
                    duration_ms=round(duration * 1000, 2),
                    request_id=getattr(request.state, "request_id", None)
                )
        else:
            await self.app(scope, receive, send)
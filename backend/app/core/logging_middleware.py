from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from app.core.logging import logger
import time


class LoggingMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        # Start timing
        start_time = time.time()
        
        # Log request
        logger.info(
            f"Request: {request.method} {request.url.path}",
            extra={
                "method": request.method,
                "path": request.url.path,
                "client": request.client.host if request.client else None
            }
        )
        
        # Process request
        response = await call_next(request)
        
        # Calculate duration
        duration = time.time() - start_time
        
        # Log response
        logger.info(
            f"Response: {response.status_code} - {duration:.3f}s",
            extra={
                "status_code": response.status_code,
                "duration": duration
            }
        )
        
        return response


# Usage in main.py:
# from app.core.logging_middleware import LoggingMiddleware
# app.add_middleware(LoggingMiddleware)

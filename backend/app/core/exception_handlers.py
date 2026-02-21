from fastapi import Request, HTTPException
from fastapi.responses import JSONResponse
from starlette import status
from app.core.logging import logger
import traceback


async def global_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """Global exception handler for all unhandled exceptions"""
    
    # Log the error
    logger.error(
        f"Unhandled exception: {str(exc)}",
        extra={
            "path": request.url.path,
            "method": request.method,
            "error": str(exc),
            "traceback": traceback.format_exc()
        }
    )
    
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "detail": "Internal server error",
            "message": "An unexpected error occurred"
        }
    )


async def http_exception_handler(request: Request, exc) -> JSONResponse:
    """Handle HTTP exceptions"""
    
    logger.warning(
        f"HTTP exception: {exc.status_code} - {exc.detail}",
        extra={
            "status_code": exc.status_code,
            "detail": exc.detail,
            "path": request.url.path
        }
    )
    
    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": exc.detail}
    )


# Usage in main.py:
# from app.core.exception_handlers import global_exception_handler, http_exception_handler
# from fastapi import HTTPException
# app.add_exception_handler(Exception, global_exception_handler)
# app.add_exception_handler(HTTPException, http_exception_handler)

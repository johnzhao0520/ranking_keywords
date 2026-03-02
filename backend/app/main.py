from fastapi import FastAPI, Request, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from contextlib import asynccontextmanager
import os

from app.core.config import settings
from app.core.database import Base, engine
from app.core.logging import logger
from app.core.logging_middleware import LoggingMiddleware
from app.core.exception_handlers import global_exception_handler, http_exception_handler
from app.api import auth, users, projects, tracking, keywords


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: Create tables
    logger.info("Starting application...")
    Base.metadata.create_all(bind=engine)
    logger.info("Database tables created")
    
    # 仅在本地开发时启动定时任务（ Railway 使用 Cron 调用 /api/tracking/process）
    if os.getenv("RUN_SCHEDULER", "false").lower() == "true":
        from app.services.scheduler import start_scheduler
        start_scheduler()
        logger.info("APScheduler started (RUN_SCHEDULER=true)")
    else:
        logger.info("APScheduler disabled - use Railway Cron to call /api/tracking/process")
    
    yield
    # Shutdown
    logger.info("Shutting down application...")
    if os.getenv("RUN_SCHEDULER", "false").lower() == "true":
        from app.services.scheduler import stop_scheduler
        stop_scheduler()


app = FastAPI(
    title=settings.APP_NAME,
    description="Google Keyword Tracking Tool API",
    version="1.0.0",
    lifespan=lifespan
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Logging middleware
app.add_middleware(LoggingMiddleware)

# Exception handlers
app.add_exception_handler(Exception, global_exception_handler)
app.add_exception_handler(HTTPException, http_exception_handler)

# Include routers
app.include_router(auth.router, prefix="/api")
app.include_router(users.router, prefix="/api")
app.include_router(projects.router, prefix="/api")
app.include_router(tracking.router, prefix="/api")
app.include_router(keywords.router, prefix="/api")


@app.get("/")
def root():
    logger.info("Root endpoint accessed")
    from fastapi.responses import FileResponse
    return FileResponse("app/static/index.html")


@app.get("/admin")
def admin():
    from fastapi.responses import FileResponse
    return FileResponse("app/static/admin.html")


@app.get("/login")
@app.get("/register")
@app.get("/pricing")
def coming_soon():
    return {"message": "Coming soon! API is working."}


@app.get("/health")
def health_check():
    return {"status": "healthy"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)

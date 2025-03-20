"""
Main FastAPI application module.
Initializes the API, includes routers, and configures middleware.
"""

from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware

from ..config.settings import get_settings, Settings
from ..services.task_manager import task_manager, start_task_manager, stop_task_manager
from ..utils.logging import app_logger
from .router import router as generation_router
from .async_router import router as async_router
from .presentation_router import router as presentation_router
from .user_router import router as user_router
from .upload_router import router as upload_router
from ..middleware.error_handler import register_exception_handlers
from ..models.database import DatabaseManager

# Create FastAPI app
app = FastAPI(
    title="Presentation Automator API",
    description="API for generating presentations from text using AI",
    version="0.1.0",
)

# Include routers
app.include_router(generation_router)
app.include_router(async_router)
app.include_router(presentation_router)
app.include_router(user_router)
app.include_router(upload_router)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Adjust for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register error handlers
register_exception_handlers(app)


# Root endpoint for health checks
@app.get("/", tags=["Health"])
async def root():
    """Root endpoint for basic health check."""
    return {"status": "ok", "message": "Presentation Automator API is running"}


# Detailed health check endpoint
@app.get("/health", tags=["Health"])
async def health_check(settings: Settings = Depends(get_settings)):
    """Detailed health check endpoint."""
    # Check if OpenAI API key is configured
    api_key_status = "configured" if settings.api.openai_api_key else "missing"
    
    # Check task manager status
    task_manager_status = "running" if task_manager.running else "stopped"
    active_tasks = len(task_manager.get_active_tasks())
    
    # Check database connection
    try:
        db_session = DatabaseManager.get_session()
        db_session.execute("SELECT 1")  # Simple query to check connection
        db_status = "connected"
        db_session.close()
    except Exception as e:
        db_status = f"error: {str(e)}"
    
    return {
        "status": "ok",
        "api_status": {
            "openai_api_key": api_key_status
        },
        "database_status": db_status,
        "task_manager": {
            "status": task_manager_status,
            "active_tasks": active_tasks
        },
        "server_info": {
            "debug_mode": settings.server.debug,
            "log_level": settings.server.log_level
        }
    }


# Event handlers for startup and shutdown
@app.on_event("startup")
async def startup_event():
    """Executed when the application starts up."""
    app_logger.info("Starting Presentation Automator API")
    
    # Check if OpenAI API key is set
    settings = get_settings()
    if not settings.api.openai_api_key:
        app_logger.warning("OPENAI_API_KEY is not set - some features may not work")
    
    # Initialize database
    try:
        DatabaseManager.initialize()
        app_logger.info("Database initialized")
    except Exception as e:
        app_logger.error(f"Failed to initialize database: {e}")
    
    # Start the task manager
    await start_task_manager()
    app_logger.info("Task manager started")


@app.on_event("shutdown")
async def shutdown_event():
    """Executed when the application is shutting down."""
    app_logger.info("Shutting down Presentation Automator API")
    
    # Close database connections
    try:
        DatabaseManager.close()
        app_logger.info("Database connections closed")
    except Exception as e:
        app_logger.error(f"Error closing database connections: {e}")
    
    # Stop the task manager
    await stop_task_manager()
    app_logger.info("Task manager stopped") 
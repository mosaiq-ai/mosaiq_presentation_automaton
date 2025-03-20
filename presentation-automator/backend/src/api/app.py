"""
Main FastAPI application module.
Initializes the API, includes routers, and configures middleware.
"""

from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware

from ..config.settings import get_settings, Settings
from ..utils.logging import app_logger
from .router import router as generation_router

# Create FastAPI app
app = FastAPI(
    title="Presentation Automator API",
    description="API for generating presentations from text using AI",
    version="0.1.0",
)

# Include routers
app.include_router(generation_router)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Adjust for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


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
    
    return {
        "status": "ok",
        "api_status": {
            "openai_api_key": api_key_status
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


@app.on_event("shutdown")
async def shutdown_event():
    """Executed when the application is shutting down."""
    app_logger.info("Shutting down Presentation Automator API") 
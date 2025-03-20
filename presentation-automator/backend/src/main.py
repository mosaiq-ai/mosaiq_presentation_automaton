"""
Main entry point for the application.
Configures and starts the ASGI server.
"""

import uvicorn
from .config.settings import get_settings
from .utils.logging import app_logger

settings = get_settings()


def start():
    """Start the application server."""
    app_logger.info(f"Starting server on {settings.server.host}:{settings.server.port}")
    
    uvicorn.run(
        "src.api.app:app",
        host=settings.server.host,
        port=settings.server.port,
        reload=settings.server.debug,
        log_level=settings.server.log_level.lower(),
    )


if __name__ == "__main__":
    start() 
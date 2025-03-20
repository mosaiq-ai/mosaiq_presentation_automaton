# Project Plan 1: Setup and Core Infrastructure

## Overview

This project plan covers the initial setup and core infrastructure development for the Presentation Automator backend. It focuses on establishing a robust foundation that will support the more complex agent-based functionality in future phases.

## Objectives

1. Set up the development environment
2. Establish project configuration
3. Create the basic API structure
4. Implement health check endpoints
5. Set up proper logging
6. Configure environment variables handling

## Prerequisites

- Python 3.11 or higher
- Git
- Basic understanding of FastAPI
- Access to OpenAI API (API key)

## Deliverables

1. Fully configured development environment
2. Project structure with proper configuration files
3. Working FastAPI application with health check endpoints
4. Environment variables management system
5. Comprehensive logging setup

## Time Estimate

Approximately 2-3 days for a junior engineer.

## Detailed Implementation Steps

### Step 1: Create Project Directory Structure

```bash
# Create main project directory
mkdir -p presentation-automator/backend
cd presentation-automator/backend

# Create subdirectories for organization
mkdir -p src/api
mkdir -p src/config
mkdir -p src/utils
mkdir -p src/models
mkdir -p tests
mkdir -p docs
```

### Step 2: Set Up Virtual Environment and Core Dependencies

```bash
# Create virtual environment
python -m venv .venv

# Activate virtual environment
# On Windows:
# .venv\Scripts\activate
# On macOS/Linux:
source .venv/bin/activate

# Upgrade pip
pip install --upgrade pip

# Install core dependencies
pip install fastapi uvicorn python-dotenv pydantic openai openai-agents
```

### Step 3: Create Configuration Files

#### pyproject.toml

Create a `pyproject.toml` file in the root directory with the following content:

```toml
[build-system]
requires = ["setuptools>=42.0.0", "wheel"]
build-backend = "setuptools.build_meta"

[project]
name = "presentation-automator-backend"
version = "0.1.0"
description = "Backend for the Presentation Automator system"
requires-python = ">=3.11"
dependencies = [
    "fastapi>=0.100.0",
    "uvicorn>=0.20.0",
    "pydantic>=2.0.0",
    "python-dotenv>=1.0.0",
    "openai>=1.0.0",
    "openai-agents>=0.0.1",
    "loguru>=0.7.0"
]

[project.optional-dependencies]
dev = [
    "pytest>=7.0.0",
    "pytest-asyncio>=0.20.0",
    "black>=23.0.0",
    "isort>=5.12.0",
    "mypy>=1.0.0"
]
```

#### Environment Variables

Create a `.env` file in the root directory:

```
# OpenAI API Configuration
OPENAI_API_KEY=your_openai_api_key_here

# Server Configuration
HOST=0.0.0.0
PORT=8000
LOG_LEVEL=INFO

# Development Settings
DEBUG=True
```

Also create a `.env.example` file that shows the structure without actual values:

```
# OpenAI API Configuration
OPENAI_API_KEY=

# Server Configuration
HOST=0.0.0.0
PORT=8000
LOG_LEVEL=INFO

# Development Settings
DEBUG=True
```

#### .gitignore

Create a `.gitignore` file:

```
# Python
__pycache__/
*.py[cod]
*$py.class
*.so
.Python
env/
build/
develop-eggs/
dist/
downloads/
eggs/
.eggs/
lib/
lib64/
parts/
sdist/
var/
*.egg-info/
.installed.cfg
*.egg

# Virtual Environment
.venv/
venv/
ENV/

# IDE
.idea/
.vscode/
*.swp
*.swo

# Environment variables
.env

# Logs
logs/
*.log

# Testing
.coverage
htmlcov/
.pytest_cache/

# Misc
.DS_Store
```

### Step 4: Create Configuration Module

Create the configuration management module at `src/config/settings.py`:

```python
"""
Configuration settings for the application.
Loads environment variables and provides settings for various components.
"""

import os
from typing import Optional
from pydantic import BaseModel, Field
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()


class ServerSettings(BaseModel):
    """Server configuration settings."""
    host: str = Field(default="0.0.0.0")
    port: int = Field(default=8000)
    debug: bool = Field(default=False)
    log_level: str = Field(default="INFO")


class APISettings(BaseModel):
    """API configuration settings."""
    openai_api_key: str = Field(default="")


class Settings(BaseModel):
    """Application settings."""
    server: ServerSettings = Field(default_factory=ServerSettings)
    api: APISettings = Field(default_factory=APISettings)


def load_settings() -> Settings:
    """Load settings from environment variables."""
    return Settings(
        server=ServerSettings(
            host=os.getenv("HOST", "0.0.0.0"),
            port=int(os.getenv("PORT", "8000")),
            debug=os.getenv("DEBUG", "False").lower() in ("true", "1", "t"),
            log_level=os.getenv("LOG_LEVEL", "INFO"),
        ),
        api=APISettings(
            openai_api_key=os.getenv("OPENAI_API_KEY", ""),
        ),
    )


# Create a global settings instance
settings = load_settings()


def get_settings() -> Settings:
    """Get the application settings."""
    return settings
```

### Step 5: Create Logging Utilities

Create the logging utility at `src/utils/logging.py`:

```python
"""
Logging configuration for the application.
Sets up loggers with appropriate formatting and log levels.
"""

import sys
import logging
from pathlib import Path
from logging.handlers import RotatingFileHandler

from ..config.settings import get_settings

# Get settings
settings = get_settings()

# Define log format
LOG_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
DATE_FORMAT = "%Y-%m-%d %H:%M:%S"

# Define log levels
LOG_LEVELS = {
    "DEBUG": logging.DEBUG,
    "INFO": logging.INFO,
    "WARNING": logging.WARNING,
    "ERROR": logging.ERROR,
    "CRITICAL": logging.CRITICAL,
}


def setup_logger(name: str) -> logging.Logger:
    """
    Set up a logger with the specified name.
    
    Args:
        name: The name for the logger.
        
    Returns:
        A configured logger instance.
    """
    # Create logger
    logger = logging.getLogger(name)
    
    # Set log level from settings
    log_level = LOG_LEVELS.get(settings.server.log_level.upper(), logging.INFO)
    logger.setLevel(log_level)
    
    # Create handlers
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(log_level)
    
    # Create formatters
    formatter = logging.Formatter(LOG_FORMAT, datefmt=DATE_FORMAT)
    
    # Add formatters to handlers
    console_handler.setFormatter(formatter)
    
    # Add handlers to logger
    if not logger.handlers:
        logger.addHandler(console_handler)
    
    # Don't propagate to root logger
    logger.propagate = False
    
    return logger


# Create application logger
app_logger = setup_logger("presentation_automator")
```

### Step 6: Create Basic API Module

Create the main API module at `src/api/app.py`:

```python
"""
Main FastAPI application module.
Initializes the API, includes routers, and configures middleware.
"""

from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware

from ..config.settings import get_settings, Settings
from ..utils.logging import app_logger

# Create FastAPI app
app = FastAPI(
    title="Presentation Automator API",
    description="API for generating presentations from text using AI",
    version="0.1.0",
)

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
```

### Step 7: Create Server Entry Point

Create the server entry point at `src/main.py`:

```python
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
```

### Step 8: Create a Simple Run Script

Create a bash script to run the server at the project root level (`run.sh`):

```bash
#!/bin/bash

# Activate virtual environment
source .venv/bin/activate

# Run the server
python -m src.main
```

Make the script executable:

```bash
chmod +x run.sh
```

### Step 9: Create Basic Test

Create a basic test at `tests/test_health.py`:

```python
"""
Tests for the health check endpoints.
"""

import pytest
from fastapi.testclient import TestClient

from src.api.app import app

client = TestClient(app)


def test_root_endpoint():
    """Test the root endpoint returns correct status."""
    response = client.get("/")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_health_endpoint():
    """Test the health endpoint returns detailed status."""
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"
    assert "api_status" in response.json()
    assert "server_info" in response.json()
```

### Step 10: Create a Package Structure

Create `src/__init__.py`:

```python
"""
Presentation Automator backend package.
"""

__version__ = "0.1.0"
```

Create empty `__init__.py` files in each subdirectory to make them proper Python packages:

```bash
touch src/api/__init__.py
touch src/config/__init__.py
touch src/utils/__init__.py
touch src/models/__init__.py
touch tests/__init__.py
```

### Step 11: Create Installation Instructions

Create a `README.md` file in the project root:

```markdown
# Presentation Automator Backend

Backend API for the Presentation Automator system, which generates professional presentations from text using AI.

## Requirements

- Python 3.11 or higher
- OpenAI API key

## Setup

1. Clone the repository:
   ```bash
   git clone [repository-url]
   cd presentation-automator/backend
   ```

2. Create a virtual environment:
   ```bash
   python -m venv .venv
   source .venv/bin/activate  # On Windows: .venv\Scripts\activate
   ```

3. Install dependencies:
   ```bash
   pip install -e .
   ```

4. Configure environment variables:
   ```bash
   cp .env.example .env
   # Edit .env file and add your OpenAI API key
   ```

## Running the Server

```bash
# Using the run script
./run.sh

# Or manually
source .venv/bin/activate
python -m src.main
```

The server will start at `http://localhost:8000` by default.

## API Documentation

Once the server is running, you can access the Swagger UI documentation at:
http://localhost:8000/docs

## Running Tests

```bash
pytest
```
```

## Testing Instructions

To verify that everything is working correctly:

1. Follow the setup instructions to create the virtual environment and install dependencies
2. Set your OpenAI API key in the `.env` file
3. Run the server using `./run.sh`
4. Open a web browser and navigate to `http://localhost:8000`
5. Verify that you see a JSON response with `{"status": "ok", "message": "Presentation Automator API is running"}`
6. Check the health endpoint at `http://localhost:8000/health` to verify that your API key is recognized
7. Run the tests with `pytest` to ensure all tests pass

## Next Steps

After completing this project plan, you should have a working API server with:
- Proper environment configuration
- Health check endpoints
- Logging setup
- Basic project structure

You're now ready to proceed to Project Plan 2, which will focus on implementing the agent framework. 
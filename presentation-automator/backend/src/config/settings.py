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
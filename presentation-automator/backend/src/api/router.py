"""
API router for presentation generation endpoints.
"""

import time
from typing import Dict, Any, Optional

from fastapi import APIRouter, HTTPException, Depends, BackgroundTasks
from pydantic import BaseModel

from ..config.settings import get_settings, Settings
from ..models.schemas import GenerationRequest, GenerationResponse, Presentation
from ..agents.presentation_generator import PresentationGenerator
from ..utils.logging import setup_logger

# Create logger
logger = setup_logger("api_router")

# Create router
router = APIRouter(prefix="/api", tags=["Generation"])

# Create presentation generator
generator = PresentationGenerator()


class ErrorResponse(BaseModel):
    """Error response model."""
    detail: str


@router.post(
    "/generate",
    response_model=GenerationResponse,
    responses={500: {"model": ErrorResponse}}
)
async def generate_presentation(
    request: GenerationRequest,
    settings: Settings = Depends(get_settings),
):
    """
    Generate a presentation from document text.
    
    Args:
        request: The generation request containing document text and options
        settings: Application settings
        
    Returns:
        The generated presentation
    """
    # Verify API key is set
    if not settings.api.openai_api_key:
        raise HTTPException(
            status_code=500,
            detail="OpenAI API key is not configured. Please set OPENAI_API_KEY in environment variables."
        )
    
    try:
        # Log the request
        logger.info(f"Received generation request. Text length: {len(request.document_text)}")
        start_time = time.time()
        
        # Generate the presentation
        presentation = await generator.generate_from_text(
            request.document_text,
            request.options
        )
        
        # Calculate generation time
        generation_time = time.time() - start_time
        
        # Create and return the response
        return GenerationResponse(
            presentation=presentation,
            metadata={
                "generation_time_seconds": generation_time,
                "slide_count": len(presentation.slides)
            }
        )
        
    except Exception as e:
        # Log the error
        logger.error(f"Error generating presentation: {str(e)}")
        
        # Raise HTTP exception
        raise HTTPException(
            status_code=500,
            detail=f"Presentation generation failed: {str(e)}"
        ) 
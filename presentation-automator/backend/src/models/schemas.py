"""
Schema definitions for the presentation generation process.
These models define the structure of data exchanged between components.
"""

from typing import List, Dict, Optional, Any
from pydantic import BaseModel, Field


class SlideStructure(BaseModel):
    """Structure of a single slide in a presentation."""
    
    slide_number: int = Field(..., description="Slide number in the presentation")
    title: str = Field(..., description="Title of the slide")
    content_tokens: List[str] = Field(
        ..., 
        description="Key points to include in the slide content"
    )
    format_tokens: List[str] = Field(
        default_factory=list, 
        description="Formatting instructions for the slide"
    )
    design_tokens: List[str] = Field(
        default_factory=list, 
        description="Design elements to include in the slide"
    )


class PresentationPlan(BaseModel):
    """Overall plan for a presentation."""
    
    title: str = Field(..., description="Title of the presentation")
    theme: str = Field(..., description="Visual theme for the presentation")
    slides: List[SlideStructure] = Field(
        ..., 
        description="List of slides in the presentation"
    )


class SlideContent(BaseModel):
    """Detailed content for a single slide."""
    
    slide_number: int = Field(..., description="Slide number in the presentation")
    title: str = Field(..., description="Title of the slide")
    content: str = Field(..., description="HTML content of the slide")
    notes: str = Field(default="", description="Speaker notes for the slide")


class Presentation(BaseModel):
    """Complete presentation with all content."""
    
    title: str = Field(..., description="Title of the presentation")
    theme: str = Field(..., description="Visual theme for the presentation")
    slides: List[SlideContent] = Field(..., description="List of slides with content")


class GenerationRequest(BaseModel):
    """Request for generating a presentation."""
    
    document_text: str = Field(..., description="Document text to generate presentation from")
    options: Dict[str, Any] = Field(
        default_factory=dict, 
        description="Additional options for generation"
    )


class GenerationResponse(BaseModel):
    """Response from the presentation generation process."""
    
    presentation: Presentation = Field(..., description="Generated presentation")
    metadata: Dict[str, Any] = Field(
        default_factory=dict, 
        description="Additional metadata about the generation process"
    ) 
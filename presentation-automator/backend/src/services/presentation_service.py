"""
Enhanced presentation service with context sharing.

This module provides the main service for generating presentations with
improved context sharing between component agents.
"""

import asyncio
import os
import uuid
from typing import Any, Callable, Dict, List, Optional, Tuple, Union
from datetime import datetime

from loguru import logger

from ..agents import planning_agent, content_agent, get_planning_agent, get_content_agent
from ..models.schemas import GenerationRequest, GenerationResponse, Presentation, PresentationPlan
from ..utils.context_manager import GenerationContext, StageStatus
from .cache_service import cache, CacheType
from .content_extraction import content_extractor
from .document_processor import document_processor
from .task_manager import update_task_progress


class PresentationService:
    """Service for generating presentations with context sharing."""
    
    def __init__(self):
        """Initialize the presentation service."""
        logger.info("Initializing enhanced presentation service")
    
    async def generate_presentation(
        self,
        text: str,
        options: Optional[Dict[str, Any]] = None,
        task_id: Optional[str] = None,
        progress_callback: Optional[Callable[[float, str], None]] = None,
    ) -> Presentation:
        """
        Generate a presentation from document text with context sharing.
        
        Args:
            text: The document text to generate from
            options: Optional generation options
            task_id: Optional task ID for progress tracking
            progress_callback: Optional callback for progress updates
            
        Returns:
            A complete presentation with slides
            
        Raises:
            Exception: If generation fails
        """
        try:
            if options is None:
                options = {}
            
            # Create a context object for sharing data between steps
            context = GenerationContext()
            
            # Process the document to extract sections, bullet points, etc.
            if task_id:
                update_task_progress(task_id, 0.1, "Processing document")
            if progress_callback:
                progress_callback(0.1, "Processing document")
            
            # Process the document
            processed_result = await document_processor.process_document(text)
            sections = processed_result.get("sections", [])
            
            # Extract key information
            if task_id:
                update_task_progress(task_id, 0.3, "Extracting key information")
            if progress_callback:
                progress_callback(0.3, "Extracting key information")
            
            # Extract additional information for context
            extraction_results = await asyncio.gather(
                content_extractor.extract_bullet_points(text, max_points=20),
                content_extractor.extract_keywords(text, max_keywords=15),
                content_extractor.get_document_statistics(text),
            )
            
            bullet_points = extraction_results[0]
            keywords = extraction_results[1]
            stats = extraction_results[2]
            
            # Share extracted data in context
            context.share_data("document_text", text)
            context.share_data("sections", sections)
            context.share_data("bullet_points", bullet_points)
            context.share_data("keywords", keywords)
            context.share_data("document_statistics", stats)
            context.share_data("options", options)
            
            # Generate a presentation plan with context sharing
            if task_id:
                update_task_progress(task_id, 0.5, "Creating presentation plan")
            if progress_callback:
                progress_callback(0.5, "Creating presentation plan")
            
            # Get the planning agent with context capabilities
            plan_agent = get_planning_agent()
            
            # Prepare input for planning agent
            planning_input = {
                "document_text": text,
                "sections": sections,
                "bullet_points": bullet_points,
                "keywords": keywords,
                "document_statistics": stats,
                "options": options
            }
            
            # Set context stage
            context.set_stage_status("planning", StageStatus.IN_PROGRESS)
            
            # Create the presentation plan
            plan = await plan_agent.create_presentation_plan(planning_input, context=context)
            
            # Store plan in context for later use
            context.share_data("presentation_plan", plan)
            context.set_stage_status("planning", StageStatus.COMPLETED)
            
            # Generate detailed content with context sharing
            if task_id:
                update_task_progress(task_id, 0.6, "Generating slide content")
            if progress_callback:
                progress_callback(0.6, "Generating slide content")
            
            # Get the content agent with context capabilities
            slide_agent = get_content_agent()
            
            # Set context stage
            context.set_stage_status("content_generation", StageStatus.IN_PROGRESS)
            
            # Create the slide content using the plan and context
            presentation = await slide_agent.generate_slides(
                plan=plan,
                document_text=text,
                context=context
            )
            
            # Update progress
            if task_id:
                update_task_progress(task_id, 0.9, "Finalizing presentation")
            if progress_callback:
                progress_callback(0.9, "Finalizing presentation")
                
            # Set final context stage
            context.set_stage_status("content_generation", StageStatus.COMPLETED)
            
            return presentation
        except Exception as e:
            logger.error(f"Error generating presentation: {e}")
            raise
    
    @cache(namespace="presentations", expire=3600 * 24 * 7, cache_type=CacheType.BOTH)  # Cache for 1 week
    async def generate_cached_presentation(
        self,
        text: str,
        options: Optional[Dict[str, Any]] = None,
        task_id: Optional[str] = None,
        progress_callback: Optional[Callable[[float, str], None]] = None,
    ) -> Presentation:
        """
        Generate a presentation with caching.
        
        Args:
            text: The document text to generate from
            options: Optional generation options
            task_id: Optional task ID for progress tracking
            progress_callback: Optional callback for progress updates
            
        Returns:
            A complete presentation with slides
        """
        return await self.generate_presentation(
            text=text, 
            options=options,
            task_id=task_id,
            progress_callback=progress_callback
        )
    
    async def handle_generation_request(
        self,
        request: GenerationRequest,
        task_id: Optional[str] = None
    ) -> GenerationResponse:
        """
        Handle a generation request.
        
        Args:
            request: Generation request with document text and options
            task_id: Optional task ID for progress tracking
            
        Returns:
            Generation response with presentation and metadata
        """
        # Generate the presentation
        presentation = await self.generate_cached_presentation(
            text=request.document_text,
            options=request.options,
            task_id=task_id
        )
        
        # Create and return the response
        return GenerationResponse(
            presentation=presentation,
            metadata={
                "word_count": len(request.document_text.split()),
                "slide_count": len(presentation.slides),
                "generated_at": datetime.now().isoformat(),
                "task_id": task_id
            }
        )


# Create a singleton instance
presentation_service = PresentationService()

# Convenience functions for direct module use
async def generate_presentation(
    document_text: str,
    options: Optional[Dict[str, Any]] = None,
    **kwargs
) -> Presentation:
    """Generate a presentation from document text."""
    return await presentation_service.generate_presentation(document_text, options, **kwargs)

async def generate_from_file(
    file_path: str,
    options: Optional[Dict[str, Any]] = None,
    **kwargs
) -> Presentation:
    """Generate a presentation from a file."""
    return await presentation_service.generate_from_file(file_path, options, **kwargs)

async def handle_generation_request(
    request: GenerationRequest,
    task_id: Optional[str] = None
) -> GenerationResponse:
    """Handle a presentation generation request."""
    return await presentation_service.handle_generation_request(request, task_id) 
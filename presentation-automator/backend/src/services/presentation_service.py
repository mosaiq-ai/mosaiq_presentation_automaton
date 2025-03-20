"""
Enhanced presentation service with context sharing.

This module provides the main service for generating presentations with
improved context sharing between component agents.
"""

import asyncio
import os
import uuid
from typing import Any, Callable, Dict, List, Optional, Tuple, Union

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
        document_text: str,
        options: Optional[Dict[str, Any]] = None,
        context: Optional[GenerationContext] = None,
        task_id: Optional[str] = None,
        progress_callback: Optional[Callable[[float, str], None]] = None
    ) -> Presentation:
        """
        Generate a presentation from document text with context sharing.
        
        Args:
            document_text: The document text to generate from
            options: Optional configuration for generation
            context: Optional context for tracking and sharing data
            task_id: Optional task ID for tracking progress
            progress_callback: Optional callback for progress updates
            
        Returns:
            The generated presentation
        """
        # Initialize options
        options = options or {}
        
        # Initialize context if not provided
        if context is None:
            context = GenerationContext(
                generation_id=task_id or str(uuid.uuid4()),
                document_source="text"
            )
        
        try:
            # Report initial progress
            if task_id:
                update_task_progress(task_id, 0.1, "Processing document")
            if progress_callback:
                progress_callback(0.1, "Processing document")
            
            # Process the document
            text, stats = await document_processor.process_document(
                document_text=document_text,
                context=context
            )
            
            # Extract content elements
            if task_id:
                update_task_progress(task_id, 0.2, "Extracting content elements")
            if progress_callback:
                progress_callback(0.2, "Extracting content elements")
            
            # Extract sections (structure)
            sections = await content_extractor.extract_sections(text, context)
            
            # Extract bullet points
            bullet_points = await content_extractor.extract_bullet_points(text, context)
            
            # Extract keywords
            keywords = await content_extractor.extract_keywords(text, max_keywords=15, context=context)
            
            # Generate presentation plan with context
            if task_id:
                update_task_progress(task_id, 0.4, "Creating presentation plan")
            if progress_callback:
                progress_callback(0.4, "Creating presentation plan")
            
            # Get the planning agent with context capabilities
            plan_agent = get_planning_agent()
            
            # Create agent input with processed content
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
            plan = await plan_agent.generate_plan(planning_input, context=context)
            
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
            
            # Complete the context
            context.set_stage_status("content_generation", StageStatus.COMPLETED)
            context.complete_generation()
            
            # Final progress update
            if task_id:
                update_task_progress(task_id, 1.0, "Presentation generation complete")
            if progress_callback:
                progress_callback(1.0, "Presentation generation complete")
            
            return presentation
        
        except Exception as e:
            # Log and record error in context
            logger.error(f"Error generating presentation: {e}")
            if context:
                context.stats.record_error("presentation_generation", str(e))
            raise
    
    @cache(namespace="presentations", expire=3600, cache_type=CacheType.BOTH)
    async def generate_cached_presentation(
        self,
        document_text: str,
        options: Optional[Dict[str, Any]] = None,
        task_id: Optional[str] = None,
        progress_callback: Optional[Callable[[float, str], None]] = None
    ) -> Presentation:
        """
        Generate a presentation with caching.
        
        This method wraps generate_presentation with caching for performance.
        
        Args:
            document_text: The document text to generate from
            options: Optional configuration for generation
            task_id: Optional task ID for tracking progress
            progress_callback: Optional callback for progress updates
            
        Returns:
            The generated presentation
        """
        # Create a new context
        context = GenerationContext(
            generation_id=task_id or str(uuid.uuid4()),
            document_source="text"
        )
        
        return await self.generate_presentation(
            document_text=document_text,
            options=options,
            context=context,
            task_id=task_id,
            progress_callback=progress_callback
        )
    
    async def generate_from_file(
        self,
        file_path: str,
        options: Optional[Dict[str, Any]] = None,
        task_id: Optional[str] = None,
        progress_callback: Optional[Callable[[float, str], None]] = None
    ) -> Presentation:
        """
        Generate a presentation from a file.
        
        Args:
            file_path: Path to the document file
            options: Optional configuration for generation
            task_id: Optional task ID for tracking progress
            progress_callback: Optional callback for progress updates
            
        Returns:
            The generated presentation
        """
        # Report initial progress
        if task_id:
            update_task_progress(task_id, 0.05, "Reading file")
        if progress_callback:
            progress_callback(0.05, "Reading file")
        
        # Create a new context
        context = GenerationContext(
            generation_id=task_id or str(uuid.uuid4()),
            document_source=file_path
        )
        
        # Process the document file
        text, stats = await document_processor.process_document(
            file_path=file_path,
            context=context
        )
        
        # Generate presentation
        return await self.generate_presentation(
            document_text=text,
            options=options,
            context=context,
            task_id=task_id,
            progress_callback=progress_callback
        )
    
    async def handle_generation_request(
        self, 
        request: GenerationRequest,
        task_id: Optional[str] = None
    ) -> GenerationResponse:
        """
        Handle a presentation generation request.
        
        Args:
            request: The generation request
            task_id: Optional task ID for tracking progress
            
        Returns:
            Response with the generated presentation
        """
        # Create a callback for progress updates
        def progress_callback(progress: float, message: str) -> None:
            if task_id:
                update_task_progress(task_id, progress, message)
        
        # Generate the presentation
        presentation = await self.generate_cached_presentation(
            document_text=request.document_text,
            options=request.options,
            task_id=task_id,
            progress_callback=progress_callback
        )
        
        # Create the response
        return GenerationResponse(
            presentation=presentation,
            metadata={
                "task_id": task_id,
                "options": request.options
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
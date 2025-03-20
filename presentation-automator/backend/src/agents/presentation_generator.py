"""
Main presentation generator orchestrator.
Coordinates the planning and content agents to generate complete presentations.
"""

from typing import Dict, Any, List, Optional
import time
import asyncio

from ..models.schemas import Presentation, SlideContent
from .planning_agent import PlanningAgent
from .content_agent import ContentAgent
from ..utils.logging import setup_logger

# Create a logger
logger = setup_logger("presentation_generator")


class PresentationGenerator:
    """
    Orchestrates the presentation generation process, coordinating
    the planning agent and content agent to produce a complete presentation.
    """
    
    def __init__(self):
        """Initialize the presentation generator with its component agents."""
        self.planning_agent = PlanningAgent()
        self.content_agent = ContentAgent()
        logger.info("Initialized PresentationGenerator")
    
    async def generate_from_text(
        self, 
        document_text: str,
        options: Optional[Dict[str, Any]] = None
    ) -> Presentation:
        """
        Generate a complete presentation from text.
        
        Args:
            document_text: The document text to generate from
            options: Optional generation options
            
        Returns:
            A complete presentation with content
        """
        # Log start of generation
        start_time = time.time()
        logger.info("Starting presentation generation from text")
        
        # Initialize context for sharing data between agents
        context = {
            "original_document": document_text,
            "options": options or {},
            "start_time": start_time,
            "stages_completed": []
        }
        
        # Step 1: Generate presentation plan
        logger.info("Generating presentation plan")
        presentation_plan = await self.planning_agent.create_presentation_plan(
            document_text,
            context=context
        )
        
        # Update context
        context["plan"] = presentation_plan.model_dump()
        context["stages_completed"].append("planning")
        
        # Step 2: Generate content for each slide
        logger.info(f"Generating content for {len(presentation_plan.slides)} slides")
        slides = []
        
        for slide_structure in presentation_plan.slides:
            # Extract relevant content for the slide
            # In a real system, this would involve more sophisticated content extraction
            # Currently using the full document for simplicity
            extracted_content = document_text
            
            # Generate content for the slide
            slide_content = await self.content_agent.generate_slide_content(
                slide_structure,
                extracted_content,
                context=context
            )
            
            slides.append(slide_content)
        
        # Update context
        context["stages_completed"].append("content_generation")
        
        # Step 3: Create the final presentation
        presentation = Presentation(
            title=presentation_plan.title,
            theme=presentation_plan.theme,
            slides=slides
        )
        
        # Add final timing information to context
        end_time = time.time()
        context["end_time"] = end_time
        context["total_time"] = end_time - start_time
        
        logger.info(f"Presentation generation completed in {context['total_time']:.2f} seconds")
        
        return presentation
    
    def generate_from_text_sync(
        self, 
        document_text: str,
        options: Optional[Dict[str, Any]] = None
    ) -> Presentation:
        """
        Synchronous wrapper for generate_from_text.
        
        Args:
            document_text: The document text to generate from
            options: Optional generation options
            
        Returns:
            A complete presentation with content
        """
        return asyncio.run(self.generate_from_text(document_text, options)) 
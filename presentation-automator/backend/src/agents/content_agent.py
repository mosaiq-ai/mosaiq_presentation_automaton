"""
Content agent for the presentation automator.
Generates detailed content for slides based on the presentation plan.
"""

from typing import Dict, Any, Optional

from ..models.schemas import SlideContent, SlideStructure, Presentation
from .base import BaseAgent
from ..utils.logging import setup_logger

# Create a logger
logger = setup_logger("content_agent")


class ContentAgent(BaseAgent[SlideContent]):
    """
    Agent responsible for generating detailed content for individual slides
    based on the slide structure from the planning phase.
    """
    
    def __init__(self):
        """Initialize the content agent with appropriate instructions."""
        
        # Define detailed instructions for the content agent
        instructions = """
        You are a presentation content specialist. Your job is to transform slide 
        structures into detailed, compelling slide content.
        
        For each slide:
        1. Create detailed content that expands on the provided content tokens
        2. Format content according to format tokens (bullet points, tables, etc.)
        3. Add presenter notes to help the presenter deliver the slide
        4. Maintain a consistent tone and style throughout the presentation
        
        Keep content concise and focused. Use markdown formatting where appropriate.
        Create visually balanced slides that follow good presentation principles.
        
        The content should be engaging, clear, and professional. Avoid jargon unless
        it's appropriate for the target audience.
        
        For HTML content, use basic HTML tags like <h1>, <h2>, <p>, <ul>, <li>, etc.
        """
        
        # Initialize the base agent
        super().__init__(
            name="Presentation Content Agent",
            instructions=instructions,
            output_type=SlideContent,
            temperature=0.3,
        )
    
    async def generate_slide_content(
        self,
        slide_structure: SlideStructure,
        extracted_content: str,
        context: Optional[Dict[str, Any]] = None
    ) -> SlideContent:
        """
        Generate detailed content for a slide.
        
        Args:
            slide_structure: The structure of the slide
            extracted_content: Relevant content extracted from the document
            context: Optional context to pass to the agent
            
        Returns:
            Detailed slide content
        """
        # Build a prompt for the agent
        prompt = f"""
        Generate detailed content for slide {slide_structure.slide_number}: '{slide_structure.title}'
        
        Content should incorporate these key points:
        {', '.join(slide_structure.content_tokens)}
        
        Format guidelines:
        {', '.join(slide_structure.format_tokens) if slide_structure.format_tokens else 'Use appropriate formatting for the content'}
        
        Design elements to consider:
        {', '.join(slide_structure.design_tokens) if slide_structure.design_tokens else 'Keep the design clean and professional'}
        
        Relevant document content:
        {extracted_content}
        
        Please generate HTML content for the slide and helpful presenter notes.
        """
        
        # Create context if not provided
        if context is None:
            context = {}
        
        # Add slide structure and content to context
        context.update({
            "slide_structure": slide_structure.model_dump(),
            "extracted_content": extracted_content
        })
        
        # Process with the agent
        return await self.process(prompt, context) 
"""
Planning agent for the presentation automator.
Analyzes document text and creates a structured presentation plan.
"""

from typing import Dict, Any, Optional

from ..models.schemas import PresentationPlan
from .base import BaseAgent
from ..utils.logging import setup_logger

# Create a logger
logger = setup_logger("planning_agent")


class PlanningAgent(BaseAgent[PresentationPlan]):
    """
    Agent responsible for analyzing document text and planning the
    presentation structure, including slides and their content.
    """
    
    def __init__(self):
        """Initialize the planning agent with appropriate instructions."""
        
        # Define detailed instructions for the planning agent
        instructions = """
        You are a presentation planning specialist. Your job is to analyze a document and
        create an optimal presentation structure from it.
        
        For each presentation:
        1. Extract a clear title based on the document content
        2. Determine an appropriate theme (business, educational, creative, etc.)
        3. Break down the content into logical slides
        4. For each slide, provide:
           - A clear, concise title
           - Key content tokens (important points to include)
           - Format tokens (how content should be structured)
           - Design tokens (visual elements to include)
        
        Keep slides focused on a single topic or point.
        Aim for 5-10 slides for most presentations (can vary based on content).
        Organize slides in a logical flow.
        
        The presentation should tell a cohesive story from beginning to end.
        """
        
        # Initialize the base agent
        super().__init__(
            name="Presentation Planning Agent",
            instructions=instructions,
            output_type=PresentationPlan,
            temperature=0.2,
        )
    
    async def create_presentation_plan(
        self, 
        document_text: str,
        context: Optional[Dict[str, Any]] = None
    ) -> PresentationPlan:
        """
        Create a presentation plan from document text.
        
        Args:
            document_text: The document text to analyze
            context: Optional context to pass to the agent
            
        Returns:
            A structured presentation plan
        """
        # Build a prompt for the agent
        prompt = f"""
        Create a presentation structure from this document:
        
        {document_text}
        
        Analyze the content carefully and identify the key points that should be
        included in the presentation. Follow a logical structure that best conveys
        the message of the document.
        """
        
        # Create context if not provided
        if context is None:
            context = {}
        
        # Add document to context
        context["document"] = document_text
        
        # Process with the agent
        return await self.process(prompt, context) 
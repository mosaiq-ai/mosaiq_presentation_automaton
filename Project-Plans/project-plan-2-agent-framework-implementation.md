# Project Plan 2: Agent Framework Implementation

## Overview

This project plan covers the implementation of the core agent framework for the Presentation Automator backend. It focuses on creating specialized agents using the OpenAI Agents SDK to handle different aspects of presentation generation, including planning the structure and generating content.

## Objectives

1. Implement a base agent class for common functionality
2. Create a planning agent to structure presentations
3. Implement a content agent to generate detailed slide content
4. Define schema models for structured agent outputs
5. Create tools for agents to use during processing
6. Implement unit tests for agent functionality

## Prerequisites

- Completion of Project Plan 1 (Setup and Core Infrastructure)
- OpenAI API key with access to GPT-4 or similar models
- Understanding of the OpenAI Agents SDK
- Familiarity with Pydantic models

## Deliverables

1. Base agent implementation with common functionality
2. Planning agent for determining presentation structure
3. Content agent for generating detailed content
4. Schema definitions for structured outputs
5. Tool implementations for agent use
6. Comprehensive tests for agent functionality

## Time Estimate

Approximately a week for a junior engineer.

## Detailed Implementation Steps

### Step 1: Create Schema Models for Agent Outputs

First, let's define the data structures that our agents will produce. Create a file at `src/models/schemas.py`:

```python
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
```

### Step 2: Create Base Agent Class

Create a base agent class that will handle common functionality for all agents. Create a file at `src/agents/base.py`:

```python
"""
Base agent implementation for the presentation automator.
Provides common functionality for all specialized agents.
"""

from typing import Any, Dict, List, Optional, Type, TypeVar, Generic
import logging
import os

from agents import Agent, Runner, function_tool, ModelSettings
from pydantic import BaseModel

from ..utils.logging import setup_logger

# Create a logger for the agents
logger = setup_logger("agents")

# Type variable for agent output types
T = TypeVar('T', bound=BaseModel)


class BaseAgent(Generic[T]):
    """
    Base class for all presentation generator agents.
    
    This provides common functionality for creating and running agents
    with the OpenAI Agents SDK.
    """
    
    def __init__(
        self,
        name: str,
        instructions: str,
        output_type: Type[T],
        model: str = "gpt-4o-2024-05-13",
        temperature: float = 0.2,
        tools: Optional[List[Any]] = None,
    ):
        """
        Initialize a base agent.
        
        Args:
            name: Name of the agent
            instructions: System instructions for the agent
            output_type: Pydantic model class for structured output
            model: OpenAI model to use
            temperature: Temperature for generation (0.0 to 1.0)
            tools: List of tools for the agent to use
        """
        self.name = name
        self.output_type = output_type
        
        # Create the underlying Agent from the OpenAI Agents SDK
        self.agent = Agent(
            name=name,
            instructions=instructions,
            model=model,
            model_settings=ModelSettings(
                temperature=temperature,
                top_p=0.95,
            ),
            tools=tools or [],
            output_type=output_type,
        )
        
        logger.info(f"Initialized agent: {name}")
    
    async def process(self, input_text: str, context: Optional[Dict[str, Any]] = None) -> T:
        """
        Process input with the agent and return the result.
        
        Args:
            input_text: The input text to process
            context: Optional context object to pass to the agent
            
        Returns:
            The structured output from the agent
        
        Raises:
            Exception: If the agent processing fails
        """
        logger.info(f"Running agent: {self.name}")
        
        try:
            # Ensure context is a dictionary if not provided
            if context is None:
                context = {}
            
            # Run the agent
            result = await Runner.run(
                self.agent,
                input_text,
                context=context,  # Must be passed as a named parameter
            )
            
            # Get the output and ensure it's the correct type
            output = result.final_output
            
            logger.info(f"Agent {self.name} completed successfully")
            return output
            
        except Exception as e:
            logger.error(f"Error in agent {self.name}: {str(e)}")
            raise
```

### Step 3: Create the Planning Agent

Implement the planning agent that will analyze document text and create a presentation structure. Create a file at `src/agents/planning_agent.py`:

```python
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
```

### Step 4: Create the Content Agent

Implement the content agent that will generate detailed content for each slide. Create a file at `src/agents/content_agent.py`:

```python
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
```

### Step 5: Create Utility Tools for Agents

Create utility functions that can be converted to tools for the agents. Create a file at `src/agents/tools.py`:

```python
"""
Tool implementations for agents to use during processing.
These tools help agents perform specific tasks during generation.
"""

from typing import List, Dict, Any, Optional
import re

from agents import function_tool
from agents.run_context import RunContextWrapper

from ..utils.logging import setup_logger

# Create a logger
logger = setup_logger("agent_tools")


def extract_key_points(text: str) -> str:
    """
    Extract key points from a text document.
    
    Args:
        text: The text to analyze
        
    Returns:
        A bullet-point list of key points
    """
    # This is a simple implementation
    # In a production system, this could use more sophisticated NLP
    
    # Split by paragraphs, sentences, or bullet points
    paragraphs = re.split(r'\n\s*\n', text)
    
    # Identify potential key points
    key_points = []
    for para in paragraphs:
        # Simplistic approach: consider shorter paragraphs as potential key points
        if 10 < len(para) < 200 and not para.startswith('#'):
            # Remove any bullet point markers
            cleaned = re.sub(r'^\s*[-*•]\s*', '', para)
            key_points.append(cleaned.strip())
    
    # Limit to top points
    top_points = key_points[:5] if len(key_points) > 5 else key_points
    
    # Format as bullet points
    formatted_points = "\n".join([f"- {point}" for point in top_points])
    
    return formatted_points


def extract_key_points_with_context(ctx: RunContextWrapper, text: Optional[str] = None) -> str:
    """
    Extract key points from a text document with context awareness.
    
    Args:
        ctx: Context wrapper containing shared context
        text: The text to analyze (falls back to document in context if not provided)
        
    Returns:
        A bullet-point list of key points
    """
    # Access context information
    context = ctx.context if ctx and hasattr(ctx, 'context') else {}
    
    # Use provided text or fall back to document in context
    doc_text = text or context.get('document', '')
    
    # Extract key points from the text
    points = extract_key_points(doc_text)
    
    # Log tool usage if context available
    if context:
        if 'tool_usage' not in context:
            context['tool_usage'] = {}
        tool_name = 'extract_key_points'
        context['tool_usage'][tool_name] = context['tool_usage'].get(tool_name, 0) + 1
        
        # Log some statistics for debugging
        context['tool_stats'] = context.get('tool_stats', {})
        context['tool_stats'][tool_name] = {
            'text_length': len(doc_text),
            'points_found': len(points.split('\n'))
        }
    
    return points


# Create function tools from the utility functions
extract_key_points_tool = function_tool(extract_key_points)
extract_key_points_with_context_tool = function_tool(extract_key_points_with_context)
```

### Step 6: Create the Presentation Generator Orchestrator

Create the main presentation generator that coordinates the agents. Create a file at `src/agents/presentation_generator.py`:

```python
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
```

### Step 7: Create Agent Module Init File

Create `src/agents/__init__.py` to organize exports:

```python
"""
Agent implementations for the presentation automator.
"""

from .base import BaseAgent
from .planning_agent import PlanningAgent
from .content_agent import ContentAgent
from .presentation_generator import PresentationGenerator
from .tools import extract_key_points_tool, extract_key_points_with_context_tool

__all__ = [
    'BaseAgent',
    'PlanningAgent',
    'ContentAgent',
    'PresentationGenerator',
    'extract_key_points_tool',
    'extract_key_points_with_context_tool',
]
```

### Step 8: Implement API Endpoint for Presentation Generation

Add a presentation generation endpoint to the API. Create a file at `src/api/router.py`:

```python
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
```

### Step 9: Update Main API Module

Update the main API module to include the router. In `src/api/app.py`, add these imports and code:

```python
# Add this import
from .router import router as generation_router

# ... existing code ...

# Add this line after creating the FastAPI app and before the root endpoint
app.include_router(generation_router)
```

### Step 10: Create Tests for Agents

Create tests for the agents. Create a file at `tests/test_agents.py`:

```python
"""
Tests for the agent components of the presentation automator.
"""

import pytest
import os
from unittest.mock import patch, MagicMock

from src.models.schemas import PresentationPlan, SlideStructure, SlideContent, Presentation
from src.agents.planning_agent import PlanningAgent
from src.agents.content_agent import ContentAgent
from src.agents.presentation_generator import PresentationGenerator

# Sample document text for testing
SAMPLE_TEXT = """
# Project Plan: Modernizing Our Company Website

## Introduction
Our company website is outdated and needs a modern redesign to better serve our customers and reflect our brand values.

## Objectives
- Improve user experience
- Increase conversion rates
- Modernize the visual design
- Enhance mobile responsiveness
- Improve page load speed

## Timeline
- Phase 1: Research and Planning (2 weeks)
- Phase 2: Design (3 weeks)
- Phase 3: Development (6 weeks)
- Phase 4: Testing (2 weeks)
- Phase 5: Launch (1 week)
"""

# Check if OpenAI API key is set
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
SKIP_API_TESTS = not OPENAI_API_KEY

# Mock presentation plan for testing without API
MOCK_PRESENTATION_PLAN = PresentationPlan(
    title="Website Modernization Project",
    theme="business",
    slides=[
        SlideStructure(
            slide_number=1,
            title="Introduction",
            content_tokens=["Project overview", "Current issues"],
            format_tokens=["Title slide"],
            design_tokens=["Modern layout"]
        ),
        SlideStructure(
            slide_number=2,
            title="Objectives",
            content_tokens=["Improve UX", "Increase conversion rates", "Modern design"],
            format_tokens=["Bullet points"],
            design_tokens=["Icons"]
        )
    ]
)

# Mock slide content for testing
MOCK_SLIDE_CONTENT = SlideContent(
    slide_number=1,
    title="Introduction",
    content="<h1>Introduction</h1><p>Our company website is outdated and needs a modern redesign</p>",
    notes="Emphasize the importance of the redesign"
)


@pytest.mark.skipif(SKIP_API_TESTS, reason="OpenAI API key not set")
@pytest.mark.asyncio
async def test_planning_agent():
    """Test the planning agent with real API calls."""
    planning_agent = PlanningAgent()
    plan = await planning_agent.create_presentation_plan(SAMPLE_TEXT)
    
    assert isinstance(plan, PresentationPlan)
    assert plan.title
    assert plan.theme
    assert len(plan.slides) > 0
    assert plan.slides[0].title
    assert len(plan.slides[0].content_tokens) > 0


@pytest.mark.skipif(SKIP_API_TESTS, reason="OpenAI API key not set")
@pytest.mark.asyncio
async def test_content_agent():
    """Test the content agent with real API calls."""
    content_agent = ContentAgent()
    slide_structure = SlideStructure(
        slide_number=1,
        title="Introduction",
        content_tokens=["Project overview", "Current issues"],
        format_tokens=["Title slide"],
        design_tokens=["Modern layout"]
    )
    
    slide_content = await content_agent.generate_slide_content(
        slide_structure,
        SAMPLE_TEXT
    )
    
    assert isinstance(slide_content, SlideContent)
    assert slide_content.slide_number == 1
    assert slide_content.title == "Introduction"
    assert len(slide_content.content) > 0


@pytest.mark.skipif(SKIP_API_TESTS, reason="OpenAI API key not set")
@pytest.mark.asyncio
async def test_presentation_generator():
    """Test the presentation generator with real API calls."""
    generator = PresentationGenerator()
    presentation = await generator.generate_from_text(SAMPLE_TEXT)
    
    assert isinstance(presentation, Presentation)
    assert presentation.title
    assert presentation.theme
    assert len(presentation.slides) > 0


@pytest.mark.asyncio
async def test_planning_agent_mock():
    """Test the planning agent with mocked responses."""
    with patch("src.agents.base.Runner.run") as mock_run:
        # Configure the mock
        mock_result = MagicMock()
        mock_result.final_output = MOCK_PRESENTATION_PLAN
        mock_run.return_value = mock_result
        
        # Create and use the agent
        planning_agent = PlanningAgent()
        plan = await planning_agent.create_presentation_plan(SAMPLE_TEXT)
        
        # Verify the result
        assert plan == MOCK_PRESENTATION_PLAN
        assert len(plan.slides) == 2
        assert plan.slides[0].title == "Introduction"


@pytest.mark.asyncio
async def test_content_agent_mock():
    """Test the content agent with mocked responses."""
    with patch("src.agents.base.Runner.run") as mock_run:
        # Configure the mock
        mock_result = MagicMock()
        mock_result.final_output = MOCK_SLIDE_CONTENT
        mock_run.return_value = mock_result
        
        # Create and use the agent
        content_agent = ContentAgent()
        slide_structure = MOCK_PRESENTATION_PLAN.slides[0]
        
        slide_content = await content_agent.generate_slide_content(
            slide_structure,
            SAMPLE_TEXT
        )
        
        # Verify the result
        assert slide_content == MOCK_SLIDE_CONTENT
        assert slide_content.title == "Introduction"
```

### Step 11: Test the API Endpoint

Create a test for the generation API endpoint. Create a file at `tests/test_api.py`:

```python
"""
Tests for the API endpoints.
"""

import pytest
import os
from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock

from src.api.app import app
from src.models.schemas import Presentation, SlideContent

client = TestClient(app)

# Check if OpenAI API key is set
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
SKIP_API_TESTS = not OPENAI_API_KEY

# Sample document text for testing
SAMPLE_TEXT = """
# Project Plan: Modernizing Our Company Website

## Introduction
Our company website is outdated and needs a modern redesign.
"""

# Mock presentation for testing
MOCK_PRESENTATION = Presentation(
    title="Website Modernization Project",
    theme="business",
    slides=[
        SlideContent(
            slide_number=1,
            title="Introduction",
            content="<h1>Introduction</h1><p>Our company website is outdated and needs a modern redesign</p>",
            notes="Speaker notes here"
        ),
        SlideContent(
            slide_number=2,
            title="Objectives",
            content="<h1>Objectives</h1><ul><li>Improve UX</li><li>Increase conversion rates</li></ul>",
            notes=""
        )
    ]
)


def test_generate_endpoint_mock():
    """Test the generate endpoint with mocked generator."""
    with patch("src.api.router.generator.generate_from_text") as mock_generate:
        # Configure the mock
        mock_generate.return_value = MOCK_PRESENTATION
        
        # Make the request
        response = client.post(
            "/api/generate",
            json={"document_text": SAMPLE_TEXT}
        )
        
        # Verify the response
        assert response.status_code == 200
        data = response.json()
        assert data["presentation"]["title"] == "Website Modernization Project"
        assert len(data["presentation"]["slides"]) == 2
        assert "metadata" in data


@pytest.mark.skipif(SKIP_API_TESTS, reason="OpenAI API key not set")
def test_generate_endpoint_real():
    """Test the generate endpoint with real API calls."""
    # Make the request
    response = client.post(
        "/api/generate",
        json={"document_text": SAMPLE_TEXT}
    )
    
    # Verify the response
    assert response.status_code == 200
    data = response.json()
    assert "presentation" in data
    assert "title" in data["presentation"]
    assert "slides" in data["presentation"]
    assert len(data["presentation"]["slides"]) > 0
    assert "metadata" in data
```

## Testing Instructions

To verify that the agent framework is working correctly:

1. Ensure that your OpenAI API key is correctly set in your `.env` file
2. Run the server using `./run.sh`
3. Use the API endpoint to generate a presentation:
   ```bash
   curl -X POST http://localhost:8000/api/generate \
     -H "Content-Type: application/json" \
     -d '{"document_text": "# Project Overview\n\nThis is a sample project document. It discusses the key aspects of our new initiative."}'
   ```
4. Verify that you receive a properly structured presentation as a response
5. Run the tests with `pytest tests/test_agents.py` to check the agent functionality
6. If you have a valid OpenAI API key, the tests with real API calls should pass; otherwise, only the mock tests will run

## Troubleshooting

If you encounter issues:

1. Check that your OpenAI API key is valid and correctly set in the `.env` file
2. Ensure that the selected model in the agents is available in your OpenAI account
3. Check the logs for detailed error messages
4. Try increasing the timeout for API calls if you're experiencing timeouts
5. For testing without an API key, ensure all the mock tests are passing

## Next Steps

After completing this project plan, you should have a functional agent framework that can:
- Analyze document text to create a structured presentation plan
- Generate detailed content for each slide
- Work with tools to enhance the generation process
- Provide structured output via the API

You're now ready to proceed to Project Plan 3, which will focus on implementing context sharing between agents for more advanced functionality. 
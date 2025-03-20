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
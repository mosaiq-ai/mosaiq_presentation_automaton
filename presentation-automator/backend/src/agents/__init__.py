"""
Agent implementations for the presentation automator.
"""

from .base import BaseAgent
from .planning_agent import PlanningAgent
from .content_agent import ContentAgent
from .presentation_generator import PresentationGenerator
from .tools import extract_key_points_tool, extract_key_points_with_context_tool

# Create singleton instances
planning_agent = PlanningAgent()
content_agent = ContentAgent()

def get_planning_agent() -> PlanningAgent:
    """Get the singleton instance of the planning agent."""
    global planning_agent
    return planning_agent

def get_content_agent() -> ContentAgent:
    """Get the singleton instance of the content agent."""
    global content_agent
    return content_agent

__all__ = [
    'BaseAgent',
    'PlanningAgent',
    'ContentAgent',
    'PresentationGenerator',
    'extract_key_points_tool',
    'extract_key_points_with_context_tool',
    'planning_agent',
    'content_agent',
    'get_planning_agent',
    'get_content_agent',
] 
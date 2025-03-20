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
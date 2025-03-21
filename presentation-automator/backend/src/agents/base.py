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
        model: str = "gpt-4o",
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
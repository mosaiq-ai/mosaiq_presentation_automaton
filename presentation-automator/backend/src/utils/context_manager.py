"""
Context manager for better agent communication and tracking.

This module provides utilities for managing context sharing between agents,
tracking generation statistics, and monitoring tool usage.
"""

from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional, Set

from pydantic import BaseModel, Field


class StageStatus(str, Enum):
    """Status of a generation stage."""
    NOT_STARTED = "not_started"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"


class GenerationStats(BaseModel):
    """Model for tracking generation statistics."""
    start_time: datetime = Field(default_factory=datetime.now)
    end_time: Optional[datetime] = None
    total_tokens_used: int = 0
    prompt_tokens: int = 0
    completion_tokens: int = 0
    total_api_calls: int = 0
    
    # Track various metrics
    tools_used: Dict[str, int] = Field(default_factory=dict)
    stages_completed: List[str] = Field(default_factory=list)
    errors_encountered: List[Dict[str, Any]] = Field(default_factory=list)
    
    def record_tool_usage(self, tool_name: str) -> None:
        """Record usage of a tool.
        
        Args:
            tool_name: Name of the tool being used
        """
        if tool_name in self.tools_used:
            self.tools_used[tool_name] += 1
        else:
            self.tools_used[tool_name] = 1
        
        # Increment API call count
        self.total_api_calls += 1
    
    def add_tokens(self, prompt_tokens: int, completion_tokens: int) -> None:
        """Add token usage to the stats.
        
        Args:
            prompt_tokens: Number of prompt tokens used
            completion_tokens: Number of completion tokens used
        """
        self.prompt_tokens += prompt_tokens
        self.completion_tokens += completion_tokens
        self.total_tokens_used += prompt_tokens + completion_tokens
    
    def complete(self) -> None:
        """Mark generation as complete and record end time."""
        self.end_time = datetime.now()
    
    def record_error(self, stage: str, error: str, details: Optional[Dict[str, Any]] = None) -> None:
        """Record an error that occurred during generation.
        
        Args:
            stage: The stage where the error occurred
            error: Error message
            details: Additional error details
        """
        self.errors_encountered.append({
            "stage": stage,
            "error": error,
            "timestamp": datetime.now(),
            "details": details or {}
        })


class GenerationContext(BaseModel):
    """Context class for sharing data between agent components."""
    
    # Generation metadata
    generation_id: str
    document_source: Optional[str] = None
    document_statistics: Dict[str, Any] = Field(default_factory=dict)
    
    # Content tracking
    extracted_content: Dict[str, Any] = Field(default_factory=dict)
    processed_sections: List[Dict[str, Any]] = Field(default_factory=list)
    
    # Generation progress tracking
    stats: GenerationStats = Field(default_factory=GenerationStats)
    stage_status: Dict[str, StageStatus] = Field(default_factory=dict)
    
    # Agent communication
    shared_data: Dict[str, Any] = Field(default_factory=dict)
    agent_outputs: Dict[str, Any] = Field(default_factory=dict)
    
    def set_document_statistics(self, statistics: Dict[str, Any]) -> None:
        """Set document statistics.
        
        Args:
            statistics: Statistics about the processed document
        """
        self.document_statistics = statistics
    
    def add_extracted_content(self, content_type: str, content: Any) -> None:
        """Add extracted content to the context.
        
        Args:
            content_type: Type of content (e.g., 'sections', 'keywords')
            content: The extracted content
        """
        self.extracted_content[content_type] = content
    
    def get_extracted_content(self, content_type: str) -> Any:
        """Get extracted content from the context.
        
        Args:
            content_type: Type of content to retrieve
            
        Returns:
            The extracted content or None if not found
        """
        return self.extracted_content.get(content_type)
    
    def set_stage_status(self, stage: str, status: StageStatus) -> None:
        """Set the status of a processing stage.
        
        Args:
            stage: Name of the stage
            status: Status to set
        """
        self.stage_status[stage] = status
        
        # If completed, add to completed stages list
        if status == StageStatus.COMPLETED and stage not in self.stats.stages_completed:
            self.stats.stages_completed.append(stage)
    
    def is_stage_completed(self, stage: str) -> bool:
        """Check if a stage is completed.
        
        Args:
            stage: Name of the stage to check
            
        Returns:
            True if the stage is completed, False otherwise
        """
        return self.stage_status.get(stage) == StageStatus.COMPLETED
    
    def share_data(self, key: str, value: Any) -> None:
        """Share data between agents.
        
        Args:
            key: Key to store the data under
            value: Data to share
        """
        self.shared_data[key] = value
    
    def get_shared_data(self, key: str, default: Any = None) -> Any:
        """Get shared data by key.
        
        Args:
            key: Key of the data to retrieve
            default: Default value if key not found
            
        Returns:
            The shared data or default if not found
        """
        return self.shared_data.get(key, default)
    
    def record_agent_output(self, agent_name: str, output: Any) -> None:
        """Record output from an agent.
        
        Args:
            agent_name: Name of the agent
            output: Output from the agent
        """
        self.agent_outputs[agent_name] = output
    
    def get_agent_output(self, agent_name: str) -> Optional[Any]:
        """Get output from an agent.
        
        Args:
            agent_name: Name of the agent
            
        Returns:
            The agent's output or None if not found
        """
        return self.agent_outputs.get(agent_name)
    
    def record_tool_usage(self, tool_name: str) -> None:
        """Record usage of a tool.
        
        Args:
            tool_name: Name of the tool being used
        """
        self.stats.record_tool_usage(tool_name)
    
    def add_tokens(self, prompt_tokens: int, completion_tokens: int) -> None:
        """Add token usage to the context stats.
        
        Args:
            prompt_tokens: Number of prompt tokens used
            completion_tokens: Number of completion tokens used
        """
        self.stats.add_tokens(prompt_tokens, completion_tokens)
    
    def complete_generation(self) -> GenerationStats:
        """Mark generation as complete and return stats.
        
        Returns:
            The final generation statistics
        """
        self.stats.complete()
        return self.stats 
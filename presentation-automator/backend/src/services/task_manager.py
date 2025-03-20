"""
Asynchronous task system for long-running operations.

This module provides a task manager for handling asynchronous operations,
such as document processing and presentation generation.
"""

import asyncio
import traceback
import uuid
from datetime import datetime
from enum import Enum
from typing import Any, Callable, Dict, List, Optional, Set, TypeVar, Union, Awaitable

from loguru import logger
from pydantic import BaseModel, Field


class TaskStatus(str, Enum):
    """Status of an asynchronous task."""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class TaskResult(BaseModel):
    """Result of an asynchronous task."""
    task_id: str
    status: TaskStatus
    created_at: datetime = Field(default_factory=datetime.now)
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    progress: float = 0.0
    message: str = ""
    result: Optional[Any] = None
    error: Optional[str] = None
    traceback: Optional[str] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)


T = TypeVar('T')
TaskFunction = Callable[[str, Dict[str, Any]], Awaitable[T]]
ProgressCallback = Callable[[str, float, str], None]


class TaskManager:
    """Manager for asynchronous tasks."""
    
    def __init__(self, max_workers: int = 5):
        """
        Initialize the task manager.
        
        Args:
            max_workers: Maximum number of concurrent tasks
        """
        self.max_workers = max_workers
        self.tasks: Dict[str, asyncio.Task] = {}
        self.results: Dict[str, TaskResult] = {}
        self.semaphore = asyncio.Semaphore(max_workers)
        self.running = False
        self.processing_task: Optional[asyncio.Task] = None
        self.progress_callbacks: Dict[str, List[ProgressCallback]] = {}
        logger.info(f"Task manager initialized with {max_workers} max workers")
    
    async def start(self) -> None:
        """Start the task manager."""
        if self.running:
            return
        
        self.running = True
        logger.info("Task manager started")
    
    async def stop(self) -> None:
        """Stop the task manager and cancel all running tasks."""
        if not self.running:
            return
        
        self.running = False
        
        # Cancel all running tasks
        for task_id, task in list(self.tasks.items()):
            if not task.done():
                logger.info(f"Cancelling task {task_id}")
                task.cancel()
                
                # Update task result
                if task_id in self.results:
                    self.results[task_id].status = TaskStatus.CANCELLED
                    self.results[task_id].completed_at = datetime.now()
                    self.results[task_id].message = "Task cancelled due to shutdown"
        
        # Wait for tasks to complete cancellation
        if self.tasks:
            await asyncio.gather(*list(self.tasks.values()), return_exceptions=True)
        
        logger.info("Task manager stopped")
    
    async def submit_task(
        self, 
        func: TaskFunction, 
        args: Dict[str, Any] = None,
        task_id: Optional[str] = None,
        metadata: Dict[str, Any] = None
    ) -> str:
        """
        Submit a task for asynchronous execution.
        
        Args:
            func: Async function to execute
            args: Arguments to pass to the function
            task_id: Optional task ID (generated if not provided)
            metadata: Optional metadata for the task
            
        Returns:
            Task ID for tracking the task
        """
        if not self.running:
            raise RuntimeError("Task manager is not running")
        
        # Generate task ID if not provided
        if task_id is None:
            task_id = str(uuid.uuid4())
        
        # Initialize task result
        result = TaskResult(
            task_id=task_id,
            status=TaskStatus.PENDING,
            message="Task pending execution",
            metadata=metadata or {}
        )
        self.results[task_id] = result
        
        # Create progress callback for this task
        self.progress_callbacks[task_id] = []
        
        # Start the task
        task = asyncio.create_task(
            self._execute_task(task_id, func, args or {})
        )
        self.tasks[task_id] = task
        
        logger.info(f"Task {task_id} submitted")
        return task_id
    
    async def _execute_task(
        self, 
        task_id: str, 
        func: TaskFunction, 
        args: Dict[str, Any]
    ) -> None:
        """
        Execute a task with error handling and semaphore control.
        
        Args:
            task_id: ID of the task
            func: Function to execute
            args: Arguments for the function
        """
        # Wait for semaphore (limit concurrent tasks)
        async with self.semaphore:
            # Update task status
            self.results[task_id].status = TaskStatus.RUNNING
            self.results[task_id].started_at = datetime.now()
            self.results[task_id].message = "Task running"
            
            try:
                # Execute the task function
                result = await func(task_id, args)
                
                # Update task result on success
                self.results[task_id].status = TaskStatus.COMPLETED
                self.results[task_id].completed_at = datetime.now()
                self.results[task_id].progress = 1.0
                self.results[task_id].message = "Task completed successfully"
                self.results[task_id].result = result
                
                logger.info(f"Task {task_id} completed successfully")
                
            except asyncio.CancelledError:
                # Task was cancelled
                self.results[task_id].status = TaskStatus.CANCELLED
                self.results[task_id].completed_at = datetime.now()
                self.results[task_id].message = "Task cancelled"
                
                logger.info(f"Task {task_id} cancelled")
                
            except Exception as e:
                # Task failed with an exception
                tb_str = traceback.format_exc()
                
                self.results[task_id].status = TaskStatus.FAILED
                self.results[task_id].completed_at = datetime.now()
                self.results[task_id].message = "Task failed with an error"
                self.results[task_id].error = str(e)
                self.results[task_id].traceback = tb_str
                
                logger.error(f"Task {task_id} failed: {e}\n{tb_str}")
            
            finally:
                # Clean up
                if task_id in self.tasks:
                    del self.tasks[task_id]
                
                # Clean up progress callbacks
                if task_id in self.progress_callbacks:
                    del self.progress_callbacks[task_id]
    
    def get_task_status(self, task_id: str) -> Optional[TaskResult]:
        """
        Get the status of a task.
        
        Args:
            task_id: ID of the task to check
            
        Returns:
            TaskResult for the task or None if not found
        """
        return self.results.get(task_id)
    
    def update_progress(self, task_id: str, progress: float, message: str = "") -> None:
        """
        Update the progress of a task.
        
        Args:
            task_id: ID of the task
            progress: Progress value (0.0 to 1.0)
            message: Optional progress message
        """
        if task_id not in self.results:
            logger.warning(f"Attempted to update progress for unknown task {task_id}")
            return
        
        # Validate progress value
        progress = max(0.0, min(1.0, progress))
        
        # Update progress in task result
        self.results[task_id].progress = progress
        if message:
            self.results[task_id].message = message
        
        # Notify progress callbacks
        if task_id in self.progress_callbacks:
            for callback in self.progress_callbacks[task_id]:
                try:
                    callback(task_id, progress, message)
                except Exception as e:
                    logger.error(f"Error in progress callback: {e}")
    
    def add_progress_callback(self, task_id: str, callback: ProgressCallback) -> None:
        """
        Add a progress callback for a task.
        
        Args:
            task_id: ID of the task
            callback: Function to call on progress updates
        """
        if task_id not in self.progress_callbacks:
            self.progress_callbacks[task_id] = []
        
        self.progress_callbacks[task_id].append(callback)
    
    def get_all_tasks(self) -> Dict[str, TaskResult]:
        """
        Get all task results.
        
        Returns:
            Dictionary of task IDs to TaskResults
        """
        return self.results.copy()
    
    def get_active_tasks(self) -> Dict[str, TaskResult]:
        """
        Get all active (pending or running) tasks.
        
        Returns:
            Dictionary of task IDs to TaskResults for active tasks
        """
        return {
            task_id: result
            for task_id, result in self.results.items()
            if result.status in (TaskStatus.PENDING, TaskStatus.RUNNING)
        }
    
    def purge_completed_tasks(self, max_age_seconds: int = 3600) -> int:
        """
        Remove completed, failed, or cancelled tasks from history.
        
        Args:
            max_age_seconds: Maximum age in seconds to keep completed tasks
            
        Returns:
            Number of tasks purged
        """
        now = datetime.now()
        to_remove = []
        
        for task_id, result in self.results.items():
            if result.status not in (TaskStatus.PENDING, TaskStatus.RUNNING):
                # Task is completed, failed, or cancelled
                if result.completed_at:
                    age = (now - result.completed_at).total_seconds()
                    if age > max_age_seconds:
                        to_remove.append(task_id)
        
        # Remove the tasks
        for task_id in to_remove:
            del self.results[task_id]
        
        return len(to_remove)


# Create a singleton instance
task_manager = TaskManager()

# Convenience functions for direct module use
async def start_task_manager() -> None:
    """Start the task manager."""
    await task_manager.start()

async def stop_task_manager() -> None:
    """Stop the task manager."""
    await task_manager.stop()

async def submit_task(func: TaskFunction, args: Dict[str, Any] = None, **kwargs) -> str:
    """Submit a task to the task manager."""
    return await task_manager.submit_task(func, args, **kwargs)

def get_task_status(task_id: str) -> Optional[TaskResult]:
    """Get the status of a task."""
    return task_manager.get_task_status(task_id)

def update_task_progress(task_id: str, progress: float, message: str = "") -> None:
    """Update the progress of a task."""
    task_manager.update_progress(task_id, progress, message) 
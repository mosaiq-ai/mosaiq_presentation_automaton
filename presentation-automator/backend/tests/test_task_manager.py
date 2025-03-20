"""
Test module for the task manager service.
"""

import asyncio
import os
import sys
import time
import pytest

# Add the src directory to the path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from src.services.task_manager import task_manager, submit_task, get_task_status, TaskStatus


@pytest.mark.asyncio
async def test_task_manager():
    """Test the task manager with a simple task."""
    
    # Define a simple async task
    async def simple_task(task_id: str, args: dict):
        """A simple task that sleeps and returns a result."""
        # Get the sleep time from args or use default
        sleep_time = args.get("sleep_time", 1)
        
        # Simulate work with sleep
        await asyncio.sleep(sleep_time)
        
        # Return a result
        return {
            "task_id": task_id,
            "result": "Task completed successfully",
            "processed_args": args
        }
    
    # Start the task manager
    await task_manager.start()
    
    try:
        # Submit a task
        task_id = await submit_task(simple_task, {"sleep_time": 0.5, "test_arg": "test_value"})
        
        # Check initial status
        status = get_task_status(task_id)
        assert status is not None
        assert status.task_id == task_id
        assert status.status in (TaskStatus.PENDING, TaskStatus.RUNNING)
        
        # Wait for the task to complete
        for _ in range(10):
            status = get_task_status(task_id)
            if status.status == TaskStatus.COMPLETED:
                break
            await asyncio.sleep(0.2)
        
        # Check final status
        status = get_task_status(task_id)
        assert status.status == TaskStatus.COMPLETED
        assert status.result is not None
        assert status.result["task_id"] == task_id
        assert status.result["result"] == "Task completed successfully"
        assert status.result["processed_args"]["test_arg"] == "test_value"
        
        # Check task progress
        assert status.progress == 1.0
        
    finally:
        # Stop the task manager
        await task_manager.stop()


if __name__ == "__main__":
    """Run the test directly."""
    asyncio.run(test_task_manager())
    print("Task manager test passed!") 
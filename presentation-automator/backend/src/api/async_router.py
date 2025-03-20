"""
Asynchronous API router for handling long-running operations.

This module defines the API endpoints for asynchronous generation
and task management with server-sent events for progress tracking.
"""

import asyncio
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, BackgroundTasks, Depends, File, Form, HTTPException, UploadFile
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from sse_starlette.sse import EventSourceResponse

from ..config.settings import get_settings, Settings
from ..models.schemas import GenerationRequest, GenerationResponse, Presentation
from ..services.document_processor import document_processor
from ..services.presentation_service import presentation_service
from ..services.task_manager import (
    task_manager, 
    get_task_status, 
    TaskStatus, 
    TaskResult
)
from ..utils.logging import app_logger


# Create async router
router = APIRouter(
    prefix="/api",
    tags=["Async Generation"],
)


class AsyncGenerationRequest(BaseModel):
    """Request model for asynchronous presentation generation."""
    document_text: str
    options: Dict[str, Any] = {}


class FileGenerationRequest(BaseModel):
    """Request model for file-based asynchronous generation."""
    options: Dict[str, Any] = {}


class TaskStatusResponse(BaseModel):
    """Response model for task status."""
    task_id: str
    status: str
    progress: float
    message: str
    created_at: str
    started_at: Optional[str] = None
    completed_at: Optional[str] = None
    error: Optional[str] = None


async def _generate_presentation_task(task_id: str, args: Dict[str, Any]) -> Presentation:
    """
    Background task for generating a presentation.
    
    Args:
        task_id: ID of the task
        args: Arguments from the request
    
    Returns:
        The generated presentation
    """
    app_logger.info(f"Starting async presentation generation for task {task_id}")
    
    request = args.get("request")
    if not request:
        raise ValueError("Request data is missing")
    
    # Generate the presentation
    response = await presentation_service.handle_generation_request(
        request=request,
        task_id=task_id
    )
    
    return response.presentation


async def _generate_from_file_task(task_id: str, args: Dict[str, Any]) -> Presentation:
    """
    Background task for generating a presentation from a file.
    
    Args:
        task_id: ID of the task
        args: Arguments from the request
    
    Returns:
        The generated presentation
    """
    app_logger.info(f"Starting async file-based presentation generation for task {task_id}")
    
    file_content = args.get("file_content")
    file_name = args.get("file_name")
    options = args.get("options", {})
    
    if not file_content or not file_name:
        raise ValueError("File content or name is missing")
    
    # Process the file
    file_extension = "." + file_name.split(".")[-1] if "." in file_name else None
    
    # Extract text from the document
    text, stats = await document_processor.process_document(
        file_content=file_content,
        file_extension=file_extension
    )
    
    # Create a request object
    request = GenerationRequest(
        document_text=text,
        options=options
    )
    
    # Generate the presentation
    response = await presentation_service.handle_generation_request(
        request=request,
        task_id=task_id
    )
    
    return response.presentation


@router.post("/generate-async", response_model=Dict[str, str])
async def generate_async(
    request: AsyncGenerationRequest,
    background_tasks: BackgroundTasks,
    settings: Settings = Depends(get_settings)
) -> JSONResponse:
    """
    Start an asynchronous presentation generation task.
    
    Args:
        request: Generation request
        background_tasks: FastAPI background tasks
        settings: Application settings
    
    Returns:
        JSON response with task ID
    """
    if not settings.api.openai_api_key:
        raise HTTPException(
            status_code=500,
            detail="OpenAI API key is not configured"
        )
    
    # Ensure task manager is running
    if not task_manager.running:
        await task_manager.start()
    
    # Create a GenerationRequest
    gen_request = GenerationRequest(
        document_text=request.document_text,
        options=request.options
    )
    
    # Submit the task
    task_id = await task_manager.submit_task(
        _generate_presentation_task,
        {"request": gen_request}
    )
    
    return JSONResponse({
        "task_id": task_id,
        "message": "Presentation generation started"
    })


@router.post("/generate-from-file-async", response_model=Dict[str, str])
async def generate_from_file_async(
    file: UploadFile = File(...),
    options: str = Form("{}"),
    settings: Settings = Depends(get_settings)
) -> JSONResponse:
    """
    Start an asynchronous presentation generation from a file.
    
    Args:
        file: Uploaded document file
        options: JSON string of generation options
        settings: Application settings
    
    Returns:
        JSON response with task ID
    """
    if not settings.api.openai_api_key:
        raise HTTPException(
            status_code=500,
            detail="OpenAI API key is not configured"
        )
    
    # Ensure task manager is running
    if not task_manager.running:
        await task_manager.start()
    
    # Read file content
    file_content = await file.read()
    
    # Parse options
    import json
    try:
        options_dict = json.loads(options)
    except json.JSONDecodeError:
        options_dict = {}
    
    # Submit the task
    task_id = await task_manager.submit_task(
        _generate_from_file_task,
        {
            "file_content": file_content,
            "file_name": file.filename,
            "options": options_dict
        }
    )
    
    return JSONResponse({
        "task_id": task_id,
        "message": "File-based presentation generation started"
    })


@router.get("/generation/{task_id}/status", response_model=TaskStatusResponse)
async def get_generation_status(task_id: str) -> TaskStatusResponse:
    """
    Get the status of a generation task.
    
    Args:
        task_id: ID of the task to check
    
    Returns:
        Task status details
    """
    result = get_task_status(task_id)
    
    if not result:
        raise HTTPException(
            status_code=404,
            detail=f"Task {task_id} not found"
        )
    
    # Convert datetime objects to strings for JSON serialization
    return TaskStatusResponse(
        task_id=result.task_id,
        status=result.status,
        progress=result.progress,
        message=result.message,
        created_at=result.created_at.isoformat(),
        started_at=result.started_at.isoformat() if result.started_at else None,
        completed_at=result.completed_at.isoformat() if result.completed_at else None,
        error=result.error
    )


@router.get("/generation/{task_id}/result")
async def get_generation_result(task_id: str) -> Dict[str, Any]:
    """
    Get the result of a completed generation task.
    
    Args:
        task_id: ID of the task
    
    Returns:
        Generated presentation or error message
    """
    result = get_task_status(task_id)
    
    if not result:
        raise HTTPException(
            status_code=404,
            detail=f"Task {task_id} not found"
        )
    
    if result.status != TaskStatus.COMPLETED:
        raise HTTPException(
            status_code=400,
            detail=f"Task {task_id} is not completed (status: {result.status})"
        )
    
    if not result.result:
        raise HTTPException(
            status_code=500,
            detail=f"No result available for task {task_id}"
        )
    
    # Return the presentation
    presentation = result.result
    return presentation.dict()


@router.get("/generation/{task_id}/events")
async def task_events(task_id: str) -> EventSourceResponse:
    """
    Server-sent events endpoint for real-time task progress updates.
    
    Args:
        task_id: ID of the task to monitor
    
    Returns:
        SSE response with progress updates
    """
    result = get_task_status(task_id)
    
    if not result:
        raise HTTPException(
            status_code=404,
            detail=f"Task {task_id} not found"
        )
    
    async def event_generator():
        """Generate SSE events for task progress."""
        # Send initial status
        yield {
            "event": "status",
            "data": {
                "task_id": result.task_id,
                "status": result.status,
                "progress": result.progress,
                "message": result.message,
            }
        }
        
        # Continue sending updates until task completes
        while True:
            # Check if task is still active
            current_result = get_task_status(task_id)
            if not current_result:
                # Task was deleted
                yield {
                    "event": "error",
                    "data": {"message": f"Task {task_id} no longer exists"}
                }
                break
            
            # Send status update
            yield {
                "event": "status",
                "data": {
                    "task_id": current_result.task_id,
                    "status": current_result.status,
                    "progress": current_result.progress,
                    "message": current_result.message,
                }
            }
            
            # Check if task is completed
            if current_result.status in (
                TaskStatus.COMPLETED, 
                TaskStatus.FAILED, 
                TaskStatus.CANCELLED
            ):
                yield {
                    "event": "complete",
                    "data": {
                        "task_id": current_result.task_id,
                        "status": current_result.status,
                        "message": current_result.message,
                    }
                }
                break
            
            # Wait before next update
            await asyncio.sleep(1)
    
    return EventSourceResponse(event_generator())


@router.get("/generations", response_model=List[TaskStatusResponse])
async def list_generations() -> List[TaskStatusResponse]:
    """
    List all generation tasks.
    
    Returns:
        List of task statuses
    """
    tasks = task_manager.get_all_tasks()
    
    return [
        TaskStatusResponse(
            task_id=result.task_id,
            status=result.status,
            progress=result.progress,
            message=result.message,
            created_at=result.created_at.isoformat(),
            started_at=result.started_at.isoformat() if result.started_at else None,
            completed_at=result.completed_at.isoformat() if result.completed_at else None,
            error=result.error
        )
        for result in tasks.values()
    ] 
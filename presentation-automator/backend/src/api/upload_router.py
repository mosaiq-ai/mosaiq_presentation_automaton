"""
API router for file upload handling.
Includes endpoints for uploading documents that will be processed for presentation generation.
"""

import os
import shutil
from datetime import datetime
from pathlib import Path
from typing import List, Optional
from uuid import uuid4

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status
from pydantic import BaseModel
from sqlalchemy.orm import Session

from ..middleware.auth import get_current_active_user
from ..models.database import User, get_db


# Configuration
UPLOAD_DIR = os.getenv("UPLOAD_DIR", "uploads")
MAX_UPLOAD_SIZE = int(os.getenv("MAX_UPLOAD_SIZE", "10485760"))  # 10MB default
ALLOWED_EXTENSIONS = {".pdf", ".docx", ".txt", ".md"}


# Create router
router = APIRouter(prefix="/api/upload", tags=["uploads"])


# Schema models
class UploadResponse(BaseModel):
    """Schema for upload responses."""
    
    filename: str
    file_id: str
    file_size: int
    content_type: str
    upload_time: str


# Ensure upload directory exists
def ensure_upload_dir():
    """Create the upload directory if it doesn't exist."""
    path = Path(UPLOAD_DIR)
    if not path.exists():
        path.mkdir(parents=True, exist_ok=True)
    return path


@router.post("", response_model=UploadResponse, status_code=status.HTTP_201_CREATED)
async def upload_file(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Upload a file for processing.
    
    Args:
        file: File to upload
        current_user: Current authenticated user
        db: Database session
        
    Returns:
        Upload information
        
    Raises:
        HTTPException: If file is too large, has an invalid extension, or upload fails
    """
    # Reset file position at the beginning to ensure we read the entire content
    await file.seek(0)
    
    # Read the entire file content
    content = await file.read()
    file_size = len(content)
    
    # Validate file size
    if file_size > MAX_UPLOAD_SIZE:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=f"File too large. Maximum size allowed is {MAX_UPLOAD_SIZE/1024/1024:.2f}MB"
        )
    
    # Validate file extension
    original_filename = file.filename
    extension = Path(original_filename).suffix.lower()
    
    if extension not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
            detail=f"Unsupported file type. Allowed types: {', '.join(ALLOWED_EXTENSIONS)}"
        )
    
    # Generate a unique file ID and determine save path
    file_id = str(uuid4())
    user_dir = ensure_upload_dir() / str(current_user.id)
    user_dir.mkdir(exist_ok=True)
    
    # Create a filename with the original extension
    save_filename = f"{file_id}{extension}"
    save_path = user_dir / save_filename
    
    # Save the file
    try:
        with open(save_path, "wb") as buffer:
            buffer.write(content)
    except Exception as e:
        # Clean up if an error occurs
        if save_path.exists():
            save_path.unlink()
        
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"File upload failed: {str(e)}"
        )
    
    return UploadResponse(
        filename=original_filename,
        file_id=file_id,
        file_size=file_size,
        content_type=file.content_type,
        upload_time=datetime.utcnow().isoformat()
    )


@router.get("", response_model=List[UploadResponse])
async def list_uploads(
    current_user: User = Depends(get_current_active_user)
):
    """
    List all uploaded files for the current user.
    
    Args:
        current_user: Current authenticated user
        
    Returns:
        List of uploaded files
    """
    # Create the user's upload directory if it doesn't exist
    user_dir = ensure_upload_dir() / str(current_user.id)
    if not user_dir.exists():
        return []
    
    # Get all files in the user's directory
    files = []
    for file_path in user_dir.iterdir():
        if file_path.is_file():
            file_id = file_path.stem
            extension = file_path.suffix
            file_size = file_path.stat().st_size
            
            # Placeholder values for information we don't store
            files.append(
                UploadResponse(
                    filename=f"upload_{file_id}{extension}",
                    file_id=file_id,
                    file_size=file_size,
                    content_type="application/octet-stream",
                    upload_time=datetime.fromtimestamp(file_path.stat().st_mtime).isoformat()
                )
            )
    
    return files


@router.delete("/{file_id}")
async def delete_upload(
    file_id: str,
    current_user: User = Depends(get_current_active_user)
):
    """
    Delete an uploaded file.
    
    Args:
        file_id: ID of the file to delete
        current_user: Current authenticated user
        
    Returns:
        Success message
        
    Raises:
        HTTPException: If file doesn't exist
    """
    user_dir = ensure_upload_dir() / str(current_user.id)
    
    # Check all possible extensions
    found = False
    for ext in ALLOWED_EXTENSIONS:
        file_path = user_dir / f"{file_id}{ext}"
        if file_path.exists():
            file_path.unlink()
            found = True
            break
    
    if not found:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"File with ID {file_id} not found"
        )
    
    return {"message": "File deleted successfully"} 
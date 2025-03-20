"""
Storage service for the Presentation Automator application.
Handles persistent storage of presentations and uploaded files.
"""

import json
import os
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Union

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from ..models.database import Presentation, User, get_db
from ..models.schemas import Presentation as PresentationSchema
from ..middleware.error_handler import ResourceNotFoundError


class StorageService:
    """Service for managing presentation storage and retrieval."""
    
    @staticmethod
    def save_presentation(
        db: Session, 
        title: str, 
        theme: str, 
        content: PresentationSchema,
        user_id: int
    ) -> Presentation:
        """
        Save a new presentation to the database.
        
        Args:
            db: Database session
            title: Presentation title
            theme: Presentation theme
            content: Presentation content schema
            user_id: ID of the owner
            
        Returns:
            Newly created presentation object
        """
        # Convert presentation content to JSON string
        content_json = json.dumps(content.model_dump())
        
        # Create new presentation
        new_presentation = Presentation(
            title=title,
            theme=theme,
            content=content_json,
            owner_id=user_id
        )
        
        db.add(new_presentation)
        db.commit()
        db.refresh(new_presentation)
        
        return new_presentation
    
    @staticmethod
    def get_presentation(db: Session, presentation_id: int, user_id: int) -> Presentation:
        """
        Get a presentation from the database.
        
        Args:
            db: Database session
            presentation_id: ID of the presentation to retrieve
            user_id: ID of the owner
            
        Returns:
            Presentation object
            
        Raises:
            ResourceNotFoundError: If presentation doesn't exist or doesn't belong to the user
        """
        presentation = (
            db.query(Presentation)
            .filter(
                Presentation.id == presentation_id,
                Presentation.owner_id == user_id
            )
            .first()
        )
        
        if presentation is None:
            raise ResourceNotFoundError("Presentation", presentation_id)
        
        return presentation
    
    @staticmethod
    def update_presentation(
        db: Session,
        presentation_id: int,
        user_id: int,
        title: Optional[str] = None,
        theme: Optional[str] = None,
        content: Optional[PresentationSchema] = None
    ) -> Presentation:
        """
        Update a presentation in the database.
        
        Args:
            db: Database session
            presentation_id: ID of the presentation to update
            user_id: ID of the owner
            title: New title (optional)
            theme: New theme (optional)
            content: New content (optional)
            
        Returns:
            Updated presentation object
            
        Raises:
            ResourceNotFoundError: If presentation doesn't exist or doesn't belong to the user
        """
        presentation = StorageService.get_presentation(db, presentation_id, user_id)
        
        # Update fields if provided
        if title is not None:
            presentation.title = title
        
        if theme is not None:
            presentation.theme = theme
        
        if content is not None:
            presentation.content = json.dumps(content.model_dump())
        
        db.commit()
        db.refresh(presentation)
        
        return presentation
    
    @staticmethod
    def delete_presentation(db: Session, presentation_id: int, user_id: int) -> None:
        """
        Delete a presentation from the database.
        
        Args:
            db: Database session
            presentation_id: ID of the presentation to delete
            user_id: ID of the owner
            
        Raises:
            ResourceNotFoundError: If presentation doesn't exist or doesn't belong to the user
        """
        presentation = StorageService.get_presentation(db, presentation_id, user_id)
        
        db.delete(presentation)
        db.commit()
    
    @staticmethod
    def list_presentations(
        db: Session, 
        user_id: int, 
        skip: int = 0, 
        limit: int = 100
    ) -> List[Presentation]:
        """
        List presentations for a user.
        
        Args:
            db: Database session
            user_id: ID of the owner
            skip: Number of presentations to skip
            limit: Maximum number of presentations to return
            
        Returns:
            List of presentation objects
        """
        presentations = (
            db.query(Presentation)
            .filter(Presentation.owner_id == user_id)
            .order_by(Presentation.created_at.desc())
            .offset(skip)
            .limit(limit)
            .all()
        )
        
        return presentations
    
    @staticmethod
    def presentation_to_schema(presentation: Presentation) -> Dict:
        """
        Convert a presentation database model to a schema dictionary.
        
        Args:
            presentation: Database presentation model
            
        Returns:
            Presentation as a dictionary
        """
        # Parse the JSON content
        content = json.loads(presentation.content)
        
        return {
            "id": presentation.id,
            "title": presentation.title,
            "theme": presentation.theme,
            "content": content,
            "created_at": presentation.created_at.isoformat(),
            "updated_at": presentation.updated_at.isoformat()
        }


class FileStorageService:
    """Service for managing file uploads and retrievals."""
    
    UPLOAD_DIR = os.getenv("UPLOAD_DIR", "uploads")
    
    @staticmethod
    def get_user_directory(user_id: int) -> Path:
        """
        Get the upload directory for a user.
        
        Args:
            user_id: User ID
            
        Returns:
            Path to the user's upload directory
        """
        base_dir = Path(FileStorageService.UPLOAD_DIR)
        
        # Create base directory if it doesn't exist
        if not base_dir.exists():
            base_dir.mkdir(parents=True, exist_ok=True)
        
        # Create user directory if it doesn't exist
        user_dir = base_dir / str(user_id)
        if not user_dir.exists():
            user_dir.mkdir(exist_ok=True)
        
        return user_dir
    
    @staticmethod
    def get_file_path(user_id: int, file_id: str) -> Optional[Path]:
        """
        Get the path to a file.
        
        Args:
            user_id: User ID
            file_id: File ID
            
        Returns:
            Path to the file, or None if not found
        """
        user_dir = FileStorageService.get_user_directory(user_id)
        
        # Look for files with the given ID and any extension
        matching_files = list(user_dir.glob(f"{file_id}.*"))
        
        return matching_files[0] if matching_files else None
    
    @staticmethod
    def delete_file(user_id: int, file_id: str) -> bool:
        """
        Delete a file.
        
        Args:
            user_id: User ID
            file_id: File ID
            
        Returns:
            True if file was deleted, False if not found
        """
        file_path = FileStorageService.get_file_path(user_id, file_id)
        
        if file_path and file_path.exists():
            file_path.unlink()
            return True
        
        return False
    
    @staticmethod
    def list_user_files(user_id: int) -> List[Dict]:
        """
        List all files for a user.
        
        Args:
            user_id: User ID
            
        Returns:
            List of file information dictionaries
        """
        user_dir = FileStorageService.get_user_directory(user_id)
        
        files = []
        for file_path in user_dir.iterdir():
            if file_path.is_file():
                file_id = file_path.stem
                extension = file_path.suffix
                file_size = file_path.stat().st_size
                
                files.append({
                    "filename": f"upload_{file_id}{extension}",
                    "file_id": file_id,
                    "file_size": file_size,
                    "content_type": "application/octet-stream",
                    "upload_time": datetime.fromtimestamp(file_path.stat().st_mtime).isoformat()
                })
        
        return files 
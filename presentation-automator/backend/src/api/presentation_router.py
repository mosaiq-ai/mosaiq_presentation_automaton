"""
API router for presentation management operations.
Includes endpoints for creating, retrieving, updating, and deleting presentations.
"""

import json
from typing import List, Optional
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from ..middleware.auth import get_current_active_user
from ..models.database import Presentation, User, get_db
from ..models.schemas import Presentation as PresentationSchema
from ..middleware.error_handler import ResourceNotFoundError


# Create router
router = APIRouter(prefix="/api/presentations", tags=["presentations"])


# Schema models
class PresentationCreate(BaseModel):
    """Schema for presentation creation requests."""
    
    title: str = Field(..., min_length=1)
    theme: str = Field(..., min_length=1)
    content: PresentationSchema = Field(...)


class PresentationResponse(BaseModel):
    """Schema for presentation responses."""
    
    id: int
    title: str
    theme: str
    content: PresentationSchema
    created_at: str
    updated_at: str
    
    class Config:
        from_attributes = True


class PresentationUpdate(BaseModel):
    """Schema for presentation update requests."""
    
    title: Optional[str] = Field(None, min_length=1)
    theme: Optional[str] = Field(None, min_length=1)
    content: Optional[PresentationSchema] = None


class PresentationListItem(BaseModel):
    """Schema for presentation list items (summary information)."""
    
    id: int
    title: str
    theme: str
    created_at: str
    updated_at: str
    
    class Config:
        from_attributes = True


@router.post("", response_model=PresentationResponse, status_code=status.HTTP_201_CREATED)
async def create_presentation(
    presentation_data: PresentationCreate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Create a new presentation.
    
    Args:
        presentation_data: Presentation creation data
        current_user: Current authenticated user
        db: Database session
        
    Returns:
        Newly created presentation
    """
    # Convert presentation content to JSON string
    content_json = json.dumps(presentation_data.content.model_dump())
    
    # Create new presentation
    new_presentation = Presentation(
        title=presentation_data.title,
        theme=presentation_data.theme,
        content=content_json,
        owner_id=current_user.id
    )
    
    db.add(new_presentation)
    db.commit()
    db.refresh(new_presentation)
    
    # Parse the JSON content back to the schema
    response = _db_presentation_to_response(new_presentation)
    
    return response


@router.get("", response_model=List[PresentationListItem])
async def list_presentations(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=100),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    List presentations for the current user.
    
    Args:
        skip: Number of presentations to skip
        limit: Maximum number of presentations to return
        current_user: Current authenticated user
        db: Database session
        
    Returns:
        List of presentations
    """
    presentations = (
        db.query(Presentation)
        .filter(Presentation.owner_id == current_user.id)
        .order_by(Presentation.created_at.desc())
        .offset(skip)
        .limit(limit)
        .all()
    )
    
    # Convert datetime fields to strings to ensure proper serialization
    result = []
    for p in presentations:
        result.append({
            "id": p.id,
            "title": p.title,
            "theme": p.theme,
            "created_at": p.created_at.isoformat() if isinstance(p.created_at, datetime) else p.created_at,
            "updated_at": p.updated_at.isoformat() if isinstance(p.updated_at, datetime) else p.updated_at
        })
    
    return result


@router.get("/{presentation_id}", response_model=PresentationResponse)
async def get_presentation(
    presentation_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Get a specific presentation.
    
    Args:
        presentation_id: ID of the presentation to retrieve
        current_user: Current authenticated user
        db: Database session
        
    Returns:
        Presentation with the specified ID
        
    Raises:
        ResourceNotFoundError: If presentation doesn't exist or doesn't belong to the user
    """
    presentation = (
        db.query(Presentation)
        .filter(
            Presentation.id == presentation_id,
            Presentation.owner_id == current_user.id
        )
        .first()
    )
    
    if presentation is None:
        raise ResourceNotFoundError("Presentation", presentation_id)
    
    # Parse the JSON content back to the schema
    response = _db_presentation_to_response(presentation)
    
    return response


@router.put("/{presentation_id}", response_model=PresentationResponse)
async def update_presentation(
    presentation_id: int,
    presentation_data: PresentationUpdate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Update a specific presentation.
    
    Args:
        presentation_id: ID of the presentation to update
        presentation_data: Updated presentation data
        current_user: Current authenticated user
        db: Database session
        
    Returns:
        Updated presentation
        
    Raises:
        ResourceNotFoundError: If presentation doesn't exist or doesn't belong to the user
    """
    presentation = (
        db.query(Presentation)
        .filter(
            Presentation.id == presentation_id,
            Presentation.owner_id == current_user.id
        )
        .first()
    )
    
    if presentation is None:
        raise ResourceNotFoundError("Presentation", presentation_id)
    
    # Update fields if provided
    if presentation_data.title:
        presentation.title = presentation_data.title
    
    if presentation_data.theme:
        presentation.theme = presentation_data.theme
    
    if presentation_data.content:
        presentation.content = json.dumps(presentation_data.content.model_dump())
    
    db.commit()
    db.refresh(presentation)
    
    # Parse the JSON content back to the schema
    response = _db_presentation_to_response(presentation)
    
    return response


@router.delete("/{presentation_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_presentation(
    presentation_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Delete a specific presentation.
    
    Args:
        presentation_id: ID of the presentation to delete
        current_user: Current authenticated user
        db: Database session
        
    Returns:
        204 No Content on success
        
    Raises:
        ResourceNotFoundError: If presentation doesn't exist or doesn't belong to the user
    """
    presentation = (
        db.query(Presentation)
        .filter(
            Presentation.id == presentation_id,
            Presentation.owner_id == current_user.id
        )
        .first()
    )
    
    if presentation is None:
        raise ResourceNotFoundError("Presentation", presentation_id)
    
    db.delete(presentation)
    db.commit()
    
    return None


def _db_presentation_to_response(presentation: Presentation) -> PresentationResponse:
    """
    Convert a database presentation model to a response schema.
    
    Args:
        presentation: Database presentation model
        
    Returns:
        Presentation response schema
    """
    # Parse the JSON content
    content = json.loads(presentation.content)
    presentation_schema = PresentationSchema.model_validate(content)
    
    return PresentationResponse(
        id=presentation.id,
        title=presentation.title,
        theme=presentation.theme,
        content=presentation_schema,
        created_at=presentation.created_at.isoformat() if isinstance(presentation.created_at, datetime) else presentation.created_at,
        updated_at=presentation.updated_at.isoformat() if isinstance(presentation.updated_at, datetime) else presentation.updated_at
    ) 
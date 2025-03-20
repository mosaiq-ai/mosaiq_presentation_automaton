"""
API router for user management operations.
Includes endpoints for registration, login, profile management, etc.
"""

from datetime import timedelta
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from pydantic import BaseModel, EmailStr, Field
from sqlalchemy.orm import Session

from ..middleware.auth import (
    get_current_active_user,
    create_access_token,
    get_password_hash,
    verify_password,
)
from ..models.database import User, get_db
from ..middleware.error_handler import ResourceNotFoundError

# Create router
router = APIRouter(prefix="/api/users", tags=["users"])


# Schema models
class UserCreate(BaseModel):
    """Schema for user creation requests."""
    
    email: EmailStr
    password: str = Field(..., min_length=8)
    name: str = Field(..., min_length=2)


class UserLogin(BaseModel):
    """Schema for user login requests."""
    
    email: EmailStr
    password: str


class UserResponse(BaseModel):
    """Schema for user responses (excludes sensitive data)."""
    
    id: int
    email: EmailStr
    name: str
    
    class Config:
        from_attributes = True


class TokenResponse(BaseModel):
    """Schema for token responses."""
    
    access_token: str
    token_type: str
    user: UserResponse


class UserUpdate(BaseModel):
    """Schema for user update requests."""
    
    email: Optional[EmailStr] = None
    name: Optional[str] = Field(None, min_length=2)
    password: Optional[str] = Field(None, min_length=8)


@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def register_user(user_data: UserCreate, db: Session = Depends(get_db)):
    """
    Register a new user.
    
    Args:
        user_data: User registration information
        db: Database session
        
    Returns:
        Newly created user information (without password)
        
    Raises:
        HTTPException: If email already exists
    """
    # Check if email already exists
    existing_user = db.query(User).filter(User.email == user_data.email).first()
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )
    
    # Create new user
    hashed_password = get_password_hash(user_data.password)
    new_user = User(
        email=user_data.email,
        name=user_data.name,
        hashed_password=hashed_password
    )
    
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    
    return new_user


@router.post("/login", response_model=TokenResponse)
async def login_user(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    """
    Authenticate a user and provide an access token.
    
    Args:
        form_data: OAuth2 form with username (email) and password
        db: Database session
        
    Returns:
        JWT access token and user information
        
    Raises:
        HTTPException: If authentication fails
    """
    # Find user by email
    user = db.query(User).filter(User.email == form_data.username).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Verify password
    if not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Create access token
    access_token_expires = timedelta(minutes=30)
    access_token = create_access_token(
        data={"sub": user.email, "user_id": user.id},
        expires_delta=access_token_expires,
    )
    
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "user": user
    }


@router.get("/me", response_model=UserResponse)
async def get_user_profile(current_user: User = Depends(get_current_active_user)):
    """
    Get the current user's profile.
    
    Args:
        current_user: Current authenticated user
        
    Returns:
        User information
    """
    return current_user


@router.put("/me", response_model=UserResponse)
async def update_user_profile(
    user_data: UserUpdate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Update the current user's profile.
    
    Args:
        user_data: Updated user information
        current_user: Current authenticated user
        db: Database session
        
    Returns:
        Updated user information
        
    Raises:
        HTTPException: If email already exists
    """
    # Check if email is being updated and if it already exists
    if user_data.email and user_data.email != current_user.email:
        existing_user = db.query(User).filter(User.email == user_data.email).first()
        if existing_user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email already registered"
            )
        current_user.email = user_data.email
    
    # Update other fields if provided
    if user_data.name:
        current_user.name = user_data.name
    
    if user_data.password:
        current_user.hashed_password = get_password_hash(user_data.password)
    
    # Save changes
    db.commit()
    db.refresh(current_user)
    
    return current_user 
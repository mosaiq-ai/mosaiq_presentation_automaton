"""
Database models for the Presentation Automator application.
Uses SQLAlchemy ORM for data persistence.
"""

from datetime import datetime
import os
from typing import List, Optional

from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, Boolean, create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship, sessionmaker, Session
from sqlalchemy.pool import QueuePool

# Base class for SQLAlchemy models
Base = declarative_base()

# Database connection settings
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///presentations.db")


class User(Base):
    """User model for authentication and authorization."""
    
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(255), unique=True, index=True, nullable=False)
    name = Column(String(255), nullable=False)
    hashed_password = Column(String(255), nullable=False)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    presentations = relationship("Presentation", back_populates="owner", cascade="all, delete-orphan")


class Presentation(Base):
    """Presentation model for storing presentation data."""
    
    __tablename__ = "presentations"
    
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(255), nullable=False)
    theme = Column(String(255), nullable=False)
    owner_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    content = Column(Text, nullable=False)  # JSON string of the presentation
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    owner = relationship("User", back_populates="presentations")


# Database connection management
class DatabaseManager:
    """Manages database connections and sessions."""
    
    _engine = None
    _SessionLocal = None
    
    @classmethod
    def initialize(cls, database_url: Optional[str] = None):
        """Initialize the database connection."""
        if database_url is None:
            database_url = DATABASE_URL
            
        cls._engine = create_engine(
            database_url,
            poolclass=QueuePool,
            pool_size=5,
            max_overflow=10,
            pool_timeout=30,
            pool_recycle=1800,
        )
        cls._SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=cls._engine)
        
        # Create tables if they don't exist
        Base.metadata.create_all(cls._engine)
    
    @classmethod
    def get_session(cls) -> Session:
        """Get a new database session."""
        if cls._SessionLocal is None:
            cls.initialize()
        return cls._SessionLocal()
    
    @classmethod
    def close(cls):
        """Close the database connection."""
        if cls._engine is not None:
            cls._engine.dispose()
            cls._engine = None
            cls._SessionLocal = None


# Initialize database on import if not in test mode
if os.getenv("TESTING") != "True":
    DatabaseManager.initialize()


def get_db():
    """
    Dependency for FastAPI routes to get a database session.
    Usage: 
        @app.get("/")
        def get_item(db: Session = Depends(get_db)):
            # Use db here
    """
    db = DatabaseManager.get_session()
    try:
        yield db
    finally:
        db.close() 
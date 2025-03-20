"""
Tests for the file upload API endpoints.
"""

import os
import shutil
import tempfile
from pathlib import Path
from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from src.api.app import app
from src.models.database import Base, get_db, User
from src.middleware.auth import get_password_hash


# Setup test database
SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Create the tables
Base.metadata.create_all(bind=engine)


# Override the get_db dependency to use the test database
def override_get_db():
    try:
        db = TestingSessionLocal()
        yield db
    finally:
        db.close()


app.dependency_overrides[get_db] = override_get_db


# Test client
client = TestClient(app)


# Setup test upload directory
@pytest.fixture(scope="module")
def test_upload_dir():
    """Create a temporary directory for uploads."""
    upload_dir = tempfile.mkdtemp()
    
    # Mock the UPLOAD_DIR in the upload router
    with patch("src.api.upload_router.UPLOAD_DIR", upload_dir):
        yield upload_dir
    
    # Clean up
    shutil.rmtree(upload_dir)


# Fixtures
@pytest.fixture
def test_user():
    """Create a test user and return credentials."""
    user_data = {
        "email": "test@example.com",
        "password": "testpassword",
        "name": "Test User"
    }
    
    return user_data


@pytest.fixture
def db_user(test_user):
    """Create and persist a test user in the database."""
    db = TestingSessionLocal()
    
    # Delete any existing user with the same email
    existing_user = db.query(User).filter(User.email == test_user["email"]).first()
    if existing_user:
        db.delete(existing_user)
        db.commit()
    
    # Create new user
    hashed_password = get_password_hash(test_user["password"])
    db_user = User(
        email=test_user["email"],
        name=test_user["name"],
        hashed_password=hashed_password
    )
    
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    
    yield db_user
    
    # Cleanup
    db.delete(db_user)
    db.commit()
    db.close()


@pytest.fixture
def auth_token(db_user, test_user):
    """Get an auth token for the test user."""
    response = client.post(
        "/api/users/login",
        data={
            "username": test_user["email"],
            "password": test_user["password"]
        }
    )
    
    assert response.status_code == 200
    
    return response.json()["access_token"]


@pytest.fixture
def test_file():
    """Create a test text file for upload."""
    content = "This is a test file content for upload testing."
    file_path = tempfile.mktemp(suffix=".txt")
    
    with open(file_path, "w") as f:
        f.write(content)
    
    yield file_path
    
    # Clean up
    if os.path.exists(file_path):
        os.unlink(file_path)


# Tests
def test_upload_file(auth_token, test_file, test_upload_dir, db_user):
    """Test uploading a file."""
    with open(test_file, "rb") as f:
        response = client.post(
            "/api/upload",
            headers={"Authorization": f"Bearer {auth_token}"},
            files={"file": (os.path.basename(test_file), f, "text/plain")}
        )
    
    assert response.status_code == 201
    assert "filename" in response.json()
    assert "file_id" in response.json()
    assert "file_size" in response.json()
    assert "content_type" in response.json()
    assert "upload_time" in response.json()
    
    # Verify file was saved
    file_id = response.json()["file_id"]
    user_dir = Path(test_upload_dir) / str(db_user.id)
    assert user_dir.exists()
    
    # Find the uploaded file by ID prefix
    uploaded_files = list(user_dir.glob(f"{file_id}*"))
    assert len(uploaded_files) == 1
    
    # Verify content
    with open(uploaded_files[0], "r") as f:
        content = f.read()
        assert content == "This is a test file content for upload testing."


def test_upload_file_unauthorized(test_file):
    """Test uploading a file without authentication."""
    with open(test_file, "rb") as f:
        response = client.post(
            "/api/upload",
            files={"file": (os.path.basename(test_file), f, "text/plain")}
        )
    
    assert response.status_code == 401
    assert "Not authenticated" in response.json()["detail"]


def test_upload_invalid_file_type(auth_token, test_upload_dir):
    """Test uploading a file with an invalid extension."""
    # Create a temporary file with invalid extension
    invalid_file = tempfile.mktemp(suffix=".invalid")
    with open(invalid_file, "w") as f:
        f.write("Invalid file content")
    
    try:
        with open(invalid_file, "rb") as f:
            response = client.post(
                "/api/upload",
                headers={"Authorization": f"Bearer {auth_token}"},
                files={"file": (os.path.basename(invalid_file), f, "application/octet-stream")}
            )
        
        assert response.status_code == 415
        assert "Unsupported file type" in response.json()["detail"]
    finally:
        if os.path.exists(invalid_file):
            os.unlink(invalid_file)


def test_list_uploads(auth_token, test_file, test_upload_dir, db_user):
    """Test listing uploaded files."""
    # First upload a file
    with open(test_file, "rb") as f:
        response = client.post(
            "/api/upload",
            headers={"Authorization": f"Bearer {auth_token}"},
            files={"file": (os.path.basename(test_file), f, "text/plain")}
        )
    
    assert response.status_code == 201
    file_id = response.json()["file_id"]
    
    # Now list the uploads
    response = client.get(
        "/api/upload",
        headers={"Authorization": f"Bearer {auth_token}"}
    )
    
    assert response.status_code == 200
    assert isinstance(response.json(), list)
    assert len(response.json()) >= 1
    
    # Check if our uploaded file is in the list
    found = False
    for file_info in response.json():
        if file_info["file_id"] == file_id:
            found = True
            assert "filename" in file_info
            assert "file_size" in file_info
            assert "content_type" in file_info
            assert "upload_time" in file_info
            break
    
    assert found, "Uploaded file not found in listing"


def test_delete_upload(auth_token, test_file, test_upload_dir, db_user):
    """Test deleting an uploaded file."""
    # First upload a file
    with open(test_file, "rb") as f:
        response = client.post(
            "/api/upload",
            headers={"Authorization": f"Bearer {auth_token}"},
            files={"file": (os.path.basename(test_file), f, "text/plain")}
        )
    
    assert response.status_code == 201
    file_id = response.json()["file_id"]
    
    # Now delete the file
    response = client.delete(
        f"/api/upload/{file_id}",
        headers={"Authorization": f"Bearer {auth_token}"}
    )
    
    assert response.status_code == 200
    assert "File deleted successfully" in response.json()["message"]
    
    # Verify file was deleted
    user_dir = Path(test_upload_dir) / str(db_user.id)
    uploaded_files = list(user_dir.glob(f"{file_id}*"))
    assert len(uploaded_files) == 0
    
    # Try to delete it again, should fail
    response = client.delete(
        f"/api/upload/{file_id}",
        headers={"Authorization": f"Bearer {auth_token}"}
    )
    
    assert response.status_code == 404
    assert "not found" in response.json()["detail"]


def test_delete_upload_unauthorized(auth_token, test_file, test_upload_dir, db_user):
    """Test deleting an uploaded file without authentication."""
    # First upload a file
    with open(test_file, "rb") as f:
        response = client.post(
            "/api/upload",
            headers={"Authorization": f"Bearer {auth_token}"},
            files={"file": (os.path.basename(test_file), f, "text/plain")}
        )
    
    assert response.status_code == 201
    file_id = response.json()["file_id"]
    
    # Try to delete without auth
    response = client.delete(f"/api/upload/{file_id}")
    
    assert response.status_code == 401
    assert "Not authenticated" in response.json()["detail"]
    
    # Verify file still exists
    user_dir = Path(test_upload_dir) / str(db_user.id)
    uploaded_files = list(user_dir.glob(f"{file_id}*"))
    assert len(uploaded_files) == 1 
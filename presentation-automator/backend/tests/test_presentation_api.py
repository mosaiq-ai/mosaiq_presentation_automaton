"""
Tests for the presentation management API endpoints.
"""

import json
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from src.api.app import app
from src.models.database import Base, get_db, User, Presentation
from src.middleware.auth import get_password_hash
from src.models.schemas import SlideContent


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


# Test data
TEST_PRESENTATION = {
    "title": "Test Presentation",
    "theme": "modern",
    "content": {
        "title": "Test Presentation",
        "theme": "modern",
        "slides": [
            {
                "slide_number": 1,
                "title": "Introduction",
                "content": "<h1>Introduction</h1><p>This is the first slide.</p>",
                "notes": "Speaker notes for introduction"
            },
            {
                "slide_number": 2,
                "title": "Content",
                "content": "<h1>Content</h1><p>This is the second slide.</p>",
                "notes": "Speaker notes for content"
            }
        ]
    }
}


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
    db.query(Presentation).filter(Presentation.owner_id == db_user.id).delete()
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
def test_presentation(db_user):
    """Create a test presentation in the database."""
    db = TestingSessionLocal()
    
    # Convert presentation content to JSON string
    content_json = json.dumps(TEST_PRESENTATION["content"])
    
    # Create new presentation
    new_presentation = Presentation(
        title=TEST_PRESENTATION["title"],
        theme=TEST_PRESENTATION["theme"],
        content=content_json,
        owner_id=db_user.id
    )
    
    db.add(new_presentation)
    db.commit()
    db.refresh(new_presentation)
    
    yield new_presentation
    
    # Cleanup handled by db_user fixture
    db.close()


# Tests
def test_create_presentation(auth_token, db_user):
    """Test creating a presentation."""
    response = client.post(
        "/api/presentations",
        headers={"Authorization": f"Bearer {auth_token}"},
        json=TEST_PRESENTATION
    )
    
    assert response.status_code == 201
    assert response.json()["title"] == TEST_PRESENTATION["title"]
    assert response.json()["theme"] == TEST_PRESENTATION["theme"]
    assert "id" in response.json()
    assert "created_at" in response.json()
    assert "updated_at" in response.json()
    
    # Verify content structure
    assert "content" in response.json()
    assert response.json()["content"]["title"] == TEST_PRESENTATION["content"]["title"]
    assert len(response.json()["content"]["slides"]) == len(TEST_PRESENTATION["content"]["slides"])
    
    # Verify database entry
    db = TestingSessionLocal()
    presentation = db.query(Presentation).filter(
        Presentation.id == response.json()["id"]
    ).first()
    
    assert presentation is not None
    assert presentation.title == TEST_PRESENTATION["title"]
    assert presentation.theme == TEST_PRESENTATION["theme"]
    assert presentation.owner_id == db_user.id
    
    db.close()


def test_get_presentation(auth_token, test_presentation):
    """Test retrieving a specific presentation."""
    response = client.get(
        f"/api/presentations/{test_presentation.id}",
        headers={"Authorization": f"Bearer {auth_token}"}
    )
    
    assert response.status_code == 200
    assert response.json()["id"] == test_presentation.id
    assert response.json()["title"] == test_presentation.title
    assert response.json()["theme"] == test_presentation.theme
    
    # Verify content was properly decoded from JSON
    assert "content" in response.json()
    assert response.json()["content"]["title"] == TEST_PRESENTATION["content"]["title"]
    assert len(response.json()["content"]["slides"]) == len(TEST_PRESENTATION["content"]["slides"])


def test_get_nonexistent_presentation(auth_token):
    """Test retrieving a non-existent presentation."""
    response = client.get(
        "/api/presentations/999",
        headers={"Authorization": f"Bearer {auth_token}"}
    )
    
    assert response.status_code == 404
    assert "not found" in response.json()["details"].lower()


def test_list_presentations(auth_token, test_presentation):
    """Test listing presentations for the current user."""
    response = client.get(
        "/api/presentations",
        headers={"Authorization": f"Bearer {auth_token}"}
    )
    
    assert response.status_code == 200
    assert isinstance(response.json(), list)
    assert len(response.json()) >= 1
    
    # Check for our test presentation
    found = False
    for item in response.json():
        if item["id"] == test_presentation.id:
            found = True
            assert item["title"] == test_presentation.title
            assert item["theme"] == test_presentation.theme
            assert "created_at" in item
            assert "updated_at" in item
            break
    
    assert found, "Test presentation not found in listing"


def test_update_presentation(auth_token, test_presentation):
    """Test updating a presentation."""
    update_data = {
        "title": "Updated Title",
        "theme": "Updated Theme"
    }
    
    response = client.put(
        f"/api/presentations/{test_presentation.id}",
        headers={"Authorization": f"Bearer {auth_token}"},
        json=update_data
    )
    
    assert response.status_code == 200
    assert response.json()["id"] == test_presentation.id
    assert response.json()["title"] == update_data["title"]
    assert response.json()["theme"] == update_data["theme"]
    
    # Check that content was preserved
    assert "content" in response.json()
    assert response.json()["content"]["title"] == TEST_PRESENTATION["content"]["title"]
    
    # Verify database was updated
    db = TestingSessionLocal()
    updated_presentation = db.query(Presentation).filter(
        Presentation.id == test_presentation.id
    ).first()
    
    assert updated_presentation is not None
    assert updated_presentation.title == update_data["title"]
    assert updated_presentation.theme == update_data["theme"]
    
    db.close()


def test_update_presentation_content(auth_token, test_presentation):
    """Test updating presentation content."""
    # Create updated content
    updated_content = TEST_PRESENTATION["content"].copy()
    updated_content["title"] = "Updated Content Title"
    updated_content["slides"].append({
        "slide_number": 3,
        "title": "New Slide",
        "content": "<h1>New Slide</h1><p>This is a new slide.</p>",
        "notes": "Speaker notes for new slide"
    })
    
    update_data = {
        "content": updated_content
    }
    
    response = client.put(
        f"/api/presentations/{test_presentation.id}",
        headers={"Authorization": f"Bearer {auth_token}"},
        json=update_data
    )
    
    assert response.status_code == 200
    assert response.json()["id"] == test_presentation.id
    
    # Check that content was updated
    assert "content" in response.json()
    assert response.json()["content"]["title"] == updated_content["title"]
    assert len(response.json()["content"]["slides"]) == len(updated_content["slides"])
    
    # Verify database was updated
    db = TestingSessionLocal()
    updated_presentation = db.query(Presentation).filter(
        Presentation.id == test_presentation.id
    ).first()
    
    assert updated_presentation is not None
    content = json.loads(updated_presentation.content)
    assert content["title"] == updated_content["title"]
    assert len(content["slides"]) == len(updated_content["slides"])
    
    db.close()


def test_update_nonexistent_presentation(auth_token):
    """Test updating a non-existent presentation."""
    update_data = {
        "title": "Updated Title"
    }
    
    response = client.put(
        "/api/presentations/999",
        headers={"Authorization": f"Bearer {auth_token}"},
        json=update_data
    )
    
    assert response.status_code == 404
    assert "not found" in response.json()["details"].lower()


def test_delete_presentation(auth_token, test_presentation):
    """Test deleting a presentation."""
    response = client.delete(
        f"/api/presentations/{test_presentation.id}",
        headers={"Authorization": f"Bearer {auth_token}"}
    )
    
    assert response.status_code == 204
    
    # Verify presentation was deleted
    db = TestingSessionLocal()
    deleted_presentation = db.query(Presentation).filter(
        Presentation.id == test_presentation.id
    ).first()
    
    assert deleted_presentation is None
    
    db.close()


def test_delete_nonexistent_presentation(auth_token):
    """Test deleting a non-existent presentation."""
    response = client.delete(
        "/api/presentations/999",
        headers={"Authorization": f"Bearer {auth_token}"}
    )
    
    assert response.status_code == 404
    assert "not found" in response.json()["details"].lower()


def test_unauthorized_access():
    """Test accessing the API without authentication."""
    # Try to list presentations
    response = client.get("/api/presentations")
    assert response.status_code == 401
    
    # Try to get a presentation
    response = client.get("/api/presentations/1")
    assert response.status_code == 401
    
    # Try to create a presentation
    response = client.post("/api/presentations", json=TEST_PRESENTATION)
    assert response.status_code == 401
    
    # Try to update a presentation
    response = client.put("/api/presentations/1", json={"title": "Unauthorized"})
    assert response.status_code == 401
    
    # Try to delete a presentation
    response = client.delete("/api/presentations/1")
    assert response.status_code == 401 
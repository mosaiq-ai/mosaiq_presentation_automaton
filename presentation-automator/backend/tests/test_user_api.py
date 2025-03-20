"""
Tests for the user management API endpoints.
"""

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


# Tests
def test_user_registration():
    """Test user registration endpoint."""
    # Clear any existing users
    db = TestingSessionLocal()
    db.query(User).delete()
    db.commit()
    
    user_data = {
        "email": "new@example.com",
        "password": "newpassword",
        "name": "New User"
    }
    
    response = client.post("/api/users/register", json=user_data)
    
    assert response.status_code == 201
    assert response.json()["email"] == user_data["email"]
    assert response.json()["name"] == user_data["name"]
    assert "id" in response.json()
    assert "hashed_password" not in response.json()
    
    # Verify user was created in database
    db_user = db.query(User).filter(User.email == user_data["email"]).first()
    assert db_user is not None
    assert db_user.email == user_data["email"]
    assert db_user.name == user_data["name"]
    
    # Cleanup
    db.delete(db_user)
    db.commit()
    db.close()


def test_duplicate_email_registration(db_user, test_user):
    """Test that registering with an existing email fails."""
    response = client.post("/api/users/register", json=test_user)
    
    assert response.status_code == 400
    assert "Email already registered" in response.json()["detail"]


def test_user_login(db_user, test_user):
    """Test user login endpoint."""
    response = client.post(
        "/api/users/login",
        data={
            "username": test_user["email"],
            "password": test_user["password"]
        }
    )
    
    assert response.status_code == 200
    assert "access_token" in response.json()
    assert response.json()["token_type"] == "bearer"
    assert response.json()["user"]["email"] == test_user["email"]
    assert response.json()["user"]["name"] == test_user["name"]


def test_user_login_invalid_credentials(db_user, test_user):
    """Test login with invalid credentials."""
    # Test with wrong password
    response = client.post(
        "/api/users/login",
        data={
            "username": test_user["email"],
            "password": "wrongpassword"
        }
    )
    
    assert response.status_code == 401
    assert "Incorrect email or password" in response.json()["detail"]
    
    # Test with non-existent email
    response = client.post(
        "/api/users/login",
        data={
            "username": "nonexistent@example.com",
            "password": test_user["password"]
        }
    )
    
    assert response.status_code == 401
    assert "Incorrect email or password" in response.json()["detail"]


def test_get_user_profile(auth_token, db_user):
    """Test getting user profile."""
    response = client.get(
        "/api/users/me",
        headers={"Authorization": f"Bearer {auth_token}"}
    )
    
    assert response.status_code == 200
    assert response.json()["email"] == db_user.email
    assert response.json()["name"] == db_user.name
    assert response.json()["id"] == db_user.id


def test_get_user_profile_unauthorized():
    """Test getting user profile without authentication."""
    response = client.get("/api/users/me")
    
    assert response.status_code == 401
    assert "Not authenticated" in response.json()["detail"]


def test_update_user_profile(auth_token, db_user):
    """Test updating user profile."""
    update_data = {
        "name": "Updated Name"
    }
    
    response = client.put(
        "/api/users/me",
        headers={"Authorization": f"Bearer {auth_token}"},
        json=update_data
    )
    
    assert response.status_code == 200
    assert response.json()["name"] == update_data["name"]
    assert response.json()["email"] == db_user.email
    
    # Verify database was updated
    db = TestingSessionLocal()
    updated_user = db.query(User).filter(User.id == db_user.id).first()
    assert updated_user.name == update_data["name"]
    db.close()


def test_update_email(auth_token, db_user):
    """Test updating user email."""
    update_data = {
        "email": "updated@example.com"
    }
    
    response = client.put(
        "/api/users/me",
        headers={"Authorization": f"Bearer {auth_token}"},
        json=update_data
    )
    
    assert response.status_code == 200
    assert response.json()["email"] == update_data["email"]
    
    # Verify database was updated
    db = TestingSessionLocal()
    updated_user = db.query(User).filter(User.id == db_user.id).first()
    assert updated_user.email == update_data["email"]
    db.close()


def test_update_password(auth_token, db_user, test_user):
    """Test updating user password."""
    new_password = "newpassword123"
    update_data = {
        "password": new_password
    }
    
    response = client.put(
        "/api/users/me",
        headers={"Authorization": f"Bearer {auth_token}"},
        json=update_data
    )
    
    assert response.status_code == 200
    
    # Try to login with new password
    response = client.post(
        "/api/users/login",
        data={
            "username": test_user["email"],
            "password": new_password
        }
    )
    
    assert response.status_code == 200
    assert "access_token" in response.json()


def test_update_to_existing_email(auth_token, db_user):
    """Test that updating to an existing email fails."""
    # Create another user
    db = TestingSessionLocal()
    other_user = User(
        email="other@example.com",
        name="Other User",
        hashed_password=get_password_hash("otherpassword")
    )
    db.add(other_user)
    db.commit()
    
    # Try to update to the other user's email
    update_data = {
        "email": "other@example.com"
    }
    
    response = client.put(
        "/api/users/me",
        headers={"Authorization": f"Bearer {auth_token}"},
        json=update_data
    )
    
    assert response.status_code == 400
    assert "Email already registered" in response.json()["detail"]
    
    # Cleanup
    db.delete(other_user)
    db.commit()
    db.close() 
"""
Tests for the health check endpoints.
"""

import pytest
from fastapi.testclient import TestClient

from src.api.app import app

client = TestClient(app)


def test_root_endpoint():
    """Test the root endpoint returns correct status."""
    response = client.get("/")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_health_endpoint():
    """Test the health endpoint returns detailed status."""
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"
    assert "api_status" in response.json()
    assert "server_info" in response.json() 
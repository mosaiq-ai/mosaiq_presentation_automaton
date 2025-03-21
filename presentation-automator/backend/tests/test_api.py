"""
Tests for the API endpoints.
"""

import pytest
import os
from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock

from src.api.app import app
from src.models.schemas import Presentation, SlideContent

client = TestClient(app)

# Check if OpenAI API key is set
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
SKIP_API_TESTS = not OPENAI_API_KEY

# Sample document text for testing
SAMPLE_TEXT = """
# Project Plan: Modernizing Our Company Website

## Introduction
Our company website is outdated and needs a modern redesign.
"""

# Mock presentation for testing
MOCK_PRESENTATION = Presentation(
    title="Website Modernization Project",
    theme="business",
    slides=[
        SlideContent(
            slide_number=1,
            title="Introduction",
            content="<h1>Introduction</h1><p>Our company website is outdated and needs a modern redesign</p>",
            notes="Speaker notes here"
        ),
        SlideContent(
            slide_number=2,
            title="Objectives",
            content="<h1>Objectives</h1><ul><li>Improve UX</li><li>Increase conversion rates</li></ul>",
            notes=""
        )
    ]
)


def test_generate_endpoint_mock():
    """Test the generate endpoint with mocked generator."""
    with patch("src.api.router.generator.generate_from_text") as mock_generate:
        # Configure the mock
        mock_generate.return_value = MOCK_PRESENTATION
        
        # Make the request
        response = client.post(
            "/api/generate",
            json={"document_text": SAMPLE_TEXT}
        )
        
        # Verify the response
        assert response.status_code == 200
        data = response.json()
        assert data["presentation"]["title"] == "Website Modernization Project"
        assert len(data["presentation"]["slides"]) == 2
        assert "metadata" in data


@pytest.mark.skipif(SKIP_API_TESTS, reason="OpenAI API key not set")
def test_generate_endpoint_real():
    """Test the generate endpoint with real API calls."""
    # Make the request
    response = client.post(
        "/api/generate",
        json={"document_text": SAMPLE_TEXT, "options": {}}
    )
    
    # Verify the response
    assert response.status_code == 200
    data = response.json()
    assert "presentation" in data
    assert "title" in data["presentation"]
    assert "slides" in data["presentation"]
    assert len(data["presentation"]["slides"]) > 0
    assert "metadata" in data 
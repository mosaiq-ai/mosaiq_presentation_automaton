"""
Test module for the document processor service.
"""

import asyncio
import os
import sys
import pytest

# Add the parent directory to the path for imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
# Add the local lib directory for additional packages
lib_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "lib"))
if os.path.exists(lib_path):
    sys.path.insert(0, lib_path)

# Import the document processor while ensuring docx is correctly imported first
try:
    import docx
except ImportError:
    print("Warning: python-docx package is installed but 'docx' module cannot be imported.")
    print("Try installing with: pip install python-docx")
    
from src.services.document_processor import process_document


@pytest.mark.asyncio
async def test_document_processor_text():
    """Test document processing with text input."""
    
    # Sample markdown document
    document_text = """# Sample Document
    
This is a test document with some sample content.

## Section 1

- Item 1
- Item 2
- Item 3

## Section 2

This is another section with some more content.
"""
    
    # Process the document
    text, stats = await process_document(document_text=document_text)
    
    # Check the results
    assert text == document_text
    assert stats["document_type"] == "text"
    assert stats["character_count"] > 0
    assert stats["word_count"] > 0
    assert stats["paragraph_count"] > 0
    assert "sentence_count" in stats
    assert "avg_words_per_paragraph" in stats


if __name__ == "__main__":
    """Run the test directly."""
    asyncio.run(test_document_processor_text())
    print("Document processor test passed!") 
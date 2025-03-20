# Context-Based Integration for Presentation Automator

This module enhances the Presentation Automator backend with advanced context sharing, document processing, and asynchronous task handling capabilities.

## Overview

The Context-Based Integration module adds the following features to the Presentation Automator:

1. **Context Management**: Better communication between agents with shared context and statistics tracking
2. **Document Processing**: Support for various document formats (DOCX, PDF, plain text)
3. **Asynchronous Task System**: Long-running operations with progress tracking
4. **Caching Service**: Performance optimization with in-memory and file-based caching
5. **Content Extraction**: Extract structured content from documents (sections, bullet points, keywords)
6. **Enhanced Presentation Service**: Context-aware presentation generation with progress reporting
7. **Async API Endpoints**: Support for asynchronous generation with status tracking

## Architecture

The architecture follows a service-oriented approach with these main components:

- **Services**: Core business logic with stateless functions for processing
- **API Endpoints**: RESTful and SSE endpoints for client interaction
- **Context Manager**: Facilitates data sharing between components
- **Task Manager**: Handles long-running tasks in the background

## Services

### Context Manager

The context manager (`utils/context_manager.py`) provides:

- `GenerationStats`: Model for tracking statistics about the generation process
- `GenerationContext`: Class for sharing data between agent components
- Stage completion tracking
- Tool usage tracking

### Document Processor

The document processor (`services/document_processor.py`) provides:

- Text extraction from DOCX files
- Text extraction from PDF files
- Processing plain text files
- Document statistics generation

### Task Manager

The task manager (`services/task_manager.py`) provides:

- Asynchronous task execution
- Progress tracking and reporting
- Task status monitoring
- Background workers with concurrency control

### Caching Service

The caching service (`services/cache_service.py`) provides:

- In-memory caching for fast access
- File-based persistent caching
- Cache decorator for function results
- Cache invalidation methods

### Content Extraction

The content extraction service (`services/content_extraction.py`) provides:

- Section extraction from documents
- Bullet point extraction
- Keyword extraction
- Slide-specific content extraction

### Presentation Service

The enhanced presentation service (`services/presentation_service.py`) provides:

- Context-aware presentation generation
- Progress tracking and reporting
- Caching integration
- Asynchronous generation

## API Endpoints

### Asynchronous Generation

New API endpoints for asynchronous generation:

- `POST /api/generate-async`: Start asynchronous presentation generation
- `POST /api/generate-from-file-async`: Start asynchronous generation from a file
- `GET /api/generation/{task_id}/status`: Check generation status
- `GET /api/generation/{task_id}/result`: Get generation result
- `GET /api/generation/{task_id}/events`: SSE endpoint for real-time updates
- `GET /api/generations`: List all generation tasks

## Usage

### Starting the Server

```bash
./run.sh
```

### Generating a Presentation Asynchronously

```bash
curl -X POST http://localhost:8000/api/generate-async \
  -H "Content-Type: application/json" \
  -d '{"document_text": "# Sample Document\n\nThis is a test document."}'
```

Response:
```json
{
  "task_id": "123e4567-e89b-12d3-a456-426614174000",
  "message": "Presentation generation started"
}
```

### Checking Generation Status

```bash
curl http://localhost:8000/api/generation/123e4567-e89b-12d3-a456-426614174000/status
```

Response:
```json
{
  "task_id": "123e4567-e89b-12d3-a456-426614174000",
  "status": "running",
  "progress": 0.4,
  "message": "Creating presentation plan",
  "created_at": "2023-06-08T12:34:56.789012",
  "started_at": "2023-06-08T12:34:57.123456"
}
```

### Retrieving Generation Results

```bash
curl http://localhost:8000/api/generation/123e4567-e89b-12d3-a456-426614174000/result
```

Response:
```json
{
  "title": "Sample Document",
  "theme": "professional",
  "slides": [
    {
      "slide_number": 1,
      "title": "Sample Document",
      "content": "<h1>Sample Document</h1>",
      "notes": "Introduction slide for the presentation."
    }
  ]
}
```

## Testing

Run the tests with:

```bash
./run_tests.sh
```

Individual tests can be run directly:

```bash
# Test document processor
python tests/test_document_processor.py

# Test task manager
python tests/test_task_manager.py

# Test cache service
python tests/test_cache_service.py
```

## Dependencies

- Python-docx for DOCX processing
- PyPDF2 for PDF processing
- AsyncIO for asynchronous operations
- SSE-Starlette for server-sent events 
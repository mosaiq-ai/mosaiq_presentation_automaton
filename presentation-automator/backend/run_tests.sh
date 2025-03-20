#!/bin/bash

# Run tests for the context-based integration features
echo "Running tests for Context-Based Integration features..."

# Make the script executable
chmod +x run_tests.sh

# Activate virtual environment if it exists
if [ -d ".venv" ]; then
    source .venv/bin/activate
fi

# Run document processor test
echo "========================================"
echo "Testing Document Processor Service..."
echo "========================================"
python tests/test_document_processor.py

# Run task manager test
echo "========================================"
echo "Testing Task Manager Service..."
echo "========================================"
python tests/test_task_manager.py

# Run cache service test
echo "========================================"
echo "Testing Cache Service..."
echo "========================================"
python tests/test_cache_service.py

# Run pytest for all tests
echo "========================================"
echo "Running all tests with pytest..."
echo "========================================"
pytest tests/

echo "========================================"
echo "All tests completed!"
echo "========================================" 
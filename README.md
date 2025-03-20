# Mosaiq Presentation Automator

An AI-powered presentation generator that automatically creates professional presentations from text documents using specialized AI agents.

## Overview

The Presentation Automator is a system designed to transform text documents into structured, coherent presentations. It leverages the OpenAI Agents SDK to create specialized agents that handle different aspects of the presentation generation process.

## Architecture

The system consists of the following components:

1. **Planning Agent**: Analyzes document text and creates a structured presentation plan
2. **Content Agent**: Generates detailed content for each slide based on the plan
3. **Presentation Generator**: Orchestrates the generation process
4. **FastAPI Backend**: Provides an API for accessing the generator functionality

## Prerequisites

- Python 3.11+
- OpenAI API Key

## Installation

1. Clone the repository:
   ```bash
   git clone https://github.com/yourusername/mosaiq_presentation_automator.git
   cd mosaiq_presentation_automator
   ```

2. Create a virtual environment:
   ```bash
   python -m venv .venv
   source .venv/bin/activate  # On Windows, use: .venv\Scripts\activate
   ```

3. Install dependencies:
   ```bash
   cd presentation-automator/backend
   pip install -e .
   ```

4. Set up environment variables:
   ```bash
   cp .env.example .env
   # Edit .env to add your OpenAI API key
   ```

## Usage

Start the backend server:

```bash
cd presentation-automator/backend
./run.sh  # or python -m src.main
```

The API will be available at http://localhost:8000

### API Endpoints

- **GET /**: Health check endpoint
- **GET /health**: Detailed health check with API status
- **POST /api/generate**: Generate a presentation from text

Example request to generate a presentation:

```bash
curl -X POST http://localhost:8000/api/generate \
  -H "Content-Type: application/json" \
  -d '{"document_text": "# Sample Document\n\nThis is a test document for presentation generation."}'
```

## Development

Run tests:

```bash
cd presentation-automator/backend
pytest  # Run all tests
pytest tests/test_agents.py::test_planning_agent_mock  # Run specific tests
```

## License

MIT 
# Presentation Automator Backend

Backend API for the Presentation Automator system, which generates professional presentations from text using AI.

## Requirements

- Python 3.11 or higher
- OpenAI API key

## Setup

1. Clone the repository:
   ```bash
   git clone [repository-url]
   cd presentation-automator/backend
   ```

2. Create a virtual environment:
   ```bash
   python -m venv .venv
   source .venv/bin/activate  # On Windows: .venv\Scripts\activate
   ```

3. Install dependencies:
   ```bash
   pip install -e .
   ```

4. Configure environment variables:
   ```bash
   cp .env.example .env
   # Edit .env file and add your OpenAI API key
   ```

## Running the Server

```bash
# Using the run script
./run.sh

# Or manually
source .venv/bin/activate
python -m src.main
```

The server will start at `http://localhost:8000` by default.

## API Documentation

Once the server is running, you can access the Swagger UI documentation at:
http://localhost:8000/docs

## Running Tests

```bash
pytest
``` 
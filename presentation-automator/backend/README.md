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
# First, make sure you're in the backend directory
cd presentation-automator/backend

# Using the run script
./run.sh

# Or manually
source .venv/bin/activate
python -m src.main
```

The server will start at `http://localhost:8000` by default.

> **Important**: Always run the server from the `presentation-automator/backend` directory, not from the project root. 
> If you get an error like `ModuleNotFoundError: No module named 'src'`, it means you're not in the correct directory.

## Running the Test Server

The test server is used for development and testing purposes.

**Starting the test server:**
```bash
# Navigate to the backend directory
cd presentation-automator/backend

# Activate the virtual environment
source .venv/bin/activate

# Start the server
python -m src.main
```

**Terminating the server:**
Press `Ctrl+C` in the terminal where the server is running.

If the server is running in the background, find and terminate the process:
```bash
# Find Python processes
ps aux | grep python

# Kill the process with the identified PID
kill <PID>
```

**Troubleshooting:**
If you get port conflicts (Address already in use), find and kill the process using that port:
```bash
# Find processes using port 8000
lsof -i :8000 | grep LISTEN

# Kill the process
kill <PID>
```

## API Documentation

Once the server is running, you can access the Swagger UI documentation at:
http://localhost:8000/docs

## Running Tests

```bash
pytest
```

## Known Issues and Solutions

### OpenAI Schema Validation Issues

When using the OpenAI Agents SDK with certain models (e.g., gpt-4o), you may encounter schema validation errors like:

```
Invalid schema for response_format 'final_output': In context=('properties', 'notes'), 'default' is not permitted.
```

**Cause**: OpenAI's structured output feature has specific limitations on JSON schema attributes. In particular:

1. The `default` attribute in JSON schema is not permitted 
2. Fields with `default_factory` values also cause validation errors
3. Advanced schema features like `oneOf` and `anyOf` may be restricted

**Solution**:

1. Avoid using `default` values in Pydantic models that get converted to JSON schemas:
   ```python
   # Incorrect - will cause validation error
   notes: str = Field(default="", description="Notes")
   
   # Correct - make the field required
   notes: str = Field(..., description="Notes")
   ```

2. Don't use `default_factory` for lists or dicts:
   ```python
   # Incorrect - will cause validation error
   options: Dict[str, Any] = Field(default_factory=dict)
   
   # Correct - make the field required
   options: Dict[str, Any] = Field(...)
   ```

3. If you're building API endpoints, ensure your client sends all required fields.

4. Consider using `gpt-4o` instead of version-specific models like `gpt-4o-2024-05-13`, as newer models may have different schema validation requirements.

For more details on schema compatibility, check the OpenAI documentation on structured outputs. 
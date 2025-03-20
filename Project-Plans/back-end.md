# Presentation Automator: Backend Development Guide

This document outlines a step-by-step approach for developing the backend of the Presentation Automator using OpenAI Agent SDK. The approach focuses on incremental development, starting with the simplest possible implementation and gradually adding complexity.

## Phase 1: Setup and Initial Proof of Concept

### Step 1: Environment Setup

```bash
# Create project directory structure
mkdir -p presentation-automator/backend/src

# Create virtual environment
cd presentation-automator/backend
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install minimal dependencies
pip install fastapi uvicorn openai openai-agents python-dotenv
```

### Step 2: Basic Configuration

Create a simple environment file:

```bash
# presentation-automator/backend/.env
OPENAI_API_KEY=your_openai_api_key_here
```

### Step 3: Create a Simple Agent

Start with a single agent that generates a presentation outline from text:

```python
# presentation-automator/backend/src/simple_agent.py
import os
from dotenv import load_dotenv
from agents import Agent, Runner

# Load environment variables
load_dotenv()

# Check if OpenAI API key is set
if not os.getenv("OPENAI_API_KEY"):
    raise ValueError("OPENAI_API_KEY is not set in environment variables")

def generate_presentation_outline(text):
    """Generate a simple presentation outline from text."""
    # Create a simple agent
    agent = Agent(
        name="Presentation Outline Generator",
        instructions="""
        You are a presentation outline generator. Your task is to analyze the given text 
        and create a structured outline for a presentation.
        
        For each outline:
        1. Create a title for the presentation
        2. Identify 3-7 main sections (slides)
        3. For each section, provide a brief description of what should be included
        
        Format your response as markdown.
        """
    )
    
    # Run the agent
    result = Runner.run_sync(agent, f"Generate a presentation outline for this text:\n\n{text}")
    
    # Return the result
    return result.final_output

# Simple test if run directly
if __name__ == "__main__":
    sample_text = """
    Our company website is outdated and needs a modern redesign to better serve 
    our customers and reflect our brand values. We aim to improve user experience, 
    increase conversion rates, and enhance mobile responsiveness.
    """
    
    outline = generate_presentation_outline(sample_text)
    print(outline)
```

### Step 4: Create a Basic HTTP Server

Create a minimal FastAPI server:

```python
# presentation-automator/backend/src/server.py
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import uvicorn

from simple_agent import generate_presentation_outline

app = FastAPI(title="Presentation Automator API")

# Enable CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, replace with specific origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Define request model
class OutlineRequest(BaseModel):
    text: str

# Define a simple endpoint
@app.post("/generate-outline")
async def create_outline(request: OutlineRequest):
    try:
        outline = generate_presentation_outline(request.text)
        return {"outline": outline}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Health check endpoint
@app.get("/health")
async def health_check():
    return {"status": "healthy"}

# Run the server if executed directly
if __name__ == "__main__":
    uvicorn.run("server:app", host="0.0.0.0", port=8000, reload=True)
```

### Step 5: Test the Implementation

Create a simple test script:

```python
# presentation-automator/backend/test_api.py
import requests

# Test data
test_text = """
Our company website is outdated and needs a modern redesign to better serve 
our customers and reflect our brand values. We aim to improve user experience, 
increase conversion rates, and enhance mobile responsiveness.
"""

# Send request to the API
response = requests.post(
    "http://localhost:8000/generate-outline",
    json={"text": test_text}
)

# Print the result
print(f"Status Code: {response.status_code}")
print(response.json())
```

## Phase 2: Structured Presentation Generation

### Step 1: Define Structured Output Schema

Create a structured schema for the presentation:

```python
# presentation-automator/backend/src/schemas.py
from typing import List
from pydantic import BaseModel

class Slide(BaseModel):
    title: str
    content: str
    notes: str = ""

class Presentation(BaseModel):
    title: str
    slides: List[Slide]
```

### Step 2: Create a Structured Agent

Enhance the agent to generate structured presentations:

```python
# presentation-automator/backend/src/presentation_agent.py
import os
from dotenv import load_dotenv
from agents import Agent, Runner
from typing import List

from schemas import Presentation, Slide

# Load environment variables
load_dotenv()

def generate_structured_presentation(text):
    """Generate a structured presentation from text."""
    # Create an agent with output schema
    agent = Agent(
        name="Structured Presentation Generator",
        instructions="""
        You are a presentation generator. Your task is to analyze the given text 
        and create a structured presentation with slides.
        
        Your output should include:
        1. A clear, concise title for the presentation
        2. 3-7 slides, each with:
           - A descriptive title
           - Bullet-point content formatted in markdown
           - Optional presenter notes
        
        Keep the content focused and relevant to the main topic.
        """,
        output_type=Presentation
    )
    
    # Run the agent
    result = Runner.run_sync(agent, f"Generate a structured presentation for this text:\n\n{text}")
    
    # Return the structured result
    return result.final_output

# Test the function if run directly
if __name__ == "__main__":
    sample_text = """
    Our company website is outdated and needs a modern redesign to better serve 
    our customers and reflect our brand values. We aim to improve user experience, 
    increase conversion rates, and enhance mobile responsiveness.
    """
    
    presentation = generate_structured_presentation(sample_text)
    print(f"Title: {presentation.title}")
    print(f"Number of slides: {len(presentation.slides)}")
    for i, slide in enumerate(presentation.slides, 1):
        print(f"\nSlide {i}: {slide.title}")
        print(f"Content: {slide.content[:50]}...")
        if slide.notes:
            print(f"Notes: {slide.notes[:50]}...")
```

### Step 3: Update the API Server

Update the server to include the structured presentation endpoint:

```python
# presentation-automator/backend/src/server.py (updated)
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import uvicorn

from simple_agent import generate_presentation_outline
from presentation_agent import generate_structured_presentation
from schemas import Presentation

app = FastAPI(title="Presentation Automator API")

# Enable CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Define request model
class TextRequest(BaseModel):
    text: str

# Simple outline endpoint
@app.post("/generate-outline")
async def create_outline(request: TextRequest):
    try:
        outline = generate_presentation_outline(request.text)
        return {"outline": outline}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Structured presentation endpoint
@app.post("/generate-presentation", response_model=Presentation)
async def create_presentation(request: TextRequest):
    try:
        presentation = generate_structured_presentation(request.text)
        return presentation
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Health check endpoint
@app.get("/health")
async def health_check():
    return {"status": "healthy"}

# Run the server if executed directly
if __name__ == "__main__":
    uvicorn.run("server:app", host="0.0.0.0", port=8000, reload=True)
```

## Phase 3: Multi-Stage Processing with Tools

### Step 1: Create Document Processing Tool

Add a tool for extracting key points from text:

```python
# presentation-automator/backend/src/tools.py
from agents import function_tool

def extract_key_points(text: str) -> str:
    """
    Extract key points from a text document.
    
    Args:
        text: The text to analyze
        
    Returns:
        A bullet-point list of key points
    """
    # This is a placeholder - in a real implementation, this might use
    # another agent call or some text processing algorithm
    return "Key points extracted from the document"
```

### Step 2: Implement the Planning Agent

Create an agent that plans the presentation structure:

```python
# presentation-automator/backend/src/planning_agent.py
import os
from typing import List, Dict
from pydantic import BaseModel
from dotenv import load_dotenv
from agents import Agent, Runner, function_tool

from tools import extract_key_points

# Load environment variables
load_dotenv()

# Define output schema
class PresentationPlan(BaseModel):
    title: str
    themes: List[str]
    sections: List[Dict[str, str]]

def create_presentation_plan(text):
    """Create a presentation plan from text."""
    # Create the planning agent
    agent = Agent(
        name="Presentation Planner",
        instructions="""
        You are a presentation planner. Your task is to analyze the given text 
        and create a structured plan for a presentation.
        
        Your output should include:
        1. A clear, concise title for the presentation
        2. Suggested themes/styles for the presentation
        3. A list of sections (slides), each with a title and key points to cover
        
        Use the extract_key_points tool to help identify important information
        in the document.
        """,
        output_type=PresentationPlan,
        tools=[function_tool(extract_key_points)]
    )
    
    # Run the agent
    result = Runner.run_sync(agent, f"Create a presentation plan for this text:\n\n{text}")
    
    # Return the structured result
    return result.final_output

# Test function if run directly
if __name__ == "__main__":
    sample_text = """
    Our company website is outdated and needs a modern redesign to better serve 
    our customers and reflect our brand values. We aim to improve user experience, 
    increase conversion rates, and enhance mobile responsiveness.
    """
    
    plan = create_presentation_plan(sample_text)
    print(f"Title: {plan.title}")
    print(f"Themes: {', '.join(plan.themes)}")
    print(f"Number of sections: {len(plan.sections)}")
    for i, section in enumerate(plan.sections, 1):
        print(f"\nSection {i}: {section['title']}")
```

### Step 3: Implement the Content Generation Agent

Create an agent that generates detailed content based on the plan:

```python
# presentation-automator/backend/src/content_agent.py
import os
from typing import List
from dotenv import load_dotenv
from agents import Agent, Runner

from schemas import Presentation, Slide
from planning_agent import PresentationPlan

# Load environment variables
load_dotenv()

def generate_content(plan: PresentationPlan):
    """Generate detailed content based on a presentation plan."""
    # Create a content generation agent
    agent = Agent(
        name="Content Generator",
        instructions="""
        You are a presentation content generator. Your task is to create detailed slide 
        content based on the provided presentation plan.
        
        For each section in the plan:
        1. Create a slide with a clear title
        2. Generate concise, engaging content formatted in markdown
        3. Add helpful presenter notes
        
        Ensure the content flows logically and maintains a consistent style.
        """,
        output_type=Presentation
    )
    
    # Convert the plan to a string representation for the agent
    plan_text = f"""
    PRESENTATION PLAN:
    Title: {plan.title}
    Themes: {', '.join(plan.themes)}
    
    SECTIONS:
    """
    
    for i, section in enumerate(plan.sections, 1):
        plan_text += f"\n{i}. {section['title']}\n"
        if 'key_points' in section:
            plan_text += f"   Key points: {section['key_points']}\n"
    
    # Run the agent
    result = Runner.run_sync(agent, f"Generate detailed presentation content based on this plan:\n\n{plan_text}")
    
    # Return the structured presentation
    return result.final_output

# Test function if run directly
if __name__ == "__main__":
    from planning_agent import create_presentation_plan
    
    sample_text = """
    Our company website is outdated and needs a modern redesign to better serve 
    our customers and reflect our brand values. We aim to improve user experience, 
    increase conversion rates, and enhance mobile responsiveness.
    """
    
    plan = create_presentation_plan(sample_text)
    presentation = generate_content(plan)
    
    print(f"Title: {presentation.title}")
    print(f"Number of slides: {len(presentation.slides)}")
    for i, slide in enumerate(presentation.slides, 1):
        print(f"\nSlide {i}: {slide.title}")
        print(f"Content: {slide.content[:50]}...")
```

### Step 4: Create a Pipeline Coordinator

Coordinate the multi-step process:

```python
# presentation-automator/backend/src/coordinator.py
from typing import Dict, Any

from planning_agent import create_presentation_plan
from content_agent import generate_content
from schemas import Presentation

async def generate_full_presentation(text: str) -> Presentation:
    """
    Generate a full presentation using a multi-stage approach.
    
    Args:
        text: The input text to generate a presentation from
        
    Returns:
        A structured presentation
    """
    # Step 1: Create a presentation plan
    plan = create_presentation_plan(text)
    
    # Step 2: Generate detailed content based on the plan
    presentation = generate_content(plan)
    
    return presentation
```

### Step 5: Implement Context Sharing Between Agents

Enhance the coordinator to use the OpenAI Agents SDK's context parameter for sharing information between agents:

```python
# presentation-automator/backend/src/coordinator.py (updated with context)
import time
from typing import Dict, Any

from planning_agent import create_presentation_plan
from content_agent import generate_content
from schemas import Presentation

async def generate_full_presentation(text: str) -> Presentation:
    """
    Generate a full presentation using a multi-stage approach with shared context.
    
    Args:
        text: The input text to generate a presentation from
        
    Returns:
        A structured presentation
    """
    # Create a shared context to pass between agents
    context = {
        "original_document": text,
        "document_statistics": {
            "word_count": len(text.split()),
            "character_count": len(text),
            "paragraphs": len(text.split("\n\n"))
        },
        "processing_metadata": {
            "start_time": time.time(),
            "stages_completed": []
        }
    }
    
    # Step 1: Create a presentation plan using shared context
    from agents import Runner
    
    # Get planning agent
    plan_result = await Runner.run(
        create_presentation_plan(),
        f"Create a presentation plan for this text:\n\n{text}",
        context=context  # Pass context as a named parameter
    )
    plan = plan_result.final_output
    
    # Update context with plan information
    context["plan"] = plan.dict()
    context["processing_metadata"]["stages_completed"].append("planning")
    
    # Step 2: Generate detailed content using the updated context
    content_result = await Runner.run(
        generate_content(),
        f"Generate detailed presentation content based on the plan",
        context=context  # Pass the same context object
    )
    presentation = content_result.final_output
    
    # Update context with final statistics
    context["processing_metadata"]["end_time"] = time.time()
    context["processing_metadata"]["total_time"] = (
        context["processing_metadata"]["end_time"] - 
        context["processing_metadata"]["start_time"]
    )
    
    return presentation
```

Now, update the agent functions to accept and use the context:

```python
# presentation-automator/backend/src/planning_agent.py (updated for context)
import os
from typing import List, Dict
from pydantic import BaseModel
from dotenv import load_dotenv
from agents import Agent, Runner, function_tool

from tools import extract_key_points_with_context

# Load environment variables
load_dotenv()

# Define output schema
class PresentationPlan(BaseModel):
    title: str
    themes: List[str]
    sections: List[Dict[str, str]]

def create_presentation_plan():
    """Create a planning agent that uses context."""
    # Create the planning agent
    agent = Agent(
        name="Presentation Planner",
        instructions="""
        You are a presentation planner. Your task is to analyze the given text 
        and create a structured plan for a presentation.
        
        Your output should include:
        1. A clear, concise title for the presentation
        2. Suggested themes/styles for the presentation
        3. A list of sections (slides), each with a title and key points to cover
        
        Use the extract_key_points tool to help identify important information
        in the document.
        """,
        output_type=PresentationPlan,
        tools=[function_tool(extract_key_points_with_context)]
    )
    
    return agent
```

Also, update the tools to be context-aware:

```python
# presentation-automator/backend/src/tools.py (updated with context)
from agents import function_tool
from agents.run_context import RunContextWrapper

def extract_key_points_with_context(ctx: RunContextWrapper, text: str = None) -> str:
    """
    Extract key points from a text document using context awareness.
    
    Args:
        ctx: The context wrapper, containing shared context
        text: The text to analyze (optional, will use context if not provided)
        
    Returns:
        A bullet-point list of key points
    """
    # Access context information
    context = ctx.context
    
    # Get the document text from context if not provided
    if text is None and "original_document" in context:
        text = context["original_document"]
    
    # Log tool usage for analytics
    if "tool_usage" not in context:
        context["tool_usage"] = {}
    if "extract_key_points" not in context["tool_usage"]:
        context["tool_usage"]["extract_key_points"] = 0
    context["tool_usage"]["extract_key_points"] += 1
    
    # Use document statistics from context to inform extraction behavior
    document_stats = context.get("document_statistics", {})
    word_count = document_stats.get("word_count", 0)
    
    # Determine how many points to extract based on document length
    if word_count < 200:
        # For short documents, extract fewer points
        points_to_extract = 3
    elif word_count < 1000:
        points_to_extract = 5
    else:
        points_to_extract = 8
    
    # Here we would implement actual extraction logic
    # For now, we'll return a placeholder
    return f"Extracted {points_to_extract} key points from the document"
```

Similarly, update the content agent:

```python
# presentation-automator/backend/src/content_agent.py (updated for context)
import os
from typing import List
from dotenv import load_dotenv
from agents import Agent, Runner

from schemas import Presentation, Slide
from planning_agent import PresentationPlan

# Load environment variables
load_dotenv()

def generate_content():
    """Create a content generation agent that uses context."""
    # Create a content generation agent
    agent = Agent(
        name="Content Generator",
        instructions="""
        You are a presentation content generator. Your task is to create detailed slide 
        content based on the provided presentation plan in the context.
        
        For each section in the plan:
        1. Create a slide with a clear title
        2. Generate concise, engaging content formatted in markdown
        3. Add helpful presenter notes
        
        Ensure the content flows logically and maintains a consistent style.
        """,
        output_type=Presentation
    )
    
    return agent
```

Advantages of using context in our pipeline:

1. **Shared State**: All components have access to the same data
2. **Reduced Redundancy**: Document analysis only happens once
3. **Metadata Tracking**: Easily track processing time and stages
4. **Enhanced Tools**: Tools can adapt behavior based on document properties
5. **Future Extensibility**: Adding new components that share data becomes simpler

### Step 6: Update the API Server

Update the server to use the coordinator:

```python
# presentation-automator/backend/src/server.py (updated)
from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import uvicorn
import asyncio

from coordinator import generate_full_presentation
from schemas import Presentation

app = FastAPI(title="Presentation Automator API")

# Enable CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Define request model
class TextRequest(BaseModel):
    text: str

# Full presentation generation endpoint
@app.post("/api/generate", response_model=Presentation)
async def create_full_presentation(request: TextRequest):
    try:
        presentation = await generate_full_presentation(request.text)
        return presentation
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Health check endpoint
@app.get("/health")
async def health_check():
    return {"status": "healthy"}

# Run the server if executed directly
if __name__ == "__main__":
    uvicorn.run("server:app", host="0.0.0.0", port=8000, reload=True)
```

## Phase 4: Enhancing with Advanced Features

### Step 1: Add Document Processing Tools

Add tools to process different document types:

```python
# presentation-automator/backend/src/document_tools.py
import os
from typing import BinaryIO

# Note: Install these packages first: python-docx, PyPDF2
import docx
import PyPDF2

def extract_text_from_docx(file: BinaryIO) -> str:
    """Extract text from a .docx file"""
    doc = docx.Document(file)
    full_text = []
    for para in doc.paragraphs:
        full_text.append(para.text)
    return "\n".join(full_text)

def extract_text_from_pdf(file: BinaryIO) -> str:
    """Extract text from a PDF file"""
    reader = PyPDF2.PdfReader(file)
    text = ""
    for page in reader.pages:
        text += page.extract_text() + "\n"
    return text
```

### Step 2: Create a Document Processor Service

Create a service to handle document processing:

```python
# presentation-automator/backend/src/document_processor.py
import os
from typing import BinaryIO, Optional
from fastapi import UploadFile

from document_tools import extract_text_from_docx, extract_text_from_pdf

async def process_document(file: UploadFile) -> str:
    """
    Process an uploaded document and extract its text content.
    
    Args:
        file: The uploaded file
        
    Returns:
        The extracted text content
    
    Raises:
        ValueError: If the file format is not supported
    """
    # Get the file extension
    filename = file.filename
    extension = os.path.splitext(filename)[1].lower() if filename else ""
    
    # Read file content
    contents = await file.read()
    
    # Process based on file type
    if extension == ".docx":
        # Create a temporary file-like object
        import io
        docx_file = io.BytesIO(contents)
        return extract_text_from_docx(docx_file)
    
    elif extension == ".pdf":
        # Create a temporary file-like object
        import io
        pdf_file = io.BytesIO(contents)
        return extract_text_from_pdf(pdf_file)
    
    elif extension in [".txt", ".md"]:
        # Plain text or markdown
        return contents.decode("utf-8")
    
    else:
        raise ValueError(f"Unsupported file format: {extension}")
```

### Step 3: Update the API for File Uploads

Add file upload support to the API:

```python
# presentation-automator/backend/src/server.py (updated)
from fastapi import FastAPI, HTTPException, File, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import uvicorn

from coordinator import generate_full_presentation
from document_processor import process_document
from schemas import Presentation

app = FastAPI(title="Presentation Automator API")

# Enable CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Define request model
class TextRequest(BaseModel):
    text: str

# Text-based generation endpoint
@app.post("/api/generate", response_model=Presentation)
async def create_from_text(request: TextRequest):
    try:
        presentation = await generate_full_presentation(request.text)
        return presentation
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# File upload endpoint
@app.post("/api/generate-from-file", response_model=Presentation)
async def create_from_file(file: UploadFile = File(...)):
    try:
        # Process the document
        text = await process_document(file)
        
        # Generate presentation
        presentation = await generate_full_presentation(text)
        return presentation
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Health check endpoint
@app.get("/health")
async def health_check():
    return {"status": "healthy"}

# Run the server if executed directly
if __name__ == "__main__":
    uvicorn.run("server:app", host="0.0.0.0", port=8000, reload=True)
```

### Step 4: Add Caching for Performance

Implement simple caching to improve performance:

```python
# presentation-automator/backend/src/cache.py
import hashlib
import json
import os
from typing import Any, Dict, Optional
import time

# Simple file-based cache
class SimpleCache:
    def __init__(self, cache_dir="./cache", ttl=3600):
        """
        Initialize a simple cache.
        
        Args:
            cache_dir: Directory to store cache files
            ttl: Time-to-live in seconds (default: 1 hour)
        """
        self.cache_dir = cache_dir
        self.ttl = ttl
        
        # Create cache directory if it doesn't exist
        os.makedirs(cache_dir, exist_ok=True)
    
    def _get_cache_path(self, key: str) -> str:
        """Get the file path for a cache key"""
        # Create a hash of the key
        key_hash = hashlib.md5(key.encode()).hexdigest()
        return os.path.join(self.cache_dir, f"{key_hash}.json")
    
    def get(self, key: str) -> Optional[Any]:
        """Get a value from the cache"""
        cache_path = self._get_cache_path(key)
        
        # Check if cache file exists
        if not os.path.exists(cache_path):
            return None
        
        try:
            # Read cache file
            with open(cache_path, "r") as f:
                cache_data = json.load(f)
            
            # Check if cache is expired
            if time.time() - cache_data["timestamp"] > self.ttl:
                return None
            
            return cache_data["value"]
        except Exception:
            # If anything goes wrong, return None
            return None
    
    def set(self, key: str, value: Any) -> None:
        """Set a value in the cache"""
        cache_path = self._get_cache_path(key)
        
        # Create cache data
        cache_data = {
            "timestamp": time.time(),
            "value": value
        }
        
        # Write to cache file
        with open(cache_path, "w") as f:
            json.dump(cache_data, f)
```

### Step 5: Update the Coordinator to Use Caching

Enhance the coordinator with caching:

```python
# presentation-automator/backend/src/coordinator.py (updated)
import hashlib
from typing import Dict, Any

from planning_agent import create_presentation_plan
from content_agent import generate_content
from schemas import Presentation
from cache import SimpleCache

# Create a cache instance
cache = SimpleCache()

async def generate_full_presentation(text: str) -> Presentation:
    """
    Generate a full presentation using a multi-stage approach.
    
    Args:
        text: The input text to generate a presentation from
        
    Returns:
        A structured presentation
    """
    # Generate a cache key based on the input text
    cache_key = f"presentation:{hashlib.md5(text.encode()).hexdigest()}"
    
    # Check cache
    cached_result = cache.get(cache_key)
    if cached_result:
        # Convert dict back to Presentation
        return Presentation(**cached_result)
    
    # Step 1: Create a presentation plan
    plan = create_presentation_plan(text)
    
    # Step 2: Generate detailed content based on the plan
    presentation = generate_content(plan)
    
    # Cache the result
    cache.set(cache_key, presentation.dict())
    
    return presentation
```

## Phase 5: Error Handling and Logging

### Step 1: Create a Logging Module

Add structured logging:

```python
# presentation-automator/backend/src/logger.py
import logging
import os
import sys
from typing import Optional

def setup_logger(name: str, log_level: Optional[str] = None) -> logging.Logger:
    """
    Set up a logger with the specified name and log level.
    
    Args:
        name: Logger name
        log_level: Log level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        
    Returns:
        Configured logger
    """
    # Get log level from environment if not provided
    if log_level is None:
        log_level = os.getenv("LOG_LEVEL", "INFO").upper()
    
    # Create logger
    logger = logging.getLogger(name)
    logger.setLevel(getattr(logging, log_level))
    
    # Create handler if not already added
    if not logger.handlers:
        handler = logging.StreamHandler(sys.stdout)
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        handler.setFormatter(formatter)
        logger.addHandler(handler)
    
    return logger
```

### Step 2: Implement Error Handling

Add error handling for the agents:

```python
# presentation-automator/backend/src/error_handler.py
from typing import Dict, Any, Callable, TypeVar, cast
import functools
import logging

from logger import setup_logger

logger = setup_logger("error_handler")

T = TypeVar('T')
F = TypeVar('F', bound=Callable[..., Any])

class AgentError(Exception):
    """Base class for agent-related errors"""
    pass

class DocumentProcessingError(Exception):
    """Error during document processing"""
    pass

def handle_agent_errors(func: F) -> F:
    """
    Decorator to handle errors in agent functions.
    
    Args:
        func: The function to decorate
        
    Returns:
        Decorated function
    """
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except Exception as e:
            logger.error(f"Error in {func.__name__}: {str(e)}")
            raise AgentError(f"Failed to process with agent: {str(e)}") from e
            
    return cast(F, wrapper)
```

### Step 3: Update Coordinator with Error Handling

Apply error handling to the coordinator:

```python
# presentation-automator/backend/src/coordinator.py (updated)
import hashlib
from typing import Dict, Any

from planning_agent import create_presentation_plan
from content_agent import generate_content
from schemas import Presentation
from cache import SimpleCache
from error_handler import handle_agent_errors, AgentError
from logger import setup_logger

# Set up logger
logger = setup_logger("coordinator")

# Create a cache instance
cache = SimpleCache()

@handle_agent_errors
async def generate_full_presentation(text: str) -> Presentation:
    """
    Generate a full presentation using a multi-stage approach.
    
    Args:
        text: The input text to generate a presentation from
        
    Returns:
        A structured presentation
    """
    logger.info("Starting presentation generation")
    
    # Generate a cache key based on the input text
    cache_key = f"presentation:{hashlib.md5(text.encode()).hexdigest()}"
    
    # Check cache
    cached_result = cache.get(cache_key)
    if cached_result:
        logger.info("Returning cached presentation")
        # Convert dict back to Presentation
        return Presentation(**cached_result)
    
    # Step 1: Create a presentation plan
    logger.info("Creating presentation plan")
    plan = create_presentation_plan(text)
    
    # Step 2: Generate detailed content based on the plan
    logger.info("Generating presentation content")
    presentation = generate_content(plan)
    
    # Cache the result
    cache.set(cache_key, presentation.dict())
    
    logger.info("Presentation generation complete")
    return presentation
```

## Conclusion

This development approach follows a gradual path from a simple proof-of-concept to a more robust implementation:

1. **Phase 1**: Start with the absolute minimum to prove the concept works - a single agent and a basic API.
2. **Phase 2**: Add structured data models to make the output more useful for the frontend.
3. **Phase 3**: Implement a multi-stage process with dedicated agents for planning and content generation.
4. **Phase 4**: Add more practical features like document processing and caching.
5. **Phase 5**: Improve robustness with proper error handling and logging.

Each phase builds incrementally on the previous one, allowing for testing and validation at each step. The OpenAI Agent SDK is used throughout as the core technology for generating the presentations, leveraging structured output schemas and tools.

By following this approach, you can quickly get a working proof-of-concept and then gradually enhance it with more features and robustness as needed. 
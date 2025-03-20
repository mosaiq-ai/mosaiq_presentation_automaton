# OpenAI Agents SDK and Response API Documentation

This document provides comprehensive information about the OpenAI Agents SDK, its components, and how to use it effectively in your applications.

## Table of Contents
- [Overview](#overview)
- [Installation](#installation)
- [Core Components](#core-components)
  - [Agent](#agent)
  - [Runner](#runner)
  - [ModelSettings](#modelsettings)
  - [Tools](#tools)
  - [Tracing](#tracing)
  - [Handoffs](#handoffs)
  - [Guardrails](#guardrails)
  - [RunConfig](#runconfig)
  - [AgentOutputSchema](#agentoutputschema)
  - [Context Usage](#context-usage)
- [Responses API vs Chat Completions API](#responses-api-vs-chat-completions-api)
- [Examples](#examples)
- [Best Practices](#best-practices)
- [Common Issues](#common-issues)
- [Compatibility Notes](#compatibility-notes)

## Overview

The OpenAI Agents SDK is a Python framework designed to streamline the development of LLM-powered agents. It provides a structured way to define agents, tools, and workflows.

Key features:
- **Agent loop**: Handles calling tools, sending results to the LLM, and looping until the task is complete
- **Python-first**: Uses built-in language features instead of requiring new abstractions
- **Handoffs**: Facilitates coordination and delegation between multiple agents
- **Guardrails**: Validates inputs and outputs in parallel to agent execution
- **Function tools**: Converts any Python function into a tool with automatic schema generation
- **Tracing**: Built-in tracing for debugging, monitoring, and evaluation

## Installation

```bash
pip install openai-agents
```

Set up your OpenAI API key:
```bash
export OPENAI_API_KEY=sk-...
```

## Core Components

### Agent

The `Agent` class is the primary building block for creating LLM-powered agents with the SDK.

**Constructor Parameters:**
- `name` (str): A name for the agent (required)
- `instructions` (str): System instructions/prompt for the agent
- `handoff_description` (str, optional): Description used when other agents might hand off to this agent
- `handoffs` (list, optional): List of agents this agent can hand off to
- `model` (str, optional): The model to use (e.g., "gpt-4o-2024-05-13", "o3-mini")
- `model_settings` (ModelSettings, optional): Configuration for the model
- `tools` (list, optional): List of tools available to the agent
- `input_guardrails` (list, optional): List of input validation guardrails
- `output_guardrails` (list, optional): List of output validation guardrails
- `output_type` (Type, optional): Expected type of the agent's output

**Example:**
```python
from agents import Agent

agent = Agent(
    name="Math Tutor",
    instructions="You provide help with math problems. Explain your reasoning step by step.",
    handoff_description="Specialist agent for mathematical questions",
    model="gpt-4o-2024-05-13",
)
```

### Runner

The `Runner` class executes agent workflows.

**Key Methods:**
- `run()`: Runs an agent asynchronously
- `run_sync()`: Runs an agent synchronously (blocking)

**Parameters:**
- `agent`: The agent to run
- `messages` or `input`: The input to the agent (can be a string or a list of message objects)
- `context` (optional): Context object to pass to the agent and tools (must be passed as a named parameter)
- `run_config` (RunConfig, optional): Configuration for the run

**Example:**
```python
from agents import Runner

result = await Runner.run(
    agent, 
    [{"role": "user", "content": "Solve 2x + 5 = 13"}],
    context={},  # Must be passed as a named parameter
    run_config=RunConfig(temperature=0.3)
)

# Access the result
output = result.final_output
```

### ModelSettings

The `ModelSettings` class configures the behavior of the model used by an agent.

**Parameters:**
- `temperature` (float, optional): Controls randomness (0.0 to 1.0)
- `top_p` (float, optional): Controls diversity via nucleus sampling
- `frequency_penalty` (float, optional): Reduces repetition of token sequences
- `presence_penalty` (float, optional): Reduces repetition of topics
- `tool_choice` (str, optional): How tools should be used ('auto', 'required', 'none')
- `parallel_tool_calls` (bool, optional): Whether to allow parallel tool calls
- `truncation` (str, optional): Truncation strategy ('auto', 'disabled')
- `max_tokens` (int, optional): Maximum tokens to generate

**Example:**
```python
from agents import Agent, ModelSettings

agent = Agent(
    name="Creative Writer",
    instructions="Write creative stories based on prompts.",
    model="gpt-4o-2024-05-13",
    model_settings=ModelSettings(
        temperature=0.7,
        top_p=0.95,
        frequency_penalty=0.2,
        presence_penalty=0.2
    )
)
```

### Tools

Tools allow agents to interact with external systems or execute specific functions.

**Function Tools:**
```python
from agents import Agent, function_tool

def get_weather(city: str) -> str:
    """Get the current weather for a city."""
    # Implementation here
    return f"The weather in {city} is sunny"

agent = Agent(
    name="Weather Assistant",
    instructions="Provide weather information when asked.",
    tools=[function_tool(get_weather)]
)
```

### Tracing

The SDK includes a tracing system for monitoring and debugging agent execution.

**Key Components:**
- `SpanData`: Contains information about a specific span within a trace
- `trace()`: Context manager for creating traces
- `add_trace_processor()`: Registers a processor to handle trace events

**Span Data Structure:**
- `span_data`: Contains the internal span information
  - `type`: Type of the span event (e.g., "agent_started", "agent_completed", "agent_error")
  - `data`: Dictionary with span-specific data like run_id and final_output

**Example:**
```python
import agents
from agents.tracing import SpanData

def my_trace_handler(span: SpanData) -> None:
    if hasattr(span, 'span_data') and hasattr(span.span_data, 'type'):
        span_type = span.span_data.type
        
        if span_type == "agent_started":
            run_id = span.span_data.data.get('run_id') if hasattr(span.span_data, 'data') else None
            print(f"Agent started - Run ID: {run_id}")
        elif span_type == "agent_completed":
            run_id = span.span_data.data.get('run_id') if hasattr(span.span_data, 'data') else None
            final_output = span.span_data.data.get('final_output') if hasattr(span.span_data, 'data') else None
            print(f"Agent completed - Run ID: {run_id}")
            print(f"Final output: {final_output}")

# Register the trace handler
agents.add_trace_processor(my_trace_handler)
```

### Handoffs

Handoffs allow agents to delegate tasks to other specialized agents.

**Example:**
```python
from agents import Agent

math_agent = Agent(
    name="Math Agent",
    handoff_description="Specialist for math problems",
    instructions="Solve math problems step by step."
)

physics_agent = Agent(
    name="Physics Agent",
    handoff_description="Specialist for physics problems",
    instructions="Solve physics problems using equations and explanations.",
    handoffs=[math_agent]  # Physics agent can hand off to math agent
)
```

### Guardrails

Guardrails provide input and output validation for agents.

**Types:**
- `InputGuardrail`: Validates inputs before agent processing
- `OutputGuardrail`: Validates outputs after agent processing

**Example:**
```python
from agents import Agent, output_guardrail, GuardrailFunctionOutput, RunContextWrapper

@output_guardrail
async def content_validation_guardrail(
    ctx: RunContextWrapper, 
    agent: Agent, 
    output: Any
) -> GuardrailFunctionOutput:
    """Validate that the output content meets quality standards."""
    is_valid = True
    reason = "Content validation passed"
    
    # Perform validation logic here
    if not output or (hasattr(output, 'content') and not output.content):
        is_valid = False
        reason = "Content cannot be empty"
    
    return GuardrailFunctionOutput(is_valid=is_valid, reason=reason)

# Usage
agent = Agent(
    name="Content Creator",
    instructions="Generate blog post content.",
    output_guardrails=[content_validation_guardrail],
    # ...other parameters
)
```

### RunConfig

The `RunConfig` class configures a specific run of an agent.

**Parameters:**
- `model` (str | Model | None): Override the model to use for the run
- `model_settings` (ModelSettings | None): Override model settings for the run
- `workflow_name` (str): Name of the workflow for tracing purposes
- `trace_id` (str | None): Custom trace ID for tracing (do not use `trace_id_generator`, which is deprecated)
- `group_id` (str | None): ID to group related traces together
- `trace_metadata` (dict | None): Additional metadata for traces
- `tracing_disabled` (bool): Whether to disable tracing
- `trace_include_sensitive_data` (bool): Whether to include sensitive data in traces
- `handoff_input_filter` (callable | None): Filter for inputs during handoffs
- `input_guardrails` (list | None): Override input guardrails
- `output_guardrails` (list | None): Override output guardrails

**Example:**
```python
from agents import Runner, RunConfig, ModelSettings

result = await Runner.run(
    agent,
    "Generate a story about space exploration",
    context={},
    run_config=RunConfig(
        model="gpt-4o-2024-05-13",
        model_settings=ModelSettings(temperature=0.8),
        workflow_name="story_generation",
        trace_id=f"story_{int(time.time())}",
        trace_metadata={"category": "science_fiction"}
    )
)
```

### AgentOutputSchema

The `AgentOutputSchema` class defines the structure of the expected output from an agent. It's used to enforce structured outputs in the right format.

**Parameters:**
- `output_type` (Type): The expected output type
- `strict_json_schema` (bool): Whether to enforce strict schema validation

**Example:**
```python
from pydantic import BaseModel
from agents import Agent, AgentOutputSchema
from typing import List

class StoryOutput(BaseModel):
    title: str
    chapters: List[str]
    
agent = Agent(
    name="Story Generator",
    instructions="Generate a short story with chapters.",
    output_type=StoryOutput  # Agent will use this to create the output schema
)

# Alternatively, create a custom schema
custom_schema = AgentOutputSchema(StoryOutput)
```

### Context Usage

The `context` parameter in the OpenAI Agents SDK provides a powerful mechanism for sharing information between agents, tools, and other components in your application. Understanding how to use context effectively can significantly improve your agent workflows, especially for multi-stage processes like our Presentation Automator.

**What is Context?**

Context is a user-defined object that can be passed to the `Runner.run()` method. It's then made available to tools, agents, guardrails, and other components throughout the execution of the agent workflow. Unlike conversations or messages that are passed to the LLM, context is only available to your code, not to the model itself.

**Key Features of Context:**
- Must be passed as a named parameter to `Runner.run()`
- Can be any Python object (dictionary, custom class, etc.)
- Is wrapped in a `RunContextWrapper` when passed to tools and other components
- Can be used to maintain state across agent runs, tool calls, and handoffs
- Allows for sharing data across different parts of your application without global variables

**Example: Basic Context Usage**

```python
# Create a dictionary as context
context = {
    "user_preferences": {
        "theme": "corporate",
        "slide_count": 10,
        "include_notes": True
    },
    "processing_metadata": {
        "start_time": time.time(),
        "document_length": len(document_text)
    }
}

# Run agent with context
result = await Runner.run(
    agent,
    "Generate a presentation about digital transformation",
    context=context  # Must be named parameter
)
```

**Using Context in the Presentation Automator**

In our Presentation Automator project, context can be leveraged in several powerful ways:

1. **Information Sharing Between Agents**

```python
# coordinator.py
async def generate_full_presentation(text: str) -> Presentation:
    """Generate a full presentation using a multi-stage approach."""
    
    # Create a shared context
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
    plan_result = await Runner.run(
        planning_agent,
        "Create a presentation plan",
        context=context
    )
    plan = plan_result.final_output
    
    # Update context with plan information
    context["plan"] = plan.model_dump()
    context["processing_metadata"]["stages_completed"].append("planning")
    
    # Step 2: Generate detailed content using the same context
    content_result = await Runner.run(
        content_agent,
        "Generate presentation content",
        context=context
    )
    presentation = content_result.final_output
    
    # Update context with final statistics
    context["processing_metadata"]["end_time"] = time.time()
    context["processing_metadata"]["total_time"] = context["processing_metadata"]["end_time"] - context["processing_metadata"]["start_time"]
    
    return presentation
```

2. **Context-Aware Tools**

```python
# tools.py
from agents import function_tool
from agents.run_context import RunContextWrapper

def extract_key_points_with_context(ctx: RunContextWrapper, text: str) -> str:
    """
    Extract key points from a text document using context awareness.
    
    Args:
        ctx: The context wrapper, containing shared context
        text: The text to analyze
        
    Returns:
        A bullet-point list of key points
    """
    # Access context information
    context = ctx.context
    document_stats = context.get("document_statistics", {})
    
    # Log tool usage
    if "tool_usage" not in context:
        context["tool_usage"] = {}
    if "extract_key_points" not in context["tool_usage"]:
        context["tool_usage"]["extract_key_points"] = 0
    context["tool_usage"]["extract_key_points"] += 1
    
    # Use context to inform extraction behavior
    word_count = document_stats.get("word_count", 0)
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

# Register the tool with your agent
planning_agent = Agent(
    name="Presentation Planner",
    instructions="Create a structured plan for a presentation",
    tools=[function_tool(extract_key_points_with_context)]
)
```

3. **Dynamic Instructions with Context**

```python
# planning_agent.py
def generate_dynamic_instructions(ctx: RunContextWrapper, agent: Agent) -> str:
    """Generate dynamic instructions based on context."""
    context = ctx.context
    
    # Default instructions
    base_instructions = """
    You are a presentation planner. Your task is to analyze the given text 
    and create a structured plan for a presentation.
    """
    
    # Add custom instructions based on context
    if "user_preferences" in context:
        prefs = context["user_preferences"]
        if "theme" in prefs:
            base_instructions += f"\nUse a {prefs['theme']} style for the presentation."
        if "slide_count" in prefs:
            base_instructions += f"\nAim to create approximately {prefs['slide_count']} slides."
    
    # Add processing information if available
    if "document_statistics" in context:
        stats = context["document_statistics"]
        if stats.get("word_count", 0) < 300:
            base_instructions += "\nThis is a short document, so create a concise presentation."
    
    return base_instructions

# Use dynamic instructions for the agent
planning_agent = Agent(
    name="Presentation Planner",
    instructions=generate_dynamic_instructions,
    output_type=PresentationPlan
)
```

4. **Context in Guardrails**

```python
# guardrails.py
from agents import output_guardrail, GuardrailFunctionOutput

@output_guardrail
async def slide_count_guardrail(ctx: RunContextWrapper, agent: Agent, output: Presentation) -> GuardrailFunctionOutput:
    """Ensure the presentation meets user's slide count preferences."""
    
    context = ctx.context
    user_prefs = context.get("user_preferences", {})
    preferred_count = user_prefs.get("slide_count")
    
    # If no preference is set, accept any slide count
    if not preferred_count:
        return GuardrailFunctionOutput(is_valid=True)
    
    actual_count = len(output.slides)
    # Allow some flexibility in slide count
    min_slides = max(3, int(preferred_count * 0.7))
    max_slides = int(preferred_count * 1.3)
    
    if actual_count < min_slides:
        return GuardrailFunctionOutput(
            is_valid=False,
            reason=f"Presentation has too few slides ({actual_count}). User preference: ~{preferred_count} slides."
        )
    elif actual_count > max_slides:
        return GuardrailFunctionOutput(
            is_valid=False,
            reason=f"Presentation has too many slides ({actual_count}). User preference: ~{preferred_count} slides."
        )
    
    return GuardrailFunctionOutput(is_valid=True)
```

**Benefits of Using Context in the Presentation Automator**

1. **State Management**: Maintains state across multiple agent runs without global variables

2. **Efficiency**: Reduces redundant computation by sharing processed data between pipeline stages

3. **Customization**: Enables dynamic agent behavior based on document characteristics and user preferences

4. **Monitoring**: Tracks performance and resource usage throughout the generation process

5. **Debugging**: Provides rich context for troubleshooting when errors occur

6. **Extensibility**: Makes it easy to add new agents or tools that can leverage existing context data

By effectively using context throughout the Presentation Automator, you can create a more coherent, efficient, and customizable generation pipeline that's also easier to debug and extend.

## Responses API vs Chat Completions API

The OpenAI ecosystem offers two primary APIs for working with language models: the Chat Completions API and the newer Responses API. Understanding their differences is crucial for choosing the right approach for your application.

### Chat Completions API

The Chat Completions API is the traditional way to interact with OpenAI's language models:

**Key Characteristics:**
- Simpler, more direct interaction with models
- Well-established with extensive documentation
- Focuses primarily on text generation
- Requires manual handling of conversation history
- Limited built-in tool use functionality (requires manual implementation)

**Best Used For:**
- Straightforward text generation tasks
- When you need complete control over the conversation flow
- Simpler applications that don't require complex tool integration

**Code Example:**
```python
from openai import OpenAI
client = OpenAI()

response = client.chat.completions.create(
  model="gpt-4o",
  messages=[
    {"role": "system", "content": "You are a helpful assistant."},
    {"role": "user", "content": "Write a haiku about programming."}
  ]
)
print(response.choices[0].message.content)
```

### Responses API

The Responses API is OpenAI's newer approach, launched in March 2025, designed to combine the simplicity of Chat Completions with more advanced features:

**Key Characteristics:**
- Combines the simplicity of Chat Completions with the tool use and state management of Assistants API
- Built-in support for tools like web search, file search, and computer use
- More structured approach to handling multimodal inputs
- Designed for building agentic experiences
- Explicit support for reasoning capabilities

**Best Used For:**
- Applications requiring built-in tool usage
- Complex agentic systems
- When you need more structured outputs
- Applications dealing with multimodal inputs (text, images, files)

**Code Example:**
```python
from openai import OpenAI
client = OpenAI()

response = client.responses.create(
  model="gpt-4o",
  input=[
    {
      "role": "system",
      "content": [
        {
          "type": "input_text",
          "text": "You are a helpful assistant."
        }
      ]
    },
    {
      "role": "user",
      "content": [
        {
          "type": "input_text",
          "text": "Find information about climate change."
        }
      ]
    }
  ],
  tools=[
    {
      "type": "web_search"
    }
  ]
)
```

### Key Differences

1. **Input Format**:
   - Chat Completions: Uses a simpler message format with roles and content.
   - Responses: Uses a more structured input format with specified content types.

2. **Tool Support**:
   - Chat Completions: Supports function calling but requires more implementation effort.
   - Responses: Has built-in tools (web search, file search, computer use) with more seamless integration.

3. **Multimodal Handling**:
   - Chat Completions: Supports basic multimodal but with simpler structure.
   - Responses: More structured approach to handling different content types.

4. **Token Consumption**:
   - For file processing, the APIs can have significant differences in token consumption. In some cases, Chat Completions may use fewer tokens than Responses for the same file inputs.

5. **State Management**:
   - Chat Completions: Stateless, requiring you to manage conversation history.
   - Responses: More built-in support for managing conversation state (similar to Assistants API).

6. **Future Direction**:
   - OpenAI is planning to gradually replace the Assistants API with the Responses API, making Responses the preferred path for complex applications.

### Migration Considerations

If you're currently using the Assistants API, note that OpenAI has announced plans to deprecate it in favor of the Responses API. The deprecation is planned for the first half of 2026, with 12 months of support from the deprecation date. A comprehensive migration guide will be provided when the deprecation is officially announced.

If you're starting a new project, the Responses API is likely the better choice for future-proofing your application, especially if you need the advanced features it provides.

## Responses API Syntax Reference

The Responses API has a specific syntax structure that differs from the Chat Completions API. This section provides a detailed reference for using the Responses API effectively.

### Basic Request Structure

```python
from openai import OpenAI
client = OpenAI()

response = client.responses.create(
  model="gpt-4o",
  input=[
    {
      "role": "system",
      "content": [
        {
          "type": "input_text",
          "text": "You are a helpful assistant."
        }
      ]
    },
    {
      "role": "user",
      "content": [
        {
          "type": "input_text",
          "text": "Your query here"
        }
      ]
    }
  ],
  # Optional parameters
  tools=[],
  reasoning={},
  text={},
  temperature=1.0,
  max_output_tokens=2048,
  top_p=1,
  store=True
)
```

### Input Parameter

The `input` parameter is a list of message objects, each having a `role` and `content`:

- **Roles**: `"system"`, `"user"`, or `"assistant"`
- **Content**: An array of content objects, each with a type field and corresponding data

#### Content Types

1. **Text Content**:
```python
{
  "type": "input_text",
  "text": "Your text here"
}
```

2. **File Content**:
```python
{
  "type": "input_file",
  "file_data": "data:application/pdf;base64,BASE64_ENCODED_DATA",
  "filename": "document.pdf"
}
```

3. **Image Content**:
```python
{
  "type": "input_image",
  "image_data": "data:image/jpeg;base64,BASE64_ENCODED_IMAGE",
}
```

### Tools Parameter

The `tools` parameter specifies what tools the model can use:

```python
tools=[
  {
    "type": "web_search"  # Built-in web search
  },
  {
    "type": "file_search",  # Built-in file search
    "settings": {
      "semantic_search": True,
      "keyword_search": True
    }
  },
  {
    "type": "computer"  # Computer use capability
  },
  {
    "type": "function",  # Custom function
    "function": {
      "name": "get_weather",
      "description": "Get current weather in a location",
      "parameters": {
        "type": "object",
        "properties": {
          "location": {
            "type": "string",
            "description": "The city and state, e.g. San Francisco, CA"
          }
        },
        "required": ["location"]
      }
    }
  }
]
```

### Reasoning Parameter

The `reasoning` parameter controls the model's reasoning process:

```python
reasoning={
  "enabled": True,  # Enable explicit reasoning
  "format": {
      "type": "markdown"  # Format of the reasoning output
  }
}
```

### Text Parameter

The `text` parameter configures the format of the text output:

```python
text={
  "format": {
    "type": "text"  # Plain text format
  }
}
```

Or for structured outputs:

```python
text={
  "format": {
    "type": "json_object",  # Important: Use json_object, not json_schema
    "schema": {
      "type": "object",
      "properties": {
        "title": {"type": "string"},
        "points": {"type": "array", "items": {"type": "string"}}
      },
      "required": ["title", "points"]
    }
  }
}
```

### Other Parameters

- `temperature` (float): Controls randomness (0.0 to 1.0)
- `max_output_tokens` (int): Maximum number of tokens in the output
- `top_p` (float): Controls diversity via nucleus sampling
- `store` (boolean): Whether to store the response in OpenAI's systems

### Response Structure

```python
{
  "id": "resp_abc123",
  "created": 1709047293,
  "model": "gpt-4o",
  "content": [
    {
      "type": "output_text",
      "text": "The generated response text"
    }
  ],
  "tool_calls": [
    {
      "type": "web_search",
      "web_search": {
        "search_query": "search query here",
        "search_results": [
          {
            "title": "Result title",
            "url": "https://example.com/result",
            "snippet": "Part of the search result"
          }
        ]
      }
    }
  ],
  "reasoning": "This is the model's reasoning process...",
  "usage": {
    "input_tokens": 123,
    "output_tokens": 456
  }
}
```

### Working with Files

Files in the Responses API are handled differently from the Chat Completions API:

```python
# Base64 encode the file first
import base64

with open("document.pdf", "rb") as file:
    base64_file = base64.b64encode(file.read()).decode("utf-8")

response = client.responses.create(
  model="gpt-4o",
  input=[
    {
      "role": "user",
      "content": [
        {
          "type": "input_text",
          "text": "Summarize this document"
        },
        {
          "type": "input_file",
          "file_data": f"data:application/pdf;base64,{base64_file}",
          "filename": "document.pdf"
        }
      ]
    }
  ],
  tools=[
    {
      "type": "file_search"
    }
  ]
)
```

### Streaming Responses

To stream responses:

```python
stream = client.responses.create(
  model="gpt-4o",
  input=[
    {"role": "user", "content": [{"type": "input_text", "text": "Tell me a story"}]}
  ],
  stream=True
)

for chunk in stream:
  if chunk.content:
    print(chunk.content[0].text, end="", flush=True)
```

## Examples

### Basic Agent

```python
from agents import Agent, Runner

agent = Agent(
    name="Assistant",
    instructions="You are a helpful assistant."
)

result = Runner.run_sync(agent, "Write a haiku about AI.")
print(result.final_output)
```

### Agent with Tools

```python
from agents import Agent, Runner, function_tool

def search_database(query: str) -> str:
    """Search a database for information."""
    # Implementation here
    return f"Results for '{query}': ..."

agent = Agent(
    name="Database Assistant",
    instructions="Help users find information in the database.",
    tools=[function_tool(search_database)]
)

result = Runner.run_sync(agent, "Find information about climate change.")
print(result.final_output)
```

## Best Practices

1. **Use Specific Instructions**: Provide clear, detailed instructions to guide agent behavior.

2. **Choose Appropriate Models**: Select models based on task complexity:
   - `o3-mini`: Faster, cheaper for simpler tasks
   - `gpt-4o-2024-05-13`: Higher quality for complex reasoning

3. **Tune ModelSettings**:
   - Lower temperature (0.0-0.3) for factual, precise tasks
   - Higher temperature (0.5-0.7) for creative tasks
   - Adjust presence_penalty to prevent repetition

4. **Implement Error Handling**: Use try/except blocks and provide graceful fallbacks.

5. **Use Tracing**: Implement trace handlers to monitor and debug agent execution.

6. **Cache Results**: Consider caching results for expensive or repeated operations.

7. **Use Named Parameters**: Always pass `context` as a named parameter to Runner.run().

8. **Handle SpanData Carefully**: Always check if attributes exist before accessing them.

## Common Issues

### ModelSettings Parameters

The ModelSettings class accepts these parameters:
- temperature
- top_p
- frequency_penalty
- presence_penalty
- tool_choice
- parallel_tool_calls
- truncation
- max_tokens

**Note**: Unlike the OpenAI API, it does not accept `response_format`. This must be handled separately.

### RunConfig Parameter Changes

Recent SDK versions have deprecated the following parameters:
- `trace_id_generator`: Use `trace_id` with a generated string instead

### Python Version Requirements

The OpenAI Agents SDK works best with Python 3.11+.

### Missing Dependencies

Ensure all dependencies are installed:
```bash
pip install openai-agents tiktoken PyPDF2 python-docx
```

### Tracing Issues

When working with traces, make sure to use the correct classes:
- Use `SpanData` from `agents.tracing` (not `TraceEvent`)
- Access span attributes carefully: `span.span_data.type` and `span.span_data.data`
- Always add trace processors before running agents

### SpanData Access

The structure for accessing data in spans has changed in newer versions:
- Old: `span.type`, `span.data.get('run_id')`
- New: `span.span_data.type`, `span.span_data.data.get('run_id')`

Always use defensive coding with `hasattr()` checks:
```python
if hasattr(span, 'span_data') and hasattr(span.span_data, 'type'):
    span_type = span.span_data.type
    # Then continue with your logic
```

## Compatibility Notes

### Model Version Compatibility

Different OpenAI models support different features:

- **gpt-4o-2024-05-13**:
  - Requires `json_object` format in the text parameter, not `json_schema`
  - Supports more advanced structured outputs

- **o3-mini**:
  - Faster and more cost-effective
  - May have lower quality for complex reasoning tasks
  - Ideal for simpler tasks like classification or data extraction

### Parameter Type Issues

When using the Responses API, ensure you use the correct parameter types:

1. **json_object vs json_schema**: Some models (like gpt-4o-2024-05-13) require `json_object` instead of `json_schema`.

2. **text.format fix**:
```python
# Correct format
text={
  "format": {
    "type": "json_object",  # Not json_schema
    "schema": {...}
  }
}
```

3. **Monkey Patching**: If the SDK uses incompatible formats, you may need to monkey patch the API:
```python
# Example patch for the Converter.get_response_format method
from agents.models.openai_responses import Converter
from agents.agent_output import AgentOutputSchema

# Store original
original_get_response_format = Converter.get_response_format

@classmethod
def patched_get_response_format(cls, output_schema):
    """Patch to use json_object instead of json_schema"""
    if output_schema is None or output_schema.is_plain_text():
        return NOT_GIVEN
    else:
        return {
            "format": {
                "type": "json_object",  # Changed from json_schema
                "name": "final_output",
                "schema": output_schema.json_schema(),
                "strict": output_schema.strict_json_schema,
            }
        }

# Apply patch
Converter.get_response_format = patched_get_response_format
```

### Port Conflicts

If you encounter port conflicts when starting your server:
```
ERROR:    [Errno 48] error while attempting to bind on address ('0.0.0.0', 8888): address already in use
```

Use one of these solutions:
1. Kill the existing process using the port: `kill <process_id>`
2. Configure a different port in your .env file or command line
3. Use the `lsof -i :<port>` command to identify processes using the port 
# Presentation Automator Project Structure

## Overview

This document outlines the complete file structure for the Presentation Automator project, organized by project plans. The system consists of a backend built with FastAPI and Python, and a frontend built with React and modern web technologies.

## Backend Structure

### Project Plan 1: Setup and Core Infrastructure

```
presentation-automator/
├── backend/
│   ├── .env                      # Environment variables (API keys, config)
│   ├── .env.example              # Example environment variables
│   ├── .gitignore                # Git ignore file
│   ├── pyproject.toml            # Python project configuration
│   ├── README.md                 # Project documentation
│   ├── run.sh                    # Script to run the server
│   ├── src/
│   │   ├── __init__.py           # Package initialization
│   │   ├── main.py               # Server entry point
│   │   ├── api/
│   │   │   ├── __init__.py
│   │   │   └── app.py            # FastAPI application setup
│   │   ├── config/
│   │   │   ├── __init__.py
│   │   │   └── settings.py       # Configuration settings
│   │   ├── models/
│   │   │   └── __init__.py
│   │   └── utils/
│   │       ├── __init__.py
│   │       └── logging.py        # Logging utilities
│   └── tests/
│       ├── __init__.py
│       └── test_health.py        # Health endpoint tests
```

- **src/main.py**: Entry point for the server application
- **src/api/app.py**: FastAPI app configuration with CORS setup and health check endpoints
- **src/config/settings.py**: Loads environment variables and provides settings
- **src/utils/logging.py**: Sets up logging configuration
- **tests/test_health.py**: Tests for health check endpoints

### Project Plan 2: Agent Framework Implementation

```
presentation-automator/
├── backend/
│   ├── src/
│   │   ├── agents/
│   │   │   ├── __init__.py       # Agent module exports
│   │   │   ├── base.py           # Base agent class
│   │   │   ├── planning_agent.py # Planning agent implementation
│   │   │   ├── content_agent.py  # Content agent implementation
│   │   │   ├── presentation_generator.py # Presentation generator orchestrator
│   │   │   └── tools.py          # Agent tools implementation
│   │   ├── api/
│   │   │   └── router.py         # API routes for presentation generation
│   │   └── models/
│   │       └── schemas.py        # Data models for presentations
│   └── tests/
│       ├── test_agents.py        # Tests for agents
│       └── test_api.py           # Tests for API endpoints
```

- **src/agents/base.py**: Generic base agent implementation using OpenAI Agents SDK
- **src/agents/planning_agent.py**: Agent for analyzing text and planning presentation structure
- **src/agents/content_agent.py**: Agent for generating detailed slide content
- **src/agents/presentation_generator.py**: Orchestrator for the generation process
- **src/agents/tools.py**: Utility tools for agents to use during processing
- **src/api/router.py**: API endpoints for presentation generation
- **src/models/schemas.py**: Pydantic models for data structures
- **tests/test_agents.py**: Unit tests for agent functionality
- **tests/test_api.py**: Tests for API endpoints

### Project Plan 3: Context-Based Integration

```
presentation-automator/
├── backend/
│   ├── src/
│   │   ├── services/
│   │   │   ├── __init__.py
│   │   │   ├── cache_service.py         # Caching service
│   │   │   ├── content_extraction.py    # Content extraction service
│   │   │   ├── document_processor.py    # Document processing service
│   │   │   ├── presentation_service.py  # Enhanced presentation service
│   │   │   └── task_manager.py          # Asynchronous task system
│   │   ├── api/
│   │   │   └── async_router.py          # Async presentation endpoints
│   │   └── utils/
│   │       └── context_manager.py       # Context management utilities
│   └── cache/                           # Cache directory for persistent caching
```

- **src/services/cache_service.py**: Caching service for improved performance
- **src/services/content_extraction.py**: Content extraction and analysis service
- **src/services/document_processor.py**: Service for processing different document formats
- **src/services/presentation_service.py**: Enhanced service with context sharing
- **src/services/task_manager.py**: Asynchronous task system for long-running operations
- **src/api/async_router.py**: API endpoints for async presentation generation
- **src/utils/context_manager.py**: Context management for agent communication

### Project Plan 4: API Integration and Endpoints

```
presentation-automator/
├── backend/
│   ├── src/
│   │   ├── api/
│   │   │   ├── presentation_router.py   # CRUD operations for presentations
│   │   │   ├── user_router.py           # User management endpoints
│   │   │   └── upload_router.py         # File upload endpoints
│   │   ├── models/
│   │   │   └── database.py              # Database models
│   │   ├── services/
│   │   │   └── storage_service.py       # Storage service for presentations
│   │   └── middleware/
│   │       ├── __init__.py
│   │       ├── auth.py                  # Authentication middleware
│   │       └── error_handler.py         # Error handling middleware
│   └── tests/
│       └── test_presentation_api.py     # Tests for presentation API
```

- **src/api/presentation_router.py**: CRUD operations for presentations
- **src/api/user_router.py**: User management endpoints
- **src/api/upload_router.py**: File upload handling endpoints
- **src/models/database.py**: Database models for data persistence
- **src/services/storage_service.py**: Service for storing and retrieving presentations
- **src/middleware/auth.py**: Authentication and authorization middleware
- **src/middleware/error_handler.py**: Global error handling middleware

## Frontend Structure

### Project Plan 5: Frontend Implementation

```
presentation-automator/
├── frontend/
│   ├── .env.development           # Development environment variables
│   ├── .env.production            # Production environment variables
│   ├── .gitignore                 # Git ignore file
│   ├── index.html                 # HTML entry point
│   ├── package.json               # NPM package configuration
│   ├── README.md                  # Frontend documentation
│   ├── vite.config.js             # Vite configuration
│   ├── tailwind.config.js         # Tailwind CSS configuration
│   ├── public/                    # Public assets
│   └── src/
│       ├── main.jsx               # React entry point
│       ├── App.jsx                # Main App component
│       ├── index.css              # Global CSS styles
│       ├── components/
│       │   ├── common/
│       │   │   ├── ErrorMessage.jsx     # Error display component
│       │   │   └── LoadingSpinner.jsx   # Loading indicator component
│       │   └── slides/
│       │       └── BasicSlide.jsx       # Slide component
│       ├── features/
│       │   ├── generator/
│       │   │   └── PresentationForm.jsx # Presentation generation form
│       │   └── viewer/
│       │       └── PresentationViewer.jsx # Presentation viewer component
│       ├── services/
│       │   └── api/
│       │       ├── config.js            # API configuration
│       │       └── presentationService.js # API service for presentations
│       └── utils/
│           └── test-utils.js            # Testing utilities
```

- **src/App.jsx**: Main application component
- **src/main.jsx**: Entry point for React application
- **src/index.css**: Global styles with Tailwind
- **src/components/common/**: Reusable UI components
- **src/components/slides/**: Slide-specific components
- **src/features/generator/**: Presentation generation components
- **src/features/viewer/**: Presentation viewing components
- **src/services/api/**: API client services

### Project Plan 6: State Management and Advanced Features

```
presentation-automator/
├── frontend/
│   └── src/
│       ├── store/
│       │   └── presentationStore.js     # Zustand state management
│       ├── features/
│       │   ├── generator/
│       │   │   ├── FileUploadForm.jsx   # File upload component
│       │   │   ├── GenerationOptions.jsx # Generation options component
│       │   │   ├── GenerationProgress.jsx # Progress tracking component
│       │   │   └── PresentationGenerator.jsx # Main generator container
│       │   └── viewer/
│       │       └── SlideThumbnails.jsx  # Slide thumbnails navigation
│       └── hooks/
│           └── useAsyncGeneration.js    # Hook for async generation
```

- **src/store/presentationStore.js**: Zustand store for global state
- **src/features/generator/FileUploadForm.jsx**: Component for file uploads
- **src/features/generator/GenerationOptions.jsx**: Component for configuring generation
- **src/features/generator/GenerationProgress.jsx**: Progress tracking component
- **src/features/generator/PresentationGenerator.jsx**: Container component
- **src/features/viewer/SlideThumbnails.jsx**: Thumbnails for navigation
- **src/hooks/useAsyncGeneration.js**: Hook for async generation management

### Project Plan 7: Presentation Editor Functionality

```
presentation-automator/
├── frontend/
│   └── src/
│       ├── features/
│       │   └── editor/
│       │       ├── EditorLayout.jsx     # Editor layout component
│       │       ├── EditorThumbnails.jsx # Thumbnails for editor navigation
│       │       ├── PresentationProperties.jsx # Presentation metadata editor
│       │       ├── SlideEditor.jsx      # Slide content editor component
│       │       ├── SlideManager.jsx     # Slide management component
│       │       └── SlidePreview.jsx     # Slide preview component
│       ├── components/
│       │   └── editor/
│       │       └── HtmlEditor.jsx       # HTML content editor component
│       └── hooks/
│           └── useAutosave.js           # Autosave functionality hook
```

- **src/features/editor/EditorLayout.jsx**: Main editor layout
- **src/features/editor/EditorThumbnails.jsx**: Thumbnail navigation in editor
- **src/features/editor/PresentationProperties.jsx**: Component for editing presentation properties
- **src/features/editor/SlideEditor.jsx**: Component for editing individual slides
- **src/features/editor/SlideManager.jsx**: Component for adding/removing slides
- **src/features/editor/SlidePreview.jsx**: Component for previewing edited slides
- **src/components/editor/HtmlEditor.jsx**: HTML editor component
- **src/hooks/useAutosave.js**: Hook for autosaving edits

### Project Plan 8: Export and Sharing Functionality

```
presentation-automator/
├── frontend/
│   └── src/
│       ├── features/
│       │   ├── export/
│       │   │   ├── ExportModal.jsx      # Export modal component
│       │   │   └── PrintView.css        # Print styles
│       │   ├── sharing/
│       │   │   └── ShareModal.jsx       # Sharing modal component
│       │   ├── templates/
│       │   │   └── TemplateSelector.jsx # Template selection component
│       │   ├── print/
│       │   │   └── PrintView.jsx        # Print view component
│       │   ├── preferences/
│       │   │   └── UserPreferences.jsx  # User preferences component
│       │   └── tools/
│       │       └── PresentationTools.jsx # Toolbar component
│       └── main.jsx                     # Updated with routing
```

- **src/features/export/ExportModal.jsx**: Modal for exporting presentations
- **src/features/export/PrintView.css**: CSS styles for printing
- **src/features/sharing/ShareModal.jsx**: Modal for sharing presentations
- **src/features/templates/TemplateSelector.jsx**: Component for selecting templates
- **src/features/print/PrintView.jsx**: View for printing presentations
- **src/features/preferences/UserPreferences.jsx**: Component for user preferences
- **src/features/tools/PresentationTools.jsx**: Toolbar with presentation tools

## Complete Project Structure

The complete project combines all the components from the individual project plans into a cohesive system:

```
presentation-automator/
├── backend/                     # Backend application
│   ├── .env                     # Environment variables
│   ├── .env.example             # Example environment configuration
│   ├── .gitignore               # Git ignore file
│   ├── pyproject.toml           # Python project configuration
│   ├── README.md                # Backend documentation
│   ├── run.sh                   # Script to run the server
│   ├── src/                     # Source code
│   │   ├── __init__.py
│   │   ├── main.py              # Server entry point
│   │   ├── agents/              # Agent implementations
│   │   ├── api/                 # API endpoints
│   │   ├── config/              # Configuration
│   │   ├── middleware/          # Middleware components
│   │   ├── models/              # Data models
│   │   ├── services/            # Service implementations
│   │   └── utils/               # Utility functions
│   ├── cache/                   # Cache directory
│   └── tests/                   # Test directory
├── frontend/                    # Frontend application
│   ├── .env.development         # Development environment variables
│   ├── .env.production          # Production environment variables
│   ├── .gitignore               # Git ignore file
│   ├── index.html               # HTML entry point
│   ├── package.json             # NPM package configuration
│   ├── README.md                # Frontend documentation
│   ├── vite.config.js           # Vite configuration
│   ├── tailwind.config.js       # Tailwind CSS configuration
│   ├── public/                  # Public assets
│   └── src/                     # Source code
│       ├── main.jsx             # React entry point
│       ├── App.jsx              # Main App component
│       ├── index.css            # Global CSS styles
│       ├── components/          # Reusable components
│       ├── features/            # Feature modules
│       ├── hooks/               # Custom React hooks
│       ├── services/            # Service implementations
│       ├── store/               # State management
│       └── utils/               # Utility functions
└── README.md                    # Project documentation
```

This structure represents the complete Presentation Automator system, with both the backend and frontend components organized according to the project plans. 
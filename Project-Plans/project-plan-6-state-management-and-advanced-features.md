# Project Plan 6: State Management and Advanced Features

## Overview

This project plan focuses on enhancing the Presentation Automator frontend with robust state management, file upload capabilities, and more sophisticated user interface components. Building upon the basic implementation from Project Plan 5, this plan introduces a global state management solution, adds file upload support, implements slide thumbnails, and creates a more dynamic user experience.

## Objectives

1. Implement global state management using Zustand
2. Add file upload capabilities for document processing
3. Create a slide thumbnails navigation component
4. Implement advanced generation options
5. Add generation progress tracking
6. Enhance error handling and feedback mechanisms

## Prerequisites

- Completion of Project Plan 5 (Frontend Implementation)
- Familiarity with state management concepts
- Understanding of file upload processes
- Backend support for file uploads and async generation

## Deliverables

1. Global state management implementation
2. File upload interface and functionality
3. Slide thumbnails navigation component
4. Generation options interface
5. Progress tracking component for async operations
6. Enhanced error handling and user feedback

## Time Estimate

Approximately 2-3 weeks for a junior engineer.

## Detailed Implementation Steps

### Step 1: Set Up Zustand for State Management

Install Zustand for lightweight yet powerful state management:

```bash
npm install zustand
```

Create the store for managing presentation state:

```javascript
// src/store/presentationStore.js
import { create } from 'zustand';
import { generatePresentation, fetchPresentation, generatePresentationFromFile } from '../services/api/presentationService';

export const usePresentationStore = create((set, get) => ({
  // Presentation state
  presentation: null,
  isLoading: false,
  error: null,
  currentSlideIndex: 0,
  
  // Generation state
  generationOptions: {
    slideCount: 'auto',
    includeNotes: true,
    theme: 'default',
  },
  
  // Actions
  setCurrentSlide: (index) => set({ currentSlideIndex: index }),
  
  setGenerationOptions: (options) => set({
    generationOptions: {
      ...get().generationOptions,
      ...options
    }
  }),
  
  generatePresentation: async (text) => {
    set({ isLoading: true, error: null });
    
    try {
      const presentation = await generatePresentation(text, get().generationOptions);
      set({ 
        presentation, 
        isLoading: false, 
        currentSlideIndex: 0 
      });
      return presentation;
    } catch (error) {
      set({ 
        error: 'Failed to generate presentation', 
        isLoading: false 
      });
      throw error;
    }
  },
  
  generatePresentationFromFile: async (file) => {
    set({ isLoading: true, error: null });
    
    try {
      const presentation = await generatePresentationFromFile(file, get().generationOptions);
      set({ 
        presentation, 
        isLoading: false, 
        currentSlideIndex: 0 
      });
      return presentation;
    } catch (error) {
      set({ 
        error: 'Failed to generate presentation from file', 
        isLoading: false 
      });
      throw error;
    }
  },
  
  fetchPresentation: async (id) => {
    set({ isLoading: true, error: null });
    
    try {
      const presentation = await fetchPresentation(id);
      set({ 
        presentation, 
        isLoading: false, 
        currentSlideIndex: 0 
      });
      return presentation;
    } catch (error) {
      set({ 
        error: 'Failed to fetch presentation', 
        isLoading: false 
      });
      throw error;
    }
  },
  
  clearPresentation: () => set({ 
    presentation: null, 
    currentSlideIndex: 0 
  }),
}));
```

### Step 2: Update API Service for File Uploads

Update the API service to handle file uploads:

```javascript
// src/services/api/presentationService.js
import axios from 'axios';
import { API_URL } from './config';

// Create axios instance with base URL
const apiClient = axios.create({
  baseURL: API_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Generate a presentation from text
export const generatePresentation = async (text, options = {}) => {
  try {
    const response = await apiClient.post('/generate', { 
      document_text: text,
      options
    });
    return response.data;
  } catch (error) {
    console.error('Error generating presentation:', error);
    throw error;
  }
};

// Generate a presentation from a file
export const generatePresentationFromFile = async (file, options = {}) => {
  try {
    const formData = new FormData();
    formData.append('file', file);
    
    // Add options as JSON string
    formData.append('options', JSON.stringify(options));
    
    const response = await axios.post(`${API_URL}/generate-from-file`, formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    });
    
    return response.data;
  } catch (error) {
    console.error('Error generating presentation from file:', error);
    throw error;
  }
};

// Start asynchronous generation
export const startAsyncGeneration = async (text, options = {}) => {
  try {
    const response = await apiClient.post('/generate-async', { 
      document_text: text,
      options
    });
    return response.data;
  } catch (error) {
    console.error('Error starting async generation:', error);
    throw error;
  }
};

// Start asynchronous generation from file
export const startAsyncGenerationFromFile = async (file, options = {}) => {
  try {
    const formData = new FormData();
    formData.append('file', file);
    formData.append('options', JSON.stringify(options));
    
    const response = await axios.post(`${API_URL}/generate-from-file-async`, formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    });
    
    return response.data;
  } catch (error) {
    console.error('Error starting async generation from file:', error);
    throw error;
  }
};

// Get generation task status
export const getGenerationStatus = async (taskId) => {
  try {
    const response = await apiClient.get(`/generation/${taskId}/status`);
    return response.data;
  } catch (error) {
    console.error('Error fetching generation status:', error);
    throw error;
  }
};

// Get generation task result
export const getGenerationResult = async (taskId) => {
  try {
    const response = await apiClient.get(`/generation/${taskId}/result`);
    return response.data;
  } catch (error) {
    console.error('Error fetching generation result:', error);
    throw error;
  }
};

// Fetch an existing presentation by ID
export const fetchPresentation = async (id) => {
  try {
    const response = await apiClient.get(`/presentations/${id}`);
    return response.data;
  } catch (error) {
    console.error('Error fetching presentation:', error);
    throw error;
  }
};
```

### Step 3: Create FileUploadForm Component

Create a component for uploading documents:

```jsx
// src/features/generator/FileUploadForm.jsx
import React, { useState } from 'react';
import { usePresentationStore } from '../../store/presentationStore';
import ErrorMessage from '../../components/common/ErrorMessage';
import LoadingSpinner from '../../components/common/LoadingSpinner';

const FileUploadForm = () => {
  const [file, setFile] = useState(null);
  const { generatePresentationFromFile, isLoading, error } = usePresentationStore();
  
  const handleFileChange = (e) => {
    if (e.target.files.length > 0) {
      setFile(e.target.files[0]);
    }
  };
  
  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!file) return;
    
    try {
      await generatePresentationFromFile(file);
    } catch (err) {
      console.error(err);
    }
  };
  
  const handleRetry = () => {
    // This will reset error state in the store
    setFile(null);
  };
  
  return (
    <div className="p-4 border rounded-lg">
      <h2 className="text-xl font-bold mb-4">Upload Document</h2>
      
      {error && (
        <div className="mb-4">
          <ErrorMessage message={error} onRetry={handleRetry} />
        </div>
      )}
      
      <form onSubmit={handleSubmit}>
        <div className="mb-4">
          <label className="block text-sm font-medium mb-1">
            Choose a document file:
          </label>
          <input
            type="file"
            onChange={handleFileChange}
            accept=".txt,.md,.docx,.pdf"
            className="w-full p-2 border rounded"
            disabled={isLoading}
          />
          <p className="text-xs text-gray-500 mt-1">
            Supported formats: .txt, .md, .docx, .pdf
          </p>
        </div>
        
        <button
          type="submit"
          disabled={isLoading || !file}
          className="w-full py-2 px-4 bg-green-600 text-white rounded hover:bg-green-700 disabled:opacity-50"
        >
          {isLoading ? (
            <div className="flex items-center justify-center">
              <LoadingSpinner size="small" message={null} />
              <span className="ml-2">Uploading & Generating...</span>
            </div>
          ) : (
            "Generate from File"
          )}
        </button>
      </form>
    </div>
  );
};

export default FileUploadForm;
```

### Step 4: Implement GenerationOptions Component

Create a component for customizing generation options:

```jsx
// src/features/generator/GenerationOptions.jsx
import React, { useState, useEffect } from 'react';
import { usePresentationStore } from '../../store/presentationStore';

const GenerationOptions = () => {
  const { generationOptions, setGenerationOptions } = usePresentationStore();
  const [localOptions, setLocalOptions] = useState(generationOptions);
  
  // Update local state when store options change
  useEffect(() => {
    setLocalOptions(generationOptions);
  }, [generationOptions]);
  
  const handleChange = (e) => {
    const { name, value, type, checked } = e.target;
    setLocalOptions(prev => ({
      ...prev,
      [name]: type === 'checkbox' ? checked : value
    }));
  };
  
  const handleSubmit = (e) => {
    e.preventDefault();
    setGenerationOptions(localOptions);
  };
  
  return (
    <div className="mt-4 p-4 border-t">
      <h3 className="font-medium mb-2">Advanced Options</h3>
      <form onSubmit={handleSubmit}>
        <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
          <div>
            <label className="block text-sm font-medium mb-1">
              Slide Count
            </label>
            <select
              name="slideCount"
              value={localOptions.slideCount}
              onChange={handleChange}
              className="w-full p-2 border rounded"
            >
              <option value="auto">Auto-detect (Recommended)</option>
              <option value="5">~5 slides</option>
              <option value="10">~10 slides</option>
              <option value="15">~15 slides</option>
            </select>
          </div>
          
          <div>
            <label className="block text-sm font-medium mb-1">
              Theme
            </label>
            <select
              name="theme"
              value={localOptions.theme}
              onChange={handleChange}
              className="w-full p-2 border rounded"
            >
              <option value="default">Default</option>
              <option value="dark">Dark</option>
              <option value="light">Light</option>
              <option value="corporate">Corporate</option>
            </select>
          </div>
          
          <div className="col-span-2">
            <label className="flex items-center space-x-2">
              <input
                type="checkbox"
                name="includeNotes"
                checked={localOptions.includeNotes}
                onChange={handleChange}
                className="h-4 w-4"
              />
              <span className="text-sm">Generate speaker notes</span>
            </label>
          </div>
        </div>
        
        <button
          type="submit"
          className="mt-4 px-3 py-1 bg-gray-200 text-gray-800 rounded"
        >
          Apply Options
        </button>
      </form>
    </div>
  );
};

export default GenerationOptions;
```

### Step 5: Create Generation Progress Tracker

Implement a component to track asynchronous generation progress:

```jsx
// src/features/generator/GenerationProgress.jsx
import React, { useEffect, useState } from 'react';
import PropTypes from 'prop-types';
import { getGenerationResult } from '../../services/api/presentationService';
import { usePresentationStore } from '../../store/presentationStore';
import LoadingSpinner from '../../components/common/LoadingSpinner';
import ErrorMessage from '../../components/common/ErrorMessage';

const GenerationProgress = ({ taskId }) => {
  const [progress, setProgress] = useState(0);
  const [status, setStatus] = useState('Starting generation...');
  const [error, setError] = useState(null);
  const { presentation, isLoading } = usePresentationStore();
  
  // Set up presentation store access
  const setPresentation = usePresentationStore(state => state.setPresentation);
  
  useEffect(() => {
    if (!taskId) return;
    
    // Create an EventSource for server-sent events
    const eventSource = new EventSource(`${process.env.VITE_API_URL}/generation/${taskId}/progress`);
    
    eventSource.onmessage = async (event) => {
      const data = JSON.parse(event.data);
      setProgress(data.progress * 100);
      setStatus(data.status);
      
      if (data.status === 'completed') {
        eventSource.close();
        
        try {
          // Fetch the presentation result
          const result = await getGenerationResult(taskId);
          if (result && result.presentation) {
            setPresentation(result.presentation);
          }
        } catch (err) {
          setError('Error fetching the generated presentation.');
          console.error(err);
        }
      }
    };
    
    eventSource.onerror = (error) => {
      console.error('SSE Error:', error);
      setError('Connection to server lost. Generation may still be in progress.');
      eventSource.close();
    };
    
    return () => {
      eventSource.close();
    };
  }, [taskId, setPresentation]);
  
  if (presentation) return null; // Don't show if presentation is already loaded
  
  return (
    <div className="p-4 border rounded-lg">
      <h2 className="text-xl font-bold mb-4">Generating Presentation</h2>
      
      {error && (
        <div className="mb-4">
          <ErrorMessage message={error} />
        </div>
      )}
      
      <div className="mb-2">{status}</div>
      
      <div className="w-full bg-gray-200 rounded-full h-2.5 mb-4">
        <div 
          className="bg-blue-600 h-2.5 rounded-full" 
          style={{ width: `${Math.max(5, progress)}%` }}
        ></div>
      </div>
      
      <p className="text-sm text-gray-500">
        This may take a few minutes depending on document length.
      </p>
      
      {isLoading && <LoadingSpinner size="small" message={null} />}
    </div>
  );
};

GenerationProgress.propTypes = {
  taskId: PropTypes.string.isRequired
};

export default GenerationProgress;
```

### Step 6: Create Slide Thumbnails Component

Create a component for navigating between slides via thumbnails:

```jsx
// src/features/viewer/SlideThumbnails.jsx
import React from 'react';
import { usePresentationStore } from '../../store/presentationStore';

const SlideThumbnails = () => {
  const { presentation, currentSlideIndex, setCurrentSlide } = usePresentationStore();
  
  if (!presentation?.slides) return null;
  
  return (
    <div className="bg-gray-900 p-2 overflow-x-auto">
      <div className="flex space-x-2">
        {presentation.slides.map((slide, index) => (
          <button
            key={index}
            className={`p-1 min-w-[100px] h-16 flex items-center justify-center border ${
              index === currentSlideIndex 
                ? 'border-blue-500 bg-blue-900' 
                : 'border-gray-700 hover:bg-gray-800'
            }`}
            onClick={() => setCurrentSlide(index)}
          >
            <span className="text-xs text-white truncate">
              Slide {index + 1}
            </span>
          </button>
        ))}
      </div>
    </div>
  );
};

export default SlideThumbnails;
```

### Step 7: Create PresentationGenerator Container Component

Create a container component that combines the form and options:

```jsx
// src/features/generator/PresentationGenerator.jsx
import React, { useState } from 'react';
import PresentationForm from './PresentationForm';
import FileUploadForm from './FileUploadForm';
import GenerationOptions from './GenerationOptions';
import GenerationProgress from './GenerationProgress';
import { usePresentationStore } from '../../store/presentationStore';

const PresentationGenerator = () => {
  const [activeTab, setActiveTab] = useState('text');
  const [taskId, setTaskId] = useState(null);
  const { isLoading } = usePresentationStore();
  
  // Handler for async generation start
  const handleAsyncGenerationStarted = (newTaskId) => {
    setTaskId(newTaskId);
  };
  
  return (
    <div className="max-w-3xl mx-auto p-4">
      {taskId ? (
        <GenerationProgress taskId={taskId} />
      ) : (
        <>
          <div className="flex border-b mb-4">
            <button
              className={`py-2 px-4 ${activeTab === 'text' ? 'border-b-2 border-blue-500 font-medium' : 'text-gray-500'}`}
              onClick={() => setActiveTab('text')}
              disabled={isLoading}
            >
              Text Input
            </button>
            <button
              className={`py-2 px-4 ${activeTab === 'file' ? 'border-b-2 border-blue-500 font-medium' : 'text-gray-500'}`}
              onClick={() => setActiveTab('file')}
              disabled={isLoading}
            >
              File Upload
            </button>
          </div>
          
          <div className="mt-4">
            {activeTab === 'text' ? (
              <PresentationForm onAsyncStarted={handleAsyncGenerationStarted} />
            ) : (
              <FileUploadForm onAsyncStarted={handleAsyncGenerationStarted} />
            )}
            
            <GenerationOptions />
          </div>
        </>
      )}
    </div>
  );
};

export default PresentationGenerator;
```

### Step 8: Update PresentationForm to Support Async Generation

Modify the PresentationForm to support asynchronous generation:

```jsx
// src/features/generator/PresentationForm.jsx
import React, { useState } from 'react';
import PropTypes from 'prop-types';
import { startAsyncGeneration } from '../../services/api/presentationService';
import { usePresentationStore } from '../../store/presentationStore';
import ErrorMessage from '../../components/common/ErrorMessage';
import LoadingSpinner from '../../components/common/LoadingSpinner';

const PresentationForm = ({ onAsyncStarted }) => {
  const [text, setText] = useState('');
  const { generatePresentation, isLoading, error, generationOptions } = usePresentationStore();
  
  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!text.trim()) return;
    
    try {
      // Regular synchronous generation
      await generatePresentation(text);
    } catch (err) {
      console.error(err);
    }
  };
  
  const handleAsyncSubmit = async (e) => {
    e.preventDefault();
    if (!text.trim()) return;
    
    try {
      // Start async generation
      const response = await startAsyncGeneration(text, generationOptions);
      
      if (response && response.task_id) {
        onAsyncStarted(response.task_id);
      }
    } catch (err) {
      console.error(err);
    }
  };
  
  const handleRetry = () => {
    // The store's error will be reset when a new request is made
  };
  
  return (
    <div className="max-w-2xl mx-auto p-4 card">
      <h2 className="text-xl font-bold mb-4">Generate Presentation</h2>
      
      {error && (
        <div className="mb-4">
          <ErrorMessage message={error} onRetry={handleRetry} />
        </div>
      )}
      
      <form onSubmit={handleSubmit}>
        <div className="mb-4">
          <label className="block text-sm font-medium mb-1" htmlFor="document-text">
            Enter your document text:
          </label>
          <textarea
            id="document-text"
            className="w-full h-40 p-2 border rounded focus:ring-primary-500 focus:border-primary-500"
            value={text}
            onChange={(e) => setText(e.target.value)}
            placeholder="Paste your document text here..."
            disabled={isLoading}
          />
        </div>
        
        <div className="flex space-x-2">
          <button
            type="submit"
            disabled={isLoading || !text.trim()}
            className="flex-1 btn btn-primary"
          >
            {isLoading ? (
              <div className="flex items-center justify-center">
                <LoadingSpinner size="small" message={null} />
                <span className="ml-2">Generating...</span>
              </div>
            ) : (
              "Generate Now"
            )}
          </button>
          
          <button
            type="button"
            onClick={handleAsyncSubmit}
            disabled={isLoading || !text.trim()}
            className="flex-1 btn btn-secondary"
          >
            Generate in Background
          </button>
        </div>
      </form>
    </div>
  );
};

PresentationForm.propTypes = {
  onAsyncStarted: PropTypes.func.isRequired
};

export default PresentationForm;
```

### Step 9: Update Main App Component with Zustand and New Components

Update the App component to use the store and new components:

```jsx
// src/App.jsx
import React, { useState } from 'react';
import PresentationGenerator from './features/generator/PresentationGenerator';
import PresentationViewer from './features/viewer/PresentationViewer';
import SlideThumbnails from './features/viewer/SlideThumbnails';
import { usePresentationStore } from './store/presentationStore';

function App() {
  const { presentation, clearPresentation } = usePresentationStore();
  
  return (
    <div className="min-h-screen flex flex-col">
      <header className="bg-gray-800 text-white p-4">
        <div className="container mx-auto flex justify-between items-center">
          <h1 className="text-2xl font-bold">Presentation Automator</h1>
          
          {presentation && (
            <button 
              className="px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700"
              onClick={clearPresentation}
            >
              New Presentation
            </button>
          )}
        </div>
      </header>
      
      <main className="flex-grow flex flex-col container mx-auto py-6">
        {!presentation ? (
          <PresentationGenerator />
        ) : (
          <div className="flex-grow flex flex-col">
            <div className="flex-grow">
              <PresentationViewer />
            </div>
            <SlideThumbnails />
          </div>
        )}
      </main>
      
      <footer className="bg-gray-100 py-4 border-t">
        <div className="container mx-auto text-center text-sm text-gray-600">
          &copy; {new Date().getFullYear()} Presentation Automator. All rights reserved.
        </div>
      </footer>
    </div>
  );
}

export default App;
```

### Step 10: Update PresentationViewer to Use Zustand Store

Update the PresentationViewer to use the Zustand store:

```jsx
// src/features/viewer/PresentationViewer.jsx
import React, { useEffect, useRef } from 'react';
import Reveal from 'reveal.js';
import 'reveal.js/dist/reveal.css';
import 'reveal.js/dist/theme/black.css';
import BasicSlide from '../../components/slides/BasicSlide';
import { usePresentationStore } from '../../store/presentationStore';

const PresentationViewer = () => {
  const revealRef = useRef(null);
  const revealInstance = useRef(null);
  const { presentation, currentSlideIndex, setCurrentSlide } = usePresentationStore();
  
  useEffect(() => {
    // Initialize Reveal.js after React has rendered slides
    if (revealRef.current && presentation?.slides?.length > 0) {
      revealInstance.current = new Reveal(revealRef.current, {
        embedded: false,
        hash: false,
        controls: true,
        progress: true,
        center: true,
        transition: 'slide',
      });
      
      // Add event listener for slide changes
      const handleSlideChange = (event) => {
        const horizontalIndex = event.indexh;
        setCurrentSlide(horizontalIndex);
      };
      
      revealInstance.current.initialize().then(() => {
        revealInstance.current.addEventListener('slidechanged', handleSlideChange);
      });
      
      // Cleanup
      return () => {
        if (revealInstance.current) {
          revealInstance.current.removeEventListener('slidechanged', handleSlideChange);
          revealInstance.current.destroy();
          revealInstance.current = null;
        }
      };
    }
  }, [presentation?.slides?.length, setCurrentSlide]);
  
  // Sync to current slide when currentSlideIndex changes externally
  useEffect(() => {
    if (revealInstance.current && revealInstance.current.isReady()) {
      revealInstance.current.slide(currentSlideIndex);
    }
  }, [currentSlideIndex]);
  
  if (!presentation || !presentation.slides || presentation.slides.length === 0) {
    return <div className="text-center py-10">No slides to display</div>;
  }
  
  return (
    <div className="reveal" ref={revealRef}>
      <div className="slides">
        {presentation.slides.map((slide, index) => (
          <BasicSlide 
            key={index} 
            content={slide.content} 
            notes={slide.notes} 
          />
        ))}
      </div>
    </div>
  );
};

export default PresentationViewer;
```

### Step 11: Update Testing Configuration for Zustand

Update the testing setup to work with Zustand:

```javascript
// src/utils/test-utils.js
import React from 'react';
import { render } from '@testing-library/react';
import { createStore } from 'zustand';
import { usePresentationStore } from '../store/presentationStore';

// Create a wrapper with a mock store for tests
export function renderWithStore(
  ui,
  {
    initialState = {},
    store = createStore((...args) => ({
      ...usePresentationStore(...args),
      ...initialState,
    })),
    ...renderOptions
  } = {}
) {
  function Wrapper({ children }) {
    // Replace the real store with the test store
    const StoreProvider = ({ children }) => {
      return children;
    };
    
    return <StoreProvider>{children}</StoreProvider>;
  }
  
  return render(ui, { wrapper: Wrapper, ...renderOptions });
}
```

### Step 12: Add Basic Component Tests

Create tests for key components:

```jsx
// src/features/generator/GenerationOptions.test.jsx
import { describe, it, expect, vi } from 'vitest';
import { render, screen, fireEvent } from '@testing-library/react';
import GenerationOptions from './GenerationOptions';
import { usePresentationStore } from '../../store/presentationStore';

// Mock the Zustand store
vi.mock('../../store/presentationStore', () => ({
  usePresentationStore: vi.fn()
}));

describe('GenerationOptions', () => {
  it('renders options correctly', () => {
    // Setup mock store
    const mockSetGenerationOptions = vi.fn();
    
    usePresentationStore.mockImplementation(() => ({
      generationOptions: {
        slideCount: 'auto',
        includeNotes: true,
        theme: 'default'
      },
      setGenerationOptions: mockSetGenerationOptions
    }));
    
    render(<GenerationOptions />);
    
    // Check if options are rendered
    expect(screen.getByLabelText(/slide count/i)).toBeInTheDocument();
    expect(screen.getByLabelText(/theme/i)).toBeInTheDocument();
    expect(screen.getByLabelText(/generate speaker notes/i)).toBeChecked();
    
    // Change an option
    fireEvent.change(screen.getByLabelText(/theme/i), { target: { value: 'dark' } });
    
    // Submit form
    fireEvent.click(screen.getByText(/apply options/i));
    
    // Check if the store function was called
    expect(mockSetGenerationOptions).toHaveBeenCalled();
  });
});
```

### Step 13: Update FileUploadForm to Support Async Generation

Similar to the PresentationForm update, modify FileUploadForm for async support:

```jsx
// src/features/generator/FileUploadForm.jsx (updated)
import React, { useState } from 'react';
import PropTypes from 'prop-types';
import { startAsyncGenerationFromFile } from '../../services/api/presentationService';
import { usePresentationStore } from '../../store/presentationStore';
import ErrorMessage from '../../components/common/ErrorMessage';
import LoadingSpinner from '../../components/common/LoadingSpinner';

const FileUploadForm = ({ onAsyncStarted }) => {
  const [file, setFile] = useState(null);
  const { generatePresentationFromFile, isLoading, error, generationOptions } = usePresentationStore();
  
  const handleFileChange = (e) => {
    if (e.target.files.length > 0) {
      setFile(e.target.files[0]);
    }
  };
  
  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!file) return;
    
    try {
      // Regular synchronous generation
      await generatePresentationFromFile(file);
    } catch (err) {
      console.error(err);
    }
  };
  
  const handleAsyncSubmit = async (e) => {
    e.preventDefault();
    if (!file) return;
    
    try {
      // Start async generation from file
      const response = await startAsyncGenerationFromFile(file, generationOptions);
      
      if (response && response.task_id) {
        onAsyncStarted(response.task_id);
      }
    } catch (err) {
      console.error(err);
    }
  };
  
  const handleRetry = () => {
    setFile(null);
  };
  
  return (
    <div className="p-4 border rounded-lg">
      <h2 className="text-xl font-bold mb-4">Upload Document</h2>
      
      {error && (
        <div className="mb-4">
          <ErrorMessage message={error} onRetry={handleRetry} />
        </div>
      )}
      
      <form onSubmit={handleSubmit}>
        <div className="mb-4">
          <label className="block text-sm font-medium mb-1">
            Choose a document file:
          </label>
          <input
            type="file"
            onChange={handleFileChange}
            accept=".txt,.md,.docx,.pdf"
            className="w-full p-2 border rounded"
            disabled={isLoading}
          />
          <p className="text-xs text-gray-500 mt-1">
            Supported formats: .txt, .md, .docx, .pdf
          </p>
        </div>
        
        <div className="flex space-x-2">
          <button
            type="submit"
            disabled={isLoading || !file}
            className="flex-1 btn btn-primary"
          >
            {isLoading ? (
              <div className="flex items-center justify-center">
                <LoadingSpinner size="small" message={null} />
                <span className="ml-2">Processing...</span>
              </div>
            ) : (
              "Generate Now"
            )}
          </button>
          
          <button
            type="button"
            onClick={handleAsyncSubmit}
            disabled={isLoading || !file}
            className="flex-1 btn btn-secondary"
          >
            Generate in Background
          </button>
        </div>
      </form>
    </div>
  );
};

FileUploadForm.propTypes = {
  onAsyncStarted: PropTypes.func.isRequired
};

export default FileUploadForm;
```

## Testing Instructions

To verify that the state management and advanced features are functioning correctly:

1. Start by ensuring the backend API with file upload and async generation support is running
2. Start the frontend development server
3. Test the primary generation flow:
   - Enter text or upload a file
   - Configure generation options
   - Generate a presentation synchronously
   - Verify that slides are displayed and navigable
4. Test the slide thumbnails:
   - Generate a presentation with multiple slides
   - Click on different thumbnails to navigate between slides
   - Verify that the current slide is highlighted
5. Test async generation flow:
   - Start an async generation (via "Generate in Background" button)
   - Observe the progress tracking
   - Verify that the presentation loads automatically when complete
6. Test file upload functionality:
   - Upload different types of files (.txt, .docx, etc.)
   - Verify that the presentation is generated correctly from each file type
7. Test error handling:
   - Submit invalid data or disconnect from the backend
   - Verify that appropriate error messages are displayed
   - Test the retry functionality

## Troubleshooting

If you encounter issues:

1. Check the browser console for JavaScript errors
2. Verify that the API endpoints are correctly configured in the environment variables
3. For file upload issues, check that the correct Content-Type headers are being sent
4. If SSE for progress tracking isn't working, verify that the backend is properly configured to send SSE events
5. If store updates aren't reflected in the UI, check that components are properly subscribed to the store state

## Next Steps

After completing this project plan, you will have a more robust frontend application with:
- Global state management with Zustand
- File upload capabilities
- Slide thumbnail navigation
- Generation options for customization
- Progress tracking for async tasks
- Improved error handling and user feedback

You're now ready to proceed to Project Plan 7, which will focus on implementing the presentation editor functionality that allows users to modify generated presentations. 
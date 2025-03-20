# Project Plan 5: Frontend Implementation

## Overview

This project plan covers the implementation of the frontend for the Presentation Automator. It focuses on building a modern, responsive user interface that connects to the backend services established in previous project plans. This plan will detail the setup, core viewing functionality, and the basic generation workflow.

## Objectives

1. Set up the frontend project structure and tooling
2. Implement a basic presentation viewer using Reveal.js
3. Create a presentation generation form interface
4. Establish API service connections to the backend
5. Build the core navigation components
6. Implement basic error handling and loading states

## Prerequisites

- Node.js 18 or higher
- npm or yarn package manager
- Basic knowledge of React, Tailwind CSS, and Reveal.js
- Operational backend API (from Project Plans 1-4)

## Deliverables

1. Configured React project with necessary dependencies
2. Working presentation viewer component
3. Presentation generation form with text input
4. API service layer for backend communication
5. Core navigation and layout components
6. Comprehensive README documentation

## Time Estimate

Approximately 2-3 weeks for a junior engineer.

## Detailed Implementation Steps

### Step 1: Project Setup

Set up a new React application using Vite for a fast, modern development experience:

```bash
# Create a new React project with Vite
npm create vite@latest presentation-frontend -- --template react

# Navigate to the project directory
cd presentation-frontend

# Install core dependencies
npm install react-router-dom axios reveal.js tailwindcss

# Install UI utilities
npm install classnames

# Initialize Tailwind CSS
npx tailwindcss init -p

# Install development dependencies
npm install -D vitest @testing-library/react @testing-library/jest-dom
```

### Step 2: Configure Project Structure

Create a clean, scalable folder structure:

```bash
mkdir -p src/{components,features,hooks,services,utils}
mkdir -p src/components/{common,slides}
mkdir -p src/features/{viewer,generator}
mkdir -p src/services/api
```

Update the Tailwind configuration in `tailwind.config.js`:

```javascript
/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        primary: {
          50: '#eef2ff',
          100: '#e0e7ff',
          200: '#c7d2fe',
          300: '#a5b4fc',
          400: '#818cf8',
          500: '#6366f1',
          600: '#4f46e5',
          700: '#4338ca',
          800: '#3730a3',
          900: '#312e81',
          950: '#1e1b4b',
        },
      },
    },
  },
  plugins: [],
}
```

Create a basic CSS file for global styles in `src/index.css`:

```css
@tailwind base;
@tailwind components;
@tailwind utilities;

body {
  @apply bg-gray-50 text-gray-900;
}

.btn {
  @apply px-4 py-2 rounded font-medium focus:outline-none focus:ring-2 focus:ring-offset-2;
}

.btn-primary {
  @apply bg-primary-600 text-white hover:bg-primary-700 focus:ring-primary-500;
}

.btn-secondary {
  @apply bg-gray-200 text-gray-800 hover:bg-gray-300 focus:ring-gray-500;
}

.card {
  @apply bg-white rounded-lg shadow p-6;
}
```

### Step 3: Create API Service

Set up the API service to connect to the backend:

```javascript
// src/services/api/config.js
export const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000/api';
```

Create the main presentation service:

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
export const generatePresentation = async (text) => {
  try {
    const response = await apiClient.post('/generate', { 
      document_text: text 
    });
    return response.data;
  } catch (error) {
    console.error('Error generating presentation:', error);
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

### Step 4: Create Basic Slide Component

Create a component to render individual slides:

```jsx
// src/components/slides/BasicSlide.jsx
import React from 'react';
import PropTypes from 'prop-types';

const BasicSlide = ({ content, notes = '' }) => {
  return (
    <section>
      <div dangerouslySetInnerHTML={{ __html: content }} />
      {notes && <aside className="notes">{notes}</aside>}
    </section>
  );
};

BasicSlide.propTypes = {
  content: PropTypes.string.isRequired,
  notes: PropTypes.string
};

export default BasicSlide;
```

### Step 5: Implement Presentation Viewer with Reveal.js

Create a viewer component to render presentations using Reveal.js:

```jsx
// src/features/viewer/PresentationViewer.jsx
import React, { useEffect, useRef } from 'react';
import PropTypes from 'prop-types';
import Reveal from 'reveal.js';
import 'reveal.js/dist/reveal.css';
import 'reveal.js/dist/theme/black.css';
import BasicSlide from '../../components/slides/BasicSlide';

const PresentationViewer = ({ slides = [] }) => {
  const revealRef = useRef(null);
  
  useEffect(() => {
    // Initialize Reveal.js after React has rendered slides
    if (revealRef.current && slides.length > 0) {
      const deck = new Reveal(revealRef.current, {
        embedded: false,
        hash: false,
        controls: true,
        progress: true,
        center: true,
        transition: 'slide',
      });
      
      deck.initialize();
      
      // Cleanup
      return () => {
        deck.destroy();
      };
    }
  }, [slides.length]);
  
  if (!slides || slides.length === 0) {
    return <div className="text-center py-10">No slides to display</div>;
  }
  
  return (
    <div className="reveal" ref={revealRef}>
      <div className="slides">
        {slides.map((slide, index) => (
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

PresentationViewer.propTypes = {
  slides: PropTypes.arrayOf(
    PropTypes.shape({
      content: PropTypes.string.isRequired,
      notes: PropTypes.string
    })
  )
};

export default PresentationViewer;
```

### Step 6: Create Loading and Error Components

Create reusable components for loading and error states:

```jsx
// src/components/common/LoadingSpinner.jsx
import React from 'react';

const LoadingSpinner = ({ size = 'medium', message = 'Loading...' }) => {
  const sizeClasses = {
    small: 'w-4 h-4',
    medium: 'w-8 h-8',
    large: 'w-12 h-12',
  };
  
  return (
    <div className="flex flex-col items-center justify-center p-4">
      <div className={`animate-spin rounded-full border-t-2 border-primary-500 ${sizeClasses[size]}`}></div>
      {message && <p className="mt-2 text-gray-600">{message}</p>}
    </div>
  );
};

export default LoadingSpinner;

// src/components/common/ErrorMessage.jsx
import React from 'react';
import PropTypes from 'prop-types';

const ErrorMessage = ({ message, onRetry }) => {
  return (
    <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded relative" role="alert">
      <strong className="font-bold">Error: </strong>
      <span className="block sm:inline">{message}</span>
      {onRetry && (
        <div className="mt-2">
          <button 
            onClick={onRetry}
            className="text-sm bg-red-100 px-3 py-1 rounded hover:bg-red-200"
          >
            Try Again
          </button>
        </div>
      )}
    </div>
  );
};

ErrorMessage.propTypes = {
  message: PropTypes.string.isRequired,
  onRetry: PropTypes.func
};

export default ErrorMessage;
```

### Step 7: Create Presentation Generation Form

Create a form for generating presentations from text:

```jsx
// src/features/generator/PresentationForm.jsx
import React, { useState } from 'react';
import PropTypes from 'prop-types';
import { generatePresentation } from '../../services/api/presentationService';
import ErrorMessage from '../../components/common/ErrorMessage';
import LoadingSpinner from '../../components/common/LoadingSpinner';

const PresentationForm = ({ onPresentationGenerated }) => {
  const [text, setText] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState(null);
  
  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!text.trim()) return;
    
    setIsLoading(true);
    setError(null);
    
    try {
      const presentation = await generatePresentation(text);
      onPresentationGenerated(presentation);
    } catch (err) {
      setError('Failed to generate presentation. Please try again.');
      console.error(err);
    } finally {
      setIsLoading(false);
    }
  };
  
  const handleRetry = () => {
    setError(null);
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
        
        <button
          type="submit"
          disabled={isLoading || !text.trim()}
          className="btn btn-primary w-full"
        >
          {isLoading ? (
            <div className="flex items-center justify-center">
              <LoadingSpinner size="small" message={null} />
              <span className="ml-2">Generating...</span>
            </div>
          ) : (
            "Generate Presentation"
          )}
        </button>
      </form>
    </div>
  );
};

PresentationForm.propTypes = {
  onPresentationGenerated: PropTypes.func.isRequired
};

export default PresentationForm;
```

### Step 8: Create Main App Component

Put everything together in the main App component:

```jsx
// src/App.jsx
import React, { useState } from 'react';
import PresentationForm from './features/generator/PresentationForm';
import PresentationViewer from './features/viewer/PresentationViewer';

function App() {
  const [presentation, setPresentation] = useState(null);
  
  const handlePresentationGenerated = (newPresentation) => {
    setPresentation(newPresentation);
  };
  
  return (
    <div className="min-h-screen flex flex-col">
      <header className="bg-gray-800 text-white p-4">
        <div className="container mx-auto">
          <h1 className="text-2xl font-bold">Presentation Automator</h1>
        </div>
      </header>
      
      <main className="flex-grow flex flex-col container mx-auto py-6">
        {!presentation ? (
          <PresentationForm onPresentationGenerated={handlePresentationGenerated} />
        ) : (
          <div className="flex-grow flex flex-col relative">
            <div className="absolute top-4 right-4 z-10">
              <button 
                className="btn btn-secondary"
                onClick={() => setPresentation(null)}
              >
                Back to Generator
              </button>
            </div>
            <PresentationViewer slides={presentation.slides} />
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

### Step 9: Create Root Entry Point

Update the main entry file:

```jsx
// src/main.jsx
import React from 'react';
import ReactDOM from 'react-dom/client';
import App from './App';
import './index.css';

ReactDOM.createRoot(document.getElementById('root')).render(
  <React.StrictMode>
    <App />
  </React.StrictMode>
);
```

### Step 10: Set Up Environment Configuration

Create an environment configuration file:

```
# .env.development
VITE_API_URL=http://localhost:8000/api
```

```
# .env.production
VITE_API_URL=/api
```

### Step 11: Update the Vite Configuration

Create or update the Vite configuration file:

```javascript
// vite.config.js
import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';

export default defineConfig({
  plugins: [react()],
  server: {
    port: 3000,
    open: true
  },
  build: {
    outDir: 'dist',
    sourcemap: true
  }
});
```

### Step 12: Add Development Scripts to package.json

Update the scripts section in package.json:

```json
"scripts": {
  "dev": "vite",
  "build": "vite build",
  "preview": "vite preview",
  "test": "vitest run",
  "test:watch": "vitest",
  "lint": "eslint src --ext js,jsx"
}
```

### Step 13: Create a Basic Test

Add a simple test for the BasicSlide component:

```jsx
// src/components/slides/BasicSlide.test.jsx
import { describe, it, expect } from 'vitest';
import { render, screen } from '@testing-library/react';
import BasicSlide from './BasicSlide';

describe('BasicSlide', () => {
  it('renders content correctly', () => {
    const content = '<h1>Test Slide</h1><p>This is a test slide</p>';
    render(<BasicSlide content={content} />);
    
    expect(screen.getByText('Test Slide')).toBeInTheDocument();
    expect(screen.getByText('This is a test slide')).toBeInTheDocument();
  });
  
  it('renders notes when provided', () => {
    const content = '<h1>Test Slide</h1>';
    const notes = 'Speaker notes for this slide';
    render(<BasicSlide content={content} notes={notes} />);
    
    expect(screen.getByText('Speaker notes for this slide')).toBeInTheDocument();
  });
});
```

### Step 14: Create README Documentation

Create a comprehensive README.md file:

```markdown
# Presentation Automator Frontend

This is the frontend application for the Presentation Automator, a tool that generates professional presentations from text using AI.

## Features

- Generate presentations from text input
- View presentations using Reveal.js
- Responsive design that works on desktop and mobile

## Requirements

- Node.js 18 or higher
- npm or yarn

## Installation

1. Clone the repository:
   ```bash
   git clone [repository-url]
   cd presentation-automator-frontend
   ```

2. Install dependencies:
   ```bash
   npm install
   ```

3. Create a `.env.local` file with your environment variables:
   ```
   VITE_API_URL=http://localhost:8000/api
   ```

## Development

Run the development server:

```bash
npm run dev
```

The application will be available at `http://localhost:3000`.

## Testing

Run tests:

```bash
npm test
```

Run tests in watch mode:

```bash
npm run test:watch
```

## Building for Production

Build the application:

```bash
npm run build
```

Preview the production build:

```bash
npm run preview
```

## Project Structure

```
presentation-frontend/
├── public/              # Static files
├── src/                 # Source files
│   ├── components/      # Reusable components
│   │   ├── common/      # Common UI components
│   │   └── slides/      # Slide-specific components
│   ├── features/        # Feature modules
│   │   ├── generator/   # Presentation generation
│   │   └── viewer/      # Presentation viewing
│   ├── hooks/           # Custom React hooks
│   ├── services/        # API and other services
│   │   └── api/         # API clients
│   ├── utils/           # Utility functions
│   ├── App.jsx          # Main app component
│   ├── main.jsx         # Entry point
│   └── index.css        # Global styles
├── .env.development     # Development environment variables
├── .env.production      # Production environment variables
├── vite.config.js       # Vite configuration
└── package.json         # Project configuration
```

## Connecting to the Backend

By default, the application expects the backend API to be running at `http://localhost:8000/api`. You can change this by updating the `VITE_API_URL` environment variable.

## Notes

- This application uses Reveal.js for presentation rendering
- Styling is done with Tailwind CSS
- React is used for UI components and state management
```

## Testing Instructions

To verify that the initial frontend implementation is working correctly:

1. Ensure that the backend API from Project Plans 1-4 is running
2. Start the frontend development server using `npm run dev`
3. Navigate to `http://localhost:3000` in your browser
4. Enter some text in the text area and click "Generate Presentation"
5. Verify that the presentation is generated and displayed using Reveal.js
6. Test the navigation between the generation form and presentation viewer
7. Verify that error states are displayed correctly by simulating a failure (e.g., disconnect from the backend)

## Next Steps

After completing this project plan, you will have a basic but functional presentation frontend with:
- A presentation generation form
- A Reveal.js-based presentation viewer
- API integration with the backend
- Basic UI components for error handling and loading states

You're now ready to proceed to Project Plan 6, which will focus on enhancing the frontend with more advanced features such as state management, file uploads, and more sophisticated presentation editing capabilities. 
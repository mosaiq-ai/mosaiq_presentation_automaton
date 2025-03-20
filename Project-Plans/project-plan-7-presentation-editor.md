# Project Plan 7: Presentation Editor Functionality

## Overview

This project plan focuses on implementing editing capabilities for the Presentation Automator frontend. Building upon the viewing and generation features from previous plans, this plan introduces the ability for users to edit slide content, add or remove slides, and make other modifications to their presentations. The editor will provide an intuitive interface for refining AI-generated content to meet specific user needs.

## Objectives

1. Create a slide editor interface
2. Implement slide content editing functionality
3. Add slide management capabilities (add, delete, reorder)
4. Implement slide properties editing
5. Create slide preview thumbnails for editing mode
6. Add autosave functionality for ongoing edits

## Prerequisites

- Completion of Project Plan 5 (Frontend Implementation)
- Completion of Project Plan 6 (State Management and Advanced Features)
- Backend API support for presentation updates

## Deliverables

1. Slide editor component with content editing
2. Slide management interface (add, delete, reorder)
3. Slide properties editor
4. Preview thumbnail navigation in editor mode
5. Autosave implementation

## Time Estimate

Approximately 2-3 weeks for a junior engineer.

## Detailed Implementation Steps

### Step 1: Enhance the Presentation Store with Editing Actions

Update the store to include editing capabilities:

```javascript
// src/store/presentationStore.js (updated with editing actions)
import { create } from 'zustand';
import { 
  generatePresentation, 
  fetchPresentation, 
  generatePresentationFromFile,
  savePresentation 
} from '../services/api/presentationService';

export const usePresentationStore = create((set, get) => ({
  // Existing state from previous plans...
  
  // Editor state
  isEditing: false,
  editingSlideIndex: null,
  isDirty: false,  // Tracks if there are unsaved changes
  saveInProgress: false,
  saveError: null,
  lastSaved: null,
  
  // Enter/exit edit mode
  toggleEditMode: () => {
    const isCurrentlyEditing = get().isEditing;
    set({ 
      isEditing: !isCurrentlyEditing,
      editingSlideIndex: isCurrentlyEditing ? null : get().currentSlideIndex
    });
  },
  
  setEditingSlide: (index) => {
    if (index !== null && (index < 0 || index >= (get().presentation?.slides?.length || 0))) {
      return; // Index out of bounds
    }
    set({ editingSlideIndex: index });
  },
  
  // Update a single slide
  updateSlide: (index, updatedSlide) => {
    const { presentation } = get();
    
    if (!presentation || !presentation.slides) return;
    
    const updatedSlides = [...presentation.slides];
    updatedSlides[index] = {
      ...updatedSlides[index],
      ...updatedSlide
    };
    
    set({
      presentation: {
        ...presentation,
        slides: updatedSlides
      },
      isDirty: true
    });
  },
  
  // Add a new slide
  addSlide: (newSlide = {}) => {
    const { presentation } = get();
    
    if (!presentation) return;
    
    const defaultSlide = {
      slide_number: (presentation.slides?.length || 0) + 1,
      title: 'New Slide',
      content: '<h2>New Slide</h2><p>Add your content here</p>',
      notes: '',
    };
    
    const slides = [...(presentation.slides || [])];
    const newSlideObject = { ...defaultSlide, ...newSlide };
    
    // If editingSlideIndex is set, insert after that slide
    const insertIndex = get().editingSlideIndex !== null
      ? get().editingSlideIndex + 1
      : slides.length;
    
    slides.splice(insertIndex, 0, newSlideObject);
    
    // Update slide numbers
    slides.forEach((slide, idx) => {
      slide.slide_number = idx + 1;
    });
    
    set({
      presentation: {
        ...presentation,
        slides
      },
      isDirty: true,
      // Optionally set the new slide as the editing slide
      editingSlideIndex: insertIndex,
      currentSlideIndex: insertIndex
    });
  },
  
  // Remove a slide
  removeSlide: (index) => {
    const { presentation, currentSlideIndex, editingSlideIndex } = get();
    
    if (!presentation || !presentation.slides) return;
    
    const updatedSlides = presentation.slides.filter((_, i) => i !== index);
    
    // Update slide numbers
    updatedSlides.forEach((slide, idx) => {
      slide.slide_number = idx + 1;
    });
    
    // Adjust current slide index if needed
    let newCurrentIndex = currentSlideIndex;
    if (currentSlideIndex >= updatedSlides.length) {
      newCurrentIndex = Math.max(0, updatedSlides.length - 1);
    } else if (currentSlideIndex >= index) {
      newCurrentIndex = Math.max(0, currentSlideIndex - 1);
    }
    
    // Adjust editing slide index if needed
    let newEditingIndex = editingSlideIndex;
    if (editingSlideIndex !== null) {
      if (editingSlideIndex >= updatedSlides.length) {
        newEditingIndex = Math.max(0, updatedSlides.length - 1);
      } else if (editingSlideIndex >= index) {
        newEditingIndex = Math.max(0, editingSlideIndex - 1);
      }
    }
    
    set({
      presentation: {
        ...presentation,
        slides: updatedSlides
      },
      isDirty: true,
      currentSlideIndex: newCurrentIndex,
      editingSlideIndex: newEditingIndex
    });
  },
  
  // Reorder slides
  reorderSlide: (oldIndex, newIndex) => {
    const { presentation, currentSlideIndex, editingSlideIndex } = get();
    
    if (!presentation || !presentation.slides) return;
    if (newIndex < 0 || newIndex >= presentation.slides.length) return;
    
    const slides = [...presentation.slides];
    const [movedSlide] = slides.splice(oldIndex, 1);
    slides.splice(newIndex, 0, movedSlide);
    
    // Update slide numbers
    slides.forEach((slide, idx) => {
      slide.slide_number = idx + 1;
    });
    
    // Track the current slide if it was moved
    let newCurrentIndex = currentSlideIndex;
    if (currentSlideIndex === oldIndex) {
      newCurrentIndex = newIndex;
    } else if (
      (oldIndex < currentSlideIndex && newIndex >= currentSlideIndex) ||
      (oldIndex > currentSlideIndex && newIndex <= currentSlideIndex)
    ) {
      // Adjust index if the move shifts the position
      newCurrentIndex = oldIndex < newIndex ? currentSlideIndex - 1 : currentSlideIndex + 1;
    }
    
    // Track the editing slide if it was moved
    let newEditingIndex = editingSlideIndex;
    if (editingSlideIndex !== null) {
      if (editingSlideIndex === oldIndex) {
        newEditingIndex = newIndex;
      } else if (
        (oldIndex < editingSlideIndex && newIndex >= editingSlideIndex) ||
        (oldIndex > editingSlideIndex && newIndex <= editingSlideIndex)
      ) {
        // Adjust index if the move shifts the position
        newEditingIndex = oldIndex < newIndex ? editingSlideIndex - 1 : editingSlideIndex + 1;
      }
    }
    
    set({
      presentation: {
        ...presentation,
        slides
      },
      isDirty: true,
      currentSlideIndex: newCurrentIndex,
      editingSlideIndex: newEditingIndex
    });
  },
  
  // Update presentation metadata
  updatePresentationMetadata: (metadata) => {
    const { presentation } = get();
    
    if (!presentation) return;
    
    set({
      presentation: {
        ...presentation,
        ...metadata
      },
      isDirty: true
    });
  },
  
  // Save the current presentation
  savePresentation: async () => {
    const { presentation, isDirty } = get();
    
    if (!presentation || !isDirty) return;
    
    set({ saveInProgress: true, saveError: null });
    
    try {
      const savedPresentation = await savePresentation(presentation);
      set({ 
        presentation: savedPresentation,
        isDirty: false,
        saveInProgress: false,
        lastSaved: new Date()
      });
      return savedPresentation;
    } catch (error) {
      set({ 
        saveError: 'Failed to save presentation',
        saveInProgress: false
      });
      throw error;
    }
  },
  
  // Clear dirty flag (e.g., after a successful autosave)
  clearDirty: () => set({ isDirty: false }),
  
  // Set last saved timestamp
  setLastSaved: (timestamp = new Date()) => set({ lastSaved: timestamp }),
}));
```

### Step 2: Create Slide Editor Component

Create a component for editing individual slides:

```jsx
// src/features/editor/SlideEditor.jsx
import React, { useState, useEffect } from 'react';
import { usePresentationStore } from '../../store/presentationStore';
import LoadingSpinner from '../../components/common/LoadingSpinner';

const SlideEditor = () => {
  const { 
    presentation, 
    editingSlideIndex, 
    updateSlide, 
    savePresentation,
    saveInProgress,
    saveError 
  } = usePresentationStore();
  
  const [editedSlide, setEditedSlide] = useState({
    title: '',
    content: '',
    notes: ''
  });
  
  const [showSaveIndicator, setShowSaveIndicator] = useState(false);
  
  // Update local state when the editing slide changes
  useEffect(() => {
    if (presentation?.slides && editingSlideIndex !== null) {
      const currentSlide = presentation.slides[editingSlideIndex];
      if (currentSlide) {
        setEditedSlide({
          title: currentSlide.title || '',
          content: currentSlide.content || '',
          notes: currentSlide.notes || ''
        });
      }
    }
  }, [presentation?.slides, editingSlideIndex]);
  
  // If no slide is selected for editing
  if (editingSlideIndex === null) {
    return (
      <div className="h-full flex items-center justify-center text-gray-500">
        <p>No slide selected for editing</p>
      </div>
    );
  }
  
  const handleChange = (e) => {
    const { name, value } = e.target;
    setEditedSlide(prev => ({
      ...prev,
      [name]: value
    }));
  };
  
  const handleBlur = () => {
    // Save changes when a field loses focus
    updateSlide(editingSlideIndex, editedSlide);
    
    // Show save indicator briefly
    setShowSaveIndicator(true);
    setTimeout(() => setShowSaveIndicator(false), 1500);
  };
  
  const handleSave = async () => {
    try {
      await savePresentation();
    } catch (error) {
      console.error('Failed to save presentation:', error);
    }
  };
  
  return (
    <div className="h-full flex flex-col p-4 overflow-auto">
      <div className="flex justify-between items-center mb-4">
        <h2 className="text-xl font-bold">Edit Slide {editingSlideIndex + 1}</h2>
        <div className="flex items-center">
          {showSaveIndicator && !saveInProgress && (
            <span className="text-green-600 text-sm mr-2">Changes saved</span>
          )}
          
          {saveError && (
            <span className="text-red-600 text-sm mr-2">{saveError}</span>
          )}
          
          <button 
            className="px-3 py-1 bg-blue-600 text-white rounded hover:bg-blue-700 disabled:opacity-50"
            onClick={handleSave}
            disabled={saveInProgress}
          >
            {saveInProgress ? (
              <div className="flex items-center">
                <LoadingSpinner size="small" message={null} />
                <span className="ml-2">Saving...</span>
              </div>
            ) : (
              "Save All"
            )}
          </button>
        </div>
      </div>
      
      <div className="grid gap-4">
        <div>
          <label className="block text-sm font-medium mb-1">
            Slide Title
          </label>
          <input
            type="text"
            name="title"
            value={editedSlide.title}
            onChange={handleChange}
            onBlur={handleBlur}
            className="w-full p-2 border rounded"
            placeholder="Enter slide title"
          />
        </div>
        
        <div>
          <label className="block text-sm font-medium mb-1">
            Content (HTML)
          </label>
          <textarea
            name="content"
            value={editedSlide.content}
            onChange={handleChange}
            onBlur={handleBlur}
            rows={12}
            className="w-full p-2 border rounded font-mono text-sm"
            placeholder="<h2>Slide Content</h2><p>Your content here...</p>"
          />
        </div>
        
        <div>
          <label className="block text-sm font-medium mb-1">
            Speaker Notes
          </label>
          <textarea
            name="notes"
            value={editedSlide.notes}
            onChange={handleChange}
            onBlur={handleBlur}
            rows={4}
            className="w-full p-2 border rounded"
            placeholder="Notes for the presenter..."
          />
        </div>
      </div>
    </div>
  );
};

export default SlideEditor;
```

### Step 3: Create Slide Preview Component

Create a component to preview the slide being edited:

```jsx
// src/features/editor/SlidePreview.jsx
import React, { useEffect, useRef } from 'react';
import { usePresentationStore } from '../../store/presentationStore';

const SlidePreview = () => {
  const { presentation, editingSlideIndex } = usePresentationStore();
  const previewRef = useRef(null);
  
  // Update preview when slide content changes
  useEffect(() => {
    if (
      presentation?.slides && 
      editingSlideIndex !== null && 
      editingSlideIndex < presentation.slides.length
    ) {
      const slide = presentation.slides[editingSlideIndex];
      if (previewRef.current && slide) {
        previewRef.current.innerHTML = slide.content || '';
      }
    }
  }, [presentation?.slides, editingSlideIndex]);
  
  if (editingSlideIndex === null || !presentation?.slides) {
    return <div className="w-full h-full flex items-center justify-center text-gray-500">No slide selected</div>;
  }
  
  return (
    <div className="w-full h-full flex flex-col">
      <div className="bg-gray-100 p-2 text-sm text-gray-700">
        Preview
      </div>
      <div className="flex-grow bg-white flex items-center justify-center overflow-auto">
        <div 
          className="max-w-2xl w-full p-4 mx-auto slide-preview"
          ref={previewRef}
        />
      </div>
    </div>
  );
};

export default SlidePreview;
```

### Step 4: Create Slide Manager for Adding and Removing Slides

Create a component for managing slides:

```jsx
// src/features/editor/SlideManager.jsx
import React from 'react';
import { usePresentationStore } from '../../store/presentationStore';

const SlideManager = () => {
  const { 
    presentation,
    editingSlideIndex,
    addSlide,
    removeSlide,
    setEditingSlide
  } = usePresentationStore();
  
  const handleAddSlide = () => {
    addSlide();
  };
  
  const handleRemoveSlide = () => {
    if (presentation?.slides?.length <= 1) {
      alert("You cannot remove the only slide in the presentation.");
      return;
    }
    
    if (window.confirm("Are you sure you want to remove this slide?")) {
      removeSlide(editingSlideIndex);
    }
  };
  
  return (
    <div className="bg-gray-800 text-white p-2 flex justify-between items-center">
      <div className="flex space-x-2">
        <button 
          className="px-3 py-1 bg-green-600 rounded hover:bg-green-700"
          onClick={handleAddSlide}
        >
          Add Slide
        </button>
        
        <button 
          className="px-3 py-1 bg-red-600 rounded hover:bg-red-700"
          onClick={handleRemoveSlide}
          disabled={!presentation?.slides || presentation.slides.length <= 1 || editingSlideIndex === null}
        >
          Remove Slide
        </button>
      </div>
      
      <div className="text-sm">
        {presentation?.slides && editingSlideIndex !== null ? (
          <span>Slide {editingSlideIndex + 1} of {presentation.slides.length}</span>
        ) : (
          <span>No slide selected</span>
        )}
      </div>
    </div>
  );
};

export default SlideManager;
```

### Step 5: Create Editor Thumbnails for Navigation

Create a component for navigating between slides in the editor:

```jsx
// src/features/editor/EditorThumbnails.jsx
import React, { useRef } from 'react';
import { usePresentationStore } from '../../store/presentationStore';

const EditorThumbnails = () => {
  const { 
    presentation, 
    editingSlideIndex, 
    setEditingSlide,
    reorderSlide 
  } = usePresentationStore();
  
  const draggedItemIndex = useRef(null);
  const dragOverItemIndex = useRef(null);
  
  if (!presentation?.slides) return null;
  
  const handleDragStart = (e, index) => {
    draggedItemIndex.current = index;
    e.dataTransfer.effectAllowed = 'move';
    // Set ghost drag image
    const dragElement = e.target.cloneNode(true);
    dragElement.style.position = 'absolute';
    dragElement.style.top = '-1000px';
    document.body.appendChild(dragElement);
    e.dataTransfer.setDragImage(dragElement, 0, 0);
    setTimeout(() => {
      document.body.removeChild(dragElement);
    }, 0);
  };
  
  const handleDragOver = (e, index) => {
    e.preventDefault();
    dragOverItemIndex.current = index;
    
    // Add visual indicator for drop position
    const thumbnails = document.querySelectorAll('.slide-thumbnail');
    thumbnails.forEach(item => item.classList.remove('border-dashed', 'border-yellow-500'));
    
    const currentItem = thumbnails[index];
    if (currentItem && draggedItemIndex.current !== index) {
      currentItem.classList.add('border-dashed', 'border-yellow-500');
    }
  };
  
  const handleDragEnd = (e) => {
    e.preventDefault();
    
    // Remove any visual indicators
    const thumbnails = document.querySelectorAll('.slide-thumbnail');
    thumbnails.forEach(item => item.classList.remove('border-dashed', 'border-yellow-500'));
    
    // Reorder if indices are valid and different
    if (
      draggedItemIndex.current !== null && 
      dragOverItemIndex.current !== null && 
      draggedItemIndex.current !== dragOverItemIndex.current
    ) {
      reorderSlide(draggedItemIndex.current, dragOverItemIndex.current);
    }
    
    // Reset drag indices
    draggedItemIndex.current = null;
    dragOverItemIndex.current = null;
  };
  
  return (
    <div className="bg-gray-900 p-2 overflow-x-auto">
      <div className="flex space-x-2">
        {presentation.slides.map((slide, index) => (
          <div
            key={index}
            className={`slide-thumbnail p-1 min-w-[100px] h-16 flex items-center justify-center border cursor-pointer ${
              index === editingSlideIndex 
                ? 'border-blue-500 bg-blue-900' 
                : 'border-gray-700 hover:bg-gray-800'
            }`}
            onClick={() => setEditingSlide(index)}
            draggable
            onDragStart={(e) => handleDragStart(e, index)}
            onDragOver={(e) => handleDragOver(e, index)}
            onDragEnd={handleDragEnd}
          >
            <span className="text-xs text-white truncate">
              Slide {index + 1}
            </span>
          </div>
        ))}
      </div>
    </div>
  );
};

export default EditorThumbnails;
```

### Step 6: Create Presentation Properties Editor

Create a component for editing overall presentation properties:

```jsx
// src/features/editor/PresentationProperties.jsx
import React, { useState, useEffect } from 'react';
import { usePresentationStore } from '../../store/presentationStore';

const PresentationProperties = () => {
  const { presentation, updatePresentationMetadata } = usePresentationStore();
  
  const [title, setTitle] = useState('');
  const [theme, setTheme] = useState('default');
  
  // Update local state when presentation changes
  useEffect(() => {
    if (presentation) {
      setTitle(presentation.title || '');
      setTheme(presentation.theme || 'default');
    }
  }, [presentation]);
  
  const handleTitleChange = (e) => {
    setTitle(e.target.value);
  };
  
  const handleThemeChange = (e) => {
    setTheme(e.target.value);
  };
  
  const handleBlur = () => {
    updatePresentationMetadata({
      title,
      theme
    });
  };
  
  if (!presentation) return null;
  
  return (
    <div className="p-4 bg-gray-100 border-b">
      <h2 className="text-lg font-medium mb-2">Presentation Properties</h2>
      
      <div className="grid grid-cols-2 gap-4">
        <div>
          <label className="block text-sm font-medium mb-1">
            Title
          </label>
          <input
            type="text"
            value={title}
            onChange={handleTitleChange}
            onBlur={handleBlur}
            className="w-full p-2 border rounded"
            placeholder="Presentation Title"
          />
        </div>
        
        <div>
          <label className="block text-sm font-medium mb-1">
            Theme
          </label>
          <select
            value={theme}
            onChange={handleThemeChange}
            onBlur={handleBlur}
            className="w-full p-2 border rounded"
          >
            <option value="default">Default</option>
            <option value="dark">Dark</option>
            <option value="light">Light</option>
            <option value="corporate">Corporate</option>
          </select>
        </div>
      </div>
    </div>
  );
};

export default PresentationProperties;
```

### Step 7: Create Editor Layout Component

Create a layout component that integrates all editor components:

```jsx
// src/features/editor/EditorLayout.jsx
import React, { useEffect } from 'react';
import { usePresentationStore } from '../../store/presentationStore';
import SlideEditor from './SlideEditor';
import SlidePreview from './SlidePreview';
import SlideManager from './SlideManager';
import EditorThumbnails from './EditorThumbnails';
import PresentationProperties from './PresentationProperties';
import useAutosave from '../../hooks/useAutosave';

const EditorLayout = () => {
  const { 
    presentation, 
    editingSlideIndex, 
    setEditingSlide,
    isDirty,
    savePresentation,
    lastSaved
  } = usePresentationStore();
  
  // Initialize editing if not set
  useEffect(() => {
    if (presentation?.slides?.length > 0 && editingSlideIndex === null) {
      setEditingSlide(0);
    }
  }, [presentation, editingSlideIndex, setEditingSlide]);
  
  // Setup autosave
  useAutosave(isDirty, savePresentation, 5000);
  
  return (
    <div className="flex flex-col h-full">
      <PresentationProperties />
      
      <div className="flex-grow flex overflow-hidden">
        {/* Editor panel - left side */}
        <div className="w-1/2 flex flex-col border-r">
          <SlideEditor />
        </div>
        
        {/* Preview panel - right side */}
        <div className="w-1/2 flex flex-col">
          <SlidePreview />
        </div>
      </div>
      
      {/* Bottom controls */}
      <SlideManager />
      
      {/* Thumbnails for navigation */}
      <EditorThumbnails />
      
      {/* Autosave indicator */}
      {lastSaved && (
        <div className="bg-gray-100 p-1 text-xs text-gray-500 text-center border-t">
          Last saved: {lastSaved.toLocaleTimeString()}
        </div>
      )}
    </div>
  );
};

export default EditorLayout;
```

### Step 8: Create Autosave Hook

Create a custom hook for autosaving:

```javascript
// src/hooks/useAutosave.js
import { useEffect, useRef } from 'react';

/**
 * Hook for automatically saving changes after a period of inactivity
 * 
 * @param {boolean} isDirty - Whether there are unsaved changes
 * @param {Function} saveFunction - Function to call to save changes
 * @param {number} delay - Delay in milliseconds before saving
 */
const useAutosave = (isDirty, saveFunction, delay = 2000) => {
  const timeoutRef = useRef(null);
  
  useEffect(() => {
    // Clear any existing timeout
    if (timeoutRef.current) {
      clearTimeout(timeoutRef.current);
    }
    
    // If there are changes to save, set a new timeout
    if (isDirty) {
      timeoutRef.current = setTimeout(async () => {
        try {
          await saveFunction();
        } catch (error) {
          console.error('Autosave failed:', error);
        }
      }, delay);
    }
    
    // Cleanup function to clear timeout on unmount or when dependencies change
    return () => {
      if (timeoutRef.current) {
        clearTimeout(timeoutRef.current);
      }
    };
  }, [isDirty, saveFunction, delay]);
};

export default useAutosave;
```

### Step 9: Update the API Service with Save Functionality

Update the API service to include saving capabilities:

```javascript
// src/services/api/presentationService.js (updated with save functionality)
// Add this function to the existing presentationService.js file

// Save a presentation
export const savePresentation = async (presentation) => {
  try {
    const response = await apiClient.post('/presentations', presentation);
    return response.data;
  } catch (error) {
    console.error('Error saving presentation:', error);
    throw error;
  }
};

// Update a presentation
export const updatePresentation = async (id, presentation) => {
  try {
    const response = await apiClient.put(`/presentations/${id}`, presentation);
    return response.data;
  } catch (error) {
    console.error('Error updating presentation:', error);
    throw error;
  }
};
```

### Step 10: Update App Component with Editor Mode

Update the App component to include the editor layout:

```jsx
// src/App.jsx (updated with editor mode)
import React from 'react';
import PresentationGenerator from './features/generator/PresentationGenerator';
import PresentationViewer from './features/viewer/PresentationViewer';
import EditorLayout from './features/editor/EditorLayout';
import { usePresentationStore } from './store/presentationStore';

function App() {
  const { 
    presentation, 
    clearPresentation, 
    isEditing, 
    toggleEditMode 
  } = usePresentationStore();
  
  return (
    <div className="min-h-screen flex flex-col">
      <header className="bg-gray-800 text-white p-4">
        <div className="container mx-auto flex justify-between items-center">
          <h1 className="text-2xl font-bold">Presentation Automator</h1>
          
          {presentation && (
            <div className="flex space-x-2">
              <button 
                className="px-4 py-2 bg-gray-600 rounded hover:bg-gray-700"
                onClick={toggleEditMode}
              >
                {isEditing ? 'View Presentation' : 'Edit Presentation'}
              </button>
              
              <button 
                className="px-4 py-2 bg-blue-600 rounded hover:bg-blue-700"
                onClick={clearPresentation}
              >
                New Presentation
              </button>
            </div>
          )}
        </div>
      </header>
      
      <main className="flex-grow flex flex-col">
        {!presentation ? (
          <div className="container mx-auto py-6">
            <PresentationGenerator />
          </div>
        ) : (
          <div className="flex-grow flex flex-col">
            {isEditing ? (
              <EditorLayout />
            ) : (
              <PresentationViewer />
            )}
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

### Step 11: Create CSS Styles for Editor Components

Add specific styles for the editor components:

```css
/* Add to src/index.css */

/* Slide preview styling */
.slide-preview {
  min-height: 300px;
  border: 1px solid #ddd;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
}

.slide-preview h1, .slide-preview h2 {
  margin-top: 0.5em;
  margin-bottom: 0.5em;
}

.slide-preview p {
  margin-bottom: 1em;
}

.slide-preview ul, .slide-preview ol {
  margin-left: 1.5em;
  margin-bottom: 1em;
}

/* Editor styling */
.slide-thumbnail.border-dashed {
  border-width: 2px;
}

/* HTML content editor */
textarea[name="content"] {
  font-family: monospace;
  font-size: 0.9rem;
  line-height: 1.5;
  white-space: pre-wrap;
}
```

### Step 12: Create Simple HTML Editor Component

Create a component for editing HTML content:

```jsx
// src/components/editor/HtmlEditor.jsx
import React, { useState, useEffect } from 'react';
import PropTypes from 'prop-types';

const HtmlEditor = ({ initialValue = '', onChange, onBlur }) => {
  const [content, setContent] = useState(initialValue);
  
  // Update editor when initialValue changes
  useEffect(() => {
    setContent(initialValue);
  }, [initialValue]);
  
  const handleChange = (e) => {
    const newValue = e.target.value;
    setContent(newValue);
    if (onChange) onChange(newValue);
  };
  
  const handleBlur = (e) => {
    if (onBlur) onBlur(content);
  };
  
  // Simple toolbar for common HTML elements
  const insertTag = (tag, attributes = '') => {
    // Get the textarea element
    const textarea = document.getElementById('html-editor');
    if (!textarea) return;
    
    // Get cursor position
    const start = textarea.selectionStart;
    const end = textarea.selectionEnd;
    
    const selectedText = content.substring(start, end);
    const beforeText = content.substring(0, start);
    const afterText = content.substring(end);
    
    // Create the HTML tags
    const openTag = attributes ? `<${tag} ${attributes}>` : `<${tag}>`;
    const closeTag = `</${tag}>`;
    
    // Insert the tags around the selected text
    const newContent = beforeText + openTag + selectedText + closeTag + afterText;
    setContent(newContent);
    if (onChange) onChange(newContent);
    
    // Focus back on the textarea and position cursor after insertion
    setTimeout(() => {
      textarea.focus();
      const newCursorPos = beforeText.length + openTag.length + selectedText.length;
      textarea.setSelectionRange(newCursorPos, newCursorPos);
    }, 0);
  };
  
  return (
    <div className="html-editor-container">
      <div className="mb-2 flex flex-wrap">
        <button 
          type="button" 
          className="px-2 py-1 bg-gray-200 text-gray-800 text-sm rounded mr-1 mb-1 hover:bg-gray-300"
          onClick={() => insertTag('h1')}
        >
          H1
        </button>
        <button 
          type="button" 
          className="px-2 py-1 bg-gray-200 text-gray-800 text-sm rounded mr-1 mb-1 hover:bg-gray-300"
          onClick={() => insertTag('h2')}
        >
          H2
        </button>
        <button 
          type="button" 
          className="px-2 py-1 bg-gray-200 text-gray-800 text-sm rounded mr-1 mb-1 hover:bg-gray-300"
          onClick={() => insertTag('p')}
        >
          Paragraph
        </button>
        <button 
          type="button" 
          className="px-2 py-1 bg-gray-200 text-gray-800 text-sm rounded mr-1 mb-1 hover:bg-gray-300"
          onClick={() => insertTag('strong')}
        >
          Bold
        </button>
        <button 
          type="button" 
          className="px-2 py-1 bg-gray-200 text-gray-800 text-sm rounded mr-1 mb-1 hover:bg-gray-300"
          onClick={() => insertTag('em')}
        >
          Italic
        </button>
        <button 
          type="button" 
          className="px-2 py-1 bg-gray-200 text-gray-800 text-sm rounded mr-1 mb-1 hover:bg-gray-300"
          onClick={() => insertTag('ul')}
        >
          List
        </button>
        <button 
          type="button" 
          className="px-2 py-1 bg-gray-200 text-gray-800 text-sm rounded mr-1 mb-1 hover:bg-gray-300"
          onClick={() => insertTag('li')}
        >
          List Item
        </button>
      </div>
      
      <textarea
        id="html-editor"
        value={content}
        onChange={handleChange}
        onBlur={handleBlur}
        rows={12}
        className="w-full p-2 border rounded font-mono text-sm"
        placeholder="<h2>Slide Content</h2><p>Your content here...</p>"
      />
    </div>
  );
};

HtmlEditor.propTypes = {
  initialValue: PropTypes.string,
  onChange: PropTypes.func,
  onBlur: PropTypes.func
};

export default HtmlEditor;
```

### Step 13: Update Slide Editor to Use the HTML Editor

Update the SlideEditor component to use the new HtmlEditor:

```jsx
// src/features/editor/SlideEditor.jsx (updated)

// Replace the content textarea with:
<div>
  <label className="block text-sm font-medium mb-1">
    Content (HTML)
  </label>
  <HtmlEditor
    initialValue={editedSlide.content}
    onChange={(value) => {
      setEditedSlide(prev => ({
        ...prev,
        content: value
      }));
    }}
    onBlur={handleBlur}
  />
</div>
```

Make sure to add the import at the top:

```jsx
import HtmlEditor from '../../components/editor/HtmlEditor';
```

## Testing Instructions

To verify that the editor functionality is working correctly:

1. Start by generating a basic presentation with multiple slides
2. Click the "Edit Presentation" button in the header
3. Test slide navigation:
   - Click on different slide thumbnails at the bottom
   - Verify that the editor and preview update to show the selected slide
4. Test slide editing:
   - Change a slide title and verify it updates in the preview
   - Edit slide content using the HTML editor and verify changes show in preview
   - Add speaker notes and verify they're saved
5. Test slide management:
   - Add a new slide and verify it appears in the thumbnails
   - Remove a slide and verify it's removed from the presentation
   - Try reordering slides by dragging thumbnails and verify the order changes
6. Test presentation properties:
   - Change the presentation title and theme
   - Verify changes are reflected throughout the application
7. Test autosave:
   - Make changes and wait for the autosave timer (5 seconds)
   - Verify the "Last saved" indicator updates
   - Refresh the page and verify changes persist
8. Test toggling between edit and view modes:
   - Click "View Presentation" button
   - Verify the full presentation viewer is shown
   - Click "Edit Presentation" to return to editor

## Troubleshooting

If you encounter issues:

1. Check browser console for JavaScript errors
2. For save/autosave issues:
   - Verify that the API endpoints are correctly implemented
   - Check network requests to ensure proper data is being sent
   - Verify that dirty flag is being set correctly in the store
3. For editor display issues:
   - Ensure CSS styles are correctly applied
   - Check component hierarchy and rendering conditions
4. For HTML preview problems:
   - Verify that the innerHTML is being set correctly
   - Check for any sanitization issues with HTML content
5. For drag-and-drop reordering issues:
   - Ensure event handlers are properly implemented
   - Check that the store is correctly updating slide order

## Next Steps

After completing this project plan, you will have a functional presentation editor with:
- Slide content editing capabilities
- Slide management (add, delete, reorder)
- Real-time preview of changes
- Autosave functionality
- Presentation properties editing

You're now ready to proceed to Project Plan 8, which will focus on implementing export capabilities, presentation sharing, and other advanced features to complete the application. 
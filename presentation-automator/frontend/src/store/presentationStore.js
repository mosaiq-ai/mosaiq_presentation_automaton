import { create } from 'zustand';
import { 
  generatePresentation, 
  fetchPresentation, 
  generatePresentationFromFile,
  savePresentation as saveToAPI
} from '../services/api/presentationService';

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
  
  // Editor state
  isEditing: false,
  editingSlideIndex: null,
  isDirty: false,  // Tracks if there are unsaved changes
  saveInProgress: false,
  saveError: null,
  lastSaved: null,
  
  // Actions
  setCurrentSlide: (index) => set({ currentSlideIndex: index }),
  
  setGenerationOptions: (options) => set({
    generationOptions: {
      ...get().generationOptions,
      ...options
    }
  }),
  
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
      const savedPresentation = await saveToAPI(presentation);
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
  
  generatePresentation: async (text) => {
    console.log('Store - Starting presentation generation with text:', text.substring(0, 100) + '...');
    set({ isLoading: true, error: null });
    console.log('Store - Set isLoading to true');
    
    try {
      const response = await generatePresentation(text, get().generationOptions);
      console.log('Store - Received presentation from API:', response);
      
      // Extract just the presentation object from the response
      const presentationData = response.presentation;
      console.log('Store - Extracted presentation data:', presentationData);
      
      set({ 
        presentation: presentationData, 
        isLoading: false, 
        currentSlideIndex: 0 
      });
      console.log('Store - Updated state with new presentation and set isLoading to false');
      return response;
    } catch (error) {
      console.error('Store - Error generating presentation:', error);
      set({ 
        error: 'Failed to generate presentation', 
        isLoading: false 
      });
      console.log('Store - Set error state and isLoading to false');
      throw error;
    }
  },
  
  generatePresentationFromFile: async (file) => {
    set({ isLoading: true, error: null });
    
    try {
      const response = await generatePresentationFromFile(file, get().generationOptions);
      console.log('Store - Received presentation from file upload API:', response);
      
      // Extract just the presentation object from the response
      const presentationData = response.presentation;
      console.log('Store - Extracted presentation data from file upload:', presentationData);
      
      set({ 
        presentation: presentationData, 
        isLoading: false, 
        currentSlideIndex: 0 
      });
      return response;
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
    currentSlideIndex: 0,
    isEditing: false,
    editingSlideIndex: null,
    isDirty: false,
    saveInProgress: false,
    saveError: null,
    lastSaved: null
  }),
})); 
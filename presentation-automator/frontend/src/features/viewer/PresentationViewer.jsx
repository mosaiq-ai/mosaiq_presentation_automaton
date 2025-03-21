import React, { useEffect, useRef, useState } from 'react';
import Reveal from 'reveal.js';
import 'reveal.js/dist/reveal.css';
// Import a default theme as fallback, will be replaced dynamically
import 'reveal.js/dist/theme/black.css';
import BasicSlide from '../../components/slides/BasicSlide';
import { usePresentationStore } from '../../store/presentationStore';

// Fragment processor to add animations
const processContentWithFragments = (content) => {
  if (!content) return content;
  
  // Add fragment animations to list items
  return content
    // Add fragments to list items that don't already have fragment classes
    .replace(
      /<li(?!\s+class="[^"]*fragment[^"]*")([^>]*)>(.*?)<\/li>/gs, 
      '<li class="fragment fade-in"$1>$2</li>'
    )
    // Add highlight fragments to important terms
    .replace(
      /<strong(?!\s+class="[^"]*fragment[^"]*")([^>]*)>(.*?)<\/strong>/gs,
      '<strong class="fragment highlight-blue"$1>$2</strong>'
    );
};

const PresentationViewer = () => {
  const revealRef = useRef(null);
  const revealInstance = useRef(null);
  const { presentation, currentSlideIndex, setCurrentSlide } = usePresentationStore();
  const [themeLoaded, setThemeLoaded] = useState(false);
  
  // Debug: Log presentation data
  console.log('PresentationViewer - presentation data:', presentation);
  console.log('PresentationViewer - currentSlideIndex:', currentSlideIndex);
  
  // More detailed debugging of slides
  if (presentation) {
    console.log('PresentationViewer - Presentation title:', presentation.title);
    console.log('PresentationViewer - Presentation theme:', presentation.theme);
    console.log('PresentationViewer - Slides array:', presentation.slides);
    if (presentation.slides) {
      console.log('PresentationViewer - Number of slides:', presentation.slides.length);
    }
  }

  // Dynamic theme loading
  useEffect(() => {
    if (presentation?.theme) {
      // Convert presentation theme to lowercase for file naming
      let theme = presentation.theme.toLowerCase();
      
      // Map custom theme names to reveal.js theme names if needed
      const themeMap = {
        'business': 'black',
        'professional': 'white',
        'creative': 'moon',
        'modern': 'league',
        'corporate': 'serif',
        'academic': 'beige', 
        'technical': 'sky',
        'minimalist': 'simple',
        'dramatic': 'blood',
        'default': 'black'
      };
      
      // Use mapped theme if available, otherwise use lowercase theme name
      const revealTheme = themeMap[theme] || theme;
      
      console.log('PresentationViewer - Loading theme:', revealTheme);
      
      // Remove existing theme link elements
      document.querySelectorAll('link[data-reveal-theme]').forEach(link => {
        link.remove();
      });
      
      // Create and append new theme link
      const link = document.createElement('link');
      link.rel = 'stylesheet';
      link.href = `https://unpkg.com/reveal.js@4.3.1/dist/theme/${revealTheme}.css`;
      link.dataset.revealTheme = revealTheme;
      link.onload = () => {
        console.log('PresentationViewer - Theme loaded:', revealTheme);
        setThemeLoaded(true);
      };
      link.onerror = () => {
        console.error('PresentationViewer - Theme failed to load:', revealTheme);
        // Fallback to black theme
        link.href = 'https://unpkg.com/reveal.js@4.3.1/dist/theme/black.css';
      };
      
      document.head.appendChild(link);
    }
  }, [presentation?.theme]);
  
  // Function to determine the best transition for each slide
  const getSlideTransition = (index) => {
    if (!presentation?.slides) return 'slide';
    
    const totalSlides = presentation.slides.length;
    
    // First slide: fade in
    if (index === 0) return 'fade';
    
    // Last slide: zoom
    if (index === totalSlides - 1) return 'zoom';
    
    // Alternating transitions for middle slides
    const transitions = ['slide', 'convex', 'concave'];
    return transitions[index % transitions.length];
  };
  
  useEffect(() => {
    // Initialize Reveal.js after React has rendered slides
    if (revealRef.current && presentation?.slides?.length > 0) {
      console.log('PresentationViewer - Initializing Reveal.js with slides:', presentation.slides);
      
      if (revealInstance.current) {
        console.log('PresentationViewer - Destroying existing Reveal.js instance');
        revealInstance.current.destroy();
      }
      
      revealInstance.current = new Reveal(revealRef.current, {
        embedded: false,
        hash: false,
        controls: true,
        progress: true,
        center: true,
        transition: 'slide',
        // Additional configuration for proper display
        width: '100%',
        height: '100%',
        margin: 0.1,
        minScale: 0.2,
        maxScale: 2.0,
        disableLayout: false,
        display: 'block',
        // Ensure proper size in container
        navigationMode: 'default',
        // Enable fragment animations
        fragments: true,
        // Wait for images to load
        preloadIframes: true,
        // Enable overview mode
        overview: true,
        // Add slide numbers
        slideNumber: 'c/t'
      });
      
      // Add event listener for slide changes
      const handleSlideChange = (event) => {
        const horizontalIndex = event.indexh;
        setCurrentSlide(horizontalIndex);
      };
      
      // Initialize Reveal after a slight delay to ensure DOM is ready
      setTimeout(() => {
        console.log('PresentationViewer - Initializing Reveal.js');
        revealInstance.current.initialize().then(() => {
          console.log('PresentationViewer - Reveal.js initialized successfully');
          revealInstance.current.addEventListener('slidechanged', handleSlideChange);
          
          // Force layout recalculation
          revealInstance.current.layout();
          
          // Fix slide visibility
          const slideElements = revealRef.current.querySelectorAll('.slides section');
          slideElements.forEach(el => {
            // Make sure slides are visible
            el.style.display = 'block';
            el.style.visibility = 'visible';
          });
        });
      }, 100);
      
      // Cleanup
      return () => {
        if (revealInstance.current) {
          revealInstance.current.removeEventListener('slidechanged', handleSlideChange);
          revealInstance.current.destroy();
          revealInstance.current = null;
        }
      };
    } else {
      console.log('PresentationViewer - Not initializing Reveal.js because:', {
        revealRefExists: !!revealRef.current,
        presentationExists: !!presentation,
        slidesExist: !!presentation?.slides,
        slidesLength: presentation?.slides?.length
      });
    }
  }, [presentation?.slides?.length, setCurrentSlide, themeLoaded]);
  
  // Sync to current slide when currentSlideIndex changes externally
  useEffect(() => {
    if (revealInstance.current && revealInstance.current.isReady()) {
      revealInstance.current.slide(currentSlideIndex);
    }
  }, [currentSlideIndex]);
  
  // Add navigation controls
  const PresentationControls = () => {
    return (
      <div className="absolute bottom-4 right-4 z-50 flex space-x-2">
        <button 
          onClick={() => revealInstance.current?.prev()} 
          className="p-2 bg-black bg-opacity-50 text-white rounded hover:bg-opacity-70 transition-all"
          aria-label="Previous slide"
        >
          ◀
        </button>
        <button 
          onClick={() => revealInstance.current?.next()} 
          className="p-2 bg-black bg-opacity-50 text-white rounded hover:bg-opacity-70 transition-all"
          aria-label="Next slide"
        >
          ▶
        </button>
        <button 
          onClick={() => revealInstance.current?.toggleOverview()} 
          className="p-2 bg-black bg-opacity-50 text-white rounded hover:bg-opacity-70 transition-all"
          aria-label="Toggle overview"
        >
          🔍
        </button>
      </div>
    );
  };
  
  if (!presentation || !presentation.slides || presentation.slides.length === 0) {
    console.log('PresentationViewer - No slides to display condition triggered:', {
      presentationExists: !!presentation,
      slidesExist: !!presentation?.slides,
      slidesLength: presentation?.slides?.length
    });
    return <div className="text-center py-10">No slides to display</div>;
  }
  
  return (
    <div className="reveal-container relative" style={{ width: '100%', height: '100vh', overflow: 'hidden' }}>
      <div className="reveal" ref={revealRef} style={{ width: '100%', height: '100%', position: 'relative' }}>
        <div className="slides">
          {presentation.slides.map((slide, index) => (
            <section 
              key={index} 
              data-transition={getSlideTransition(index)}
              data-auto-animate={index > 0 ? "" : undefined}
            >
              <div 
                className="slide-content" 
                dangerouslySetInnerHTML={{ __html: processContentWithFragments(slide.content) }} 
              />
              {slide.notes && (
                <aside className="notes" dangerouslySetInnerHTML={{ __html: slide.notes }}></aside>
              )}
            </section>
          ))}
        </div>
      </div>
      <PresentationControls />
    </div>
  );
};

export default PresentationViewer; 
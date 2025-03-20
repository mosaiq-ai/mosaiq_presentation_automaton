"""
Content extraction service for analyzing document content.

This module provides utilities for extracting various content elements from text,
such as sections, bullet points, keywords, and slide-specific content.
"""

import re
from typing import Any, Dict, List, Optional, Set, Tuple, Union

from loguru import logger

from ..utils.context_manager import GenerationContext


class ContentExtractor:
    """Service for content extraction and analysis."""
    
    def __init__(self):
        """Initialize the content extractor service."""
        logger.info("Initializing content extractor service")
    
    async def extract_sections(
        self, 
        text: str,
        context: Optional[GenerationContext] = None
    ) -> List[Dict[str, Any]]:
        """
        Extract sections from a document based on headings.
        
        Args:
            text: The document text
            context: Context for tracking extraction (optional)
            
        Returns:
            List of sections with headings and content
        """
        if context:
            context.set_stage_status("content_extraction_sections", "in_progress")
        
        # Regex patterns for Markdown headings
        heading_patterns = [
            (r'^#\s+(.*?)$', 1),  # h1 - # Heading
            (r'^##\s+(.*?)$', 2),  # h2 - ## Heading
            (r'^###\s+(.*?)$', 3),  # h3 - ### Heading
            (r'^####\s+(.*?)$', 4),  # h4 - #### Heading
            (r'^#####\s+(.*?)$', 5),  # h5 - ##### Heading
            (r'^######\s+(.*?)$', 6),  # h6 - ###### Heading
        ]
        
        # Process the text line by line
        lines = text.split('\n')
        sections = []
        current_section = None
        
        for line in lines:
            # Check if this line is a heading
            is_heading = False
            for pattern, level in heading_patterns:
                match = re.match(pattern, line, re.MULTILINE)
                if match:
                    # Found a heading
                    heading_text = match.group(1).strip()
                    
                    # Store the previous section if it exists
                    if current_section:
                        sections.append(current_section)
                    
                    # Start a new section
                    current_section = {
                        'level': level,
                        'heading': heading_text,
                        'content': [],
                        'subsections': []
                    }
                    
                    is_heading = True
                    break
            
            # If not a heading, add to current section content
            if not is_heading and current_section:
                current_section['content'].append(line)
        
        # Add the last section
        if current_section:
            sections.append(current_section)
        
        # Convert content lists to strings
        for section in sections:
            section['content'] = '\n'.join(section['content']).strip()
        
        # Organize sections into a hierarchy
        organized_sections = self._organize_sections_hierarchy(sections)
        
        if context:
            context.add_extracted_content('sections', organized_sections)
            context.set_stage_status("content_extraction_sections", "completed")
        
        return organized_sections
    
    def _organize_sections_hierarchy(self, sections: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Organize sections into a hierarchical structure.
        
        Args:
            sections: List of section dictionaries
            
        Returns:
            List of top-level sections with nested subsections
        """
        if not sections:
            return []
        
        # Create a hierarchical structure
        result = []
        section_stack = []
        
        for section in sections:
            level = section['level']
            
            # Pop from stack until we find a parent section
            while section_stack and section_stack[-1]['level'] >= level:
                section_stack.pop()
            
            if section_stack:
                # Add as subsection to the parent
                section_stack[-1]['subsections'].append(section)
            else:
                # This is a top-level section
                result.append(section)
            
            # Push current section to the stack
            section_stack.append(section)
        
        return result
    
    async def extract_bullet_points(
        self, 
        text: str,
        context: Optional[GenerationContext] = None
    ) -> List[Dict[str, Any]]:
        """
        Extract bullet points and lists from a document.
        
        Args:
            text: The document text
            context: Context for tracking extraction (optional)
            
        Returns:
            List of bullet point groups
        """
        if context:
            context.set_stage_status("content_extraction_bullets", "in_progress")
        
        # Regular expressions for different list formats
        bullet_patterns = [
            r'^\s*[\*\-\+]\s+(.*?)$',  # Markdown bullets: *, -, +
            r'^\s*(\d+)[\.\)]\s+(.*?)$',  # Numbered lists: 1. or 1)
        ]
        
        # Process text line by line
        lines = text.split('\n')
        bullet_groups = []
        current_group = None
        
        for line in lines:
            is_bullet = False
            
            # Check for bullet points
            match = re.match(bullet_patterns[0], line, re.MULTILINE)
            if match:
                bullet_text = match.group(1).strip()
                bullet_type = 'unordered'
                is_bullet = True
            else:
                # Check for numbered lists
                match = re.match(bullet_patterns[1], line, re.MULTILINE)
                if match:
                    bullet_number = match.group(1)
                    bullet_text = match.group(2).strip()
                    bullet_type = 'ordered'
                    is_bullet = True
            
            if is_bullet:
                # If this is the first bullet in a group
                if current_group is None or current_group['type'] != bullet_type:
                    if current_group:
                        bullet_groups.append(current_group)
                    
                    current_group = {
                        'type': bullet_type,
                        'context': '',  # Text before the bullet list
                        'items': []
                    }
                
                # Add the bullet point
                if bullet_type == 'ordered':
                    current_group['items'].append({
                        'number': bullet_number,
                        'text': bullet_text
                    })
                else:
                    current_group['items'].append({
                        'text': bullet_text
                    })
            elif line.strip() == '':
                # Empty line might end a bullet group
                if current_group and current_group['items']:
                    bullet_groups.append(current_group)
                    current_group = None
            elif current_group is None:
                # This could be context for a future bullet group
                pass
            elif current_group and not current_group['items']:
                # This is context for the current bullet group
                current_group['context'] += line + '\n'
        
        # Add the last group
        if current_group and current_group['items']:
            bullet_groups.append(current_group)
        
        # Clean up context strings
        for group in bullet_groups:
            group['context'] = group['context'].strip()
        
        if context:
            context.add_extracted_content('bullet_points', bullet_groups)
            context.set_stage_status("content_extraction_bullets", "completed")
        
        return bullet_groups
    
    async def extract_keywords(
        self, 
        text: str,
        max_keywords: int = 10,
        context: Optional[GenerationContext] = None
    ) -> List[Dict[str, Any]]:
        """
        Extract important keywords from a document.
        
        This is a simple implementation that uses word frequency
        and common patterns. For production, consider using NLP libraries.
        
        Args:
            text: The document text
            max_keywords: Maximum number of keywords to extract
            context: Context for tracking extraction (optional)
            
        Returns:
            List of keywords with scores
        """
        if context:
            context.set_stage_status("content_extraction_keywords", "in_progress")
        
        # Normalize text
        text = text.lower()
        
        # Remove common punctuation
        text = re.sub(r'[^\w\s]', ' ', text)
        
        # Get all words
        words = text.split()
        
        # Count word frequency
        word_counts = {}
        for word in words:
            if len(word) > 2:  # Skip very short words
                if word in word_counts:
                    word_counts[word] += 1
                else:
                    word_counts[word] = 1
        
        # Filter out common stop words
        stop_words = {
            'the', 'and', 'or', 'in', 'on', 'at', 'to', 'a', 'an', 'is', 'are', 'was',
            'were', 'for', 'of', 'by', 'with', 'about', 'that', 'this', 'these', 'those'
        }
        
        for word in stop_words:
            if word in word_counts:
                del word_counts[word]
        
        # Sort by frequency
        sorted_words = sorted(
            word_counts.items(), 
            key=lambda x: x[1], 
            reverse=True
        )
        
        # Get top keywords
        keywords = [
            {'word': word, 'count': count, 'score': count / len(words)}
            for word, count in sorted_words[:max_keywords]
        ]
        
        if context:
            context.add_extracted_content('keywords', keywords)
            context.set_stage_status("content_extraction_keywords", "completed")
        
        return keywords
    
    async def extract_slide_content(
        self, 
        text: str,
        num_slides: int = 10,
        context: Optional[GenerationContext] = None
    ) -> List[Dict[str, Any]]:
        """
        Extract content suitable for presentation slides.
        
        Args:
            text: The document text
            num_slides: Target number of slides
            context: Context for tracking extraction (optional)
            
        Returns:
            List of potential slide content
        """
        if context:
            context.set_stage_status("content_extraction_slides", "in_progress")
        
        # First extract sections to understand the document structure
        sections = await self.extract_sections(text)
        
        # Extract bullet points for potential slide content
        bullet_points = await self.extract_bullet_points(text)
        
        # Initialize slides list
        slides = []
        
        # Create title slide
        if sections and sections[0]['level'] == 1:
            title = sections[0]['heading']
            subtitle = ""
            # Try to find a suitable subtitle
            if sections[0]['content']:
                first_para = sections[0]['content'].split('\n\n')[0]
                if len(first_para) < 100:  # Only use short paragraphs
                    subtitle = first_para
            
            slides.append({
                'type': 'title',
                'title': title,
                'subtitle': subtitle
            })
        
        # Create content slides from sections
        for i, section in enumerate(sections):
            # Skip the title section which we already used
            if i == 0 and section['level'] == 1:
                continue
            
            # Only use level 1-3 headings for slides
            if section['level'] <= 3:
                slide = {
                    'type': 'content',
                    'title': section['heading'],
                    'content': []
                }
                
                # Extract a short paragraph for the slide
                if section['content']:
                    paragraphs = section['content'].split('\n\n')
                    if paragraphs:
                        # Use the first paragraph if it's not too long
                        first_para = paragraphs[0]
                        if len(first_para) < 200:
                            slide['content'].append({
                                'type': 'text',
                                'text': first_para
                            })
                
                # Find bullet points that might belong to this section
                for bullet_group in bullet_points:
                    # Simple heuristic: if the bullet group's context contains
                    # the section heading, it probably belongs to this section
                    if (section['heading'].lower() in bullet_group['context'].lower() or
                        (slides and slides[-1]['title'].lower() in bullet_group['context'].lower())):
                        slide['content'].append({
                            'type': 'bullets',
                            'items': [item['text'] for item in bullet_group['items']]
                        })
                
                # Only add if we have some content
                if slide['content']:
                    slides.append(slide)
        
        # If we don't have enough slides, try to create more from remaining sections
        if len(slides) < num_slides:
            # Find sections we haven't used yet
            for section in sections:
                # Skip sections already used
                if any(slide['title'] == section['heading'] for slide in slides):
                    continue
                
                # Create a slide for this section
                slide = {
                    'type': 'content',
                    'title': section['heading'],
                    'content': []
                }
                
                # Extract paragraphs
                if section['content']:
                    paragraphs = section['content'].split('\n\n')
                    if paragraphs:
                        for para in paragraphs[:2]:  # Use up to 2 paragraphs
                            if len(para) < 200:
                                slide['content'].append({
                                    'type': 'text',
                                    'text': para
                                })
                
                # Only add if we have some content
                if slide['content']:
                    slides.append(slide)
                
                # Stop if we have enough slides
                if len(slides) >= num_slides:
                    break
        
        # Add conclusion slide if we have space
        if len(slides) < num_slides:
            slides.append({
                'type': 'conclusion',
                'title': 'Conclusion',
                'content': [
                    {
                        'type': 'text',
                        'text': 'Thank you for your attention!'
                    }
                ]
            })
        
        if context:
            context.add_extracted_content('slides', slides)
            context.set_stage_status("content_extraction_slides", "completed")
        
        return slides


# Create a singleton instance
content_extractor = ContentExtractor()

# Convenience functions for direct module use
async def extract_sections(text: str, context: Optional[GenerationContext] = None) -> List[Dict[str, Any]]:
    """Extract sections from a document."""
    return await content_extractor.extract_sections(text, context)

async def extract_bullet_points(text: str, context: Optional[GenerationContext] = None) -> List[Dict[str, Any]]:
    """Extract bullet points from a document."""
    return await content_extractor.extract_bullet_points(text, context)

async def extract_keywords(text: str, max_keywords: int = 10, context: Optional[GenerationContext] = None) -> List[Dict[str, Any]]:
    """Extract keywords from a document."""
    return await content_extractor.extract_keywords(text, max_keywords, context)

async def extract_slide_content(text: str, num_slides: int = 10, context: Optional[GenerationContext] = None) -> List[Dict[str, Any]]:
    """Extract content suitable for presentation slides."""
    return await content_extractor.extract_slide_content(text, num_slides, context) 
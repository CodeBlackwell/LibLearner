"""
File type detection and processing module for LibLearner.
Handles detection of file types and routing to appropriate processors.
"""

import os
import mimetypes
import magic  # python-magic library for robust file type detection
from typing import Optional, Dict, Type, List, Union
from abc import ABC, abstractmethod
from pathlib import Path
from collections import defaultdict

# Default directories to ignore
DEFAULT_IGNORE_DIRS = {"venv", ".git", "ds_venv", "dw_env", "__pycache__", ".venv", "*.egg-info"}

class FileProcessor(ABC):
    """Base class for file processors."""
    
    @abstractmethod
    def get_supported_types(self) -> List[str]:
        """
        Returns the MIME types this processor can handle.
        
        Returns:
            List of supported MIME types
        """
        pass
    
    @abstractmethod
    def process_file(self, file_path: str) -> Union[dict, str]:
        """
        Process a file and extract information.
        
        Args:
            file_path: Path to the file to process
            
        Returns:
            Either:
            - Dictionary containing extracted information for function-based processors
            - String path to the CSV file for cell-based processors
            - None if processing failed
        """
        pass

class FileTypeDetector:
    """Handles file type detection using multiple methods."""
    
    def __init__(self):
        """Initialize the detector with magic library."""
        self._magic = magic.Magic(mime=True)
        
        # Define strict mappings for file extensions
        self._extension_mime_types = {
            '.py': 'text/x-python',
            '.pyi': 'text/x-python',
            '.ipynb': 'application/x-ipynb+json',
            '.txt': 'text/plain',
            '.md': 'text/markdown',
            '.json': 'application/json'
        }
    
    def detect_type(self, file_path: str) -> str:
        """
        Detect the MIME type of a file using multiple methods.
        
        Args:
            file_path: Path to the file
            
        Returns:
            MIME type string
        """
        # Get file extension
        extension = Path(file_path).suffix.lower()
        
        # First check our strict extension mappings
        if extension in self._extension_mime_types:
            return self._extension_mime_types[extension]
            
        # Try magic library
        try:
            mime_type = self._magic.from_file(file_path)
            if mime_type:
                return mime_type
        except Exception as e:
            print(f"Warning: Magic library failed for {file_path}: {str(e)}")
        
        # Fallback to mimetypes library
        mime_type, _ = mimetypes.guess_type(file_path)
        return mime_type if mime_type else 'application/octet-stream'

class ProcessorRegistry:
    """Registry for file processors."""
    
    def __init__(self):
        """Initialize registry and file type detector."""
        self._processors = {}
        self._detector = FileTypeDetector()
    
    def register_processor(self, processor_class: Type[FileProcessor]) -> None:
        """Register a processor for its supported MIME types."""
        processor = processor_class()
        for mime_type in processor.get_supported_types():
            print(f"DEBUG: Registering processor for MIME type: {mime_type}")
            self._processors[mime_type] = processor_class
    
    def get_processor(self, file_path: str) -> Optional[FileProcessor]:
        """Get appropriate processor for a file."""
        mime_type = self._detector.detect_type(file_path)
        
        # For text/plain files, check extension first
        if mime_type == 'text/plain':
            ext = Path(file_path).suffix.lower()
            if ext == '.py':
                mime_type = 'text/x-python'
            else:
                print(f"DEBUG: Skipping non-Python text file: {file_path}")
                return None
        
        processor_class = self._processors.get(mime_type)
        print(f"DEBUG: Looking for processor for {mime_type}, found: {processor_class is not None}")
        return processor_class() if processor_class else None
    
    def process_file(self, file_path: str) -> Optional[Union[dict, str]]:
        """Process a single file using appropriate processor."""
        processor = self.get_processor(file_path)
        if processor:
            try:
                result = processor.process_file(file_path)
                print(f"DEBUG: Successfully processed {file_path}")
                return result
            except Exception as e:
                print(f"DEBUG: Error processing {file_path}: {str(e)}")
                return None
        return None

    def process_directory(self, directory_path: str, ignore_dirs: Optional[List[str]] = None) -> Dict[str, List[Union[dict, str]]]:
        """
        Process all files in a directory recursively.
        
        Args:
            directory_path: Path to the directory to process
            ignore_dirs: List of directory names to ignore (in addition to DEFAULT_IGNORE_DIRS)
        
        Returns:
            Dictionary mapping relative paths to lists of processing results
        """
        results = defaultdict(list)
        
        # Split ignore patterns into exact matches and glob patterns
        exact_ignores = set()
        glob_patterns = set()
        
        # Process default ignore dirs
        for pattern in DEFAULT_IGNORE_DIRS:
            if '*' in pattern:
                glob_patterns.add(pattern)
            else:
                exact_ignores.add(pattern)
        
        # Add user-provided ignore dirs
        if ignore_dirs:
            for pattern in ignore_dirs:
                if '*' in pattern:
                    glob_patterns.add(pattern)
                else:
                    exact_ignores.add(pattern)

        for root, dirs, files in os.walk(directory_path):
            # Remove directories that match exact names or glob patterns
            dirs[:] = [d for d in dirs 
                      if d not in exact_ignores 
                      and not any(part in exact_ignores for part in Path(d).parts)
                      and not any(Path(d).match(pattern) for pattern in glob_patterns)]
            
            # Get relative path from input directory
            rel_path = os.path.relpath(root, directory_path)
            rel_path = '.' if rel_path == '.' else rel_path
            
            # Skip if current directory matches any glob pattern
            if any(Path(root).match(pattern) for pattern in glob_patterns):
                continue
            
            for file in files:
                file_path = os.path.join(root, file)
                result = self.process_file(file_path)
                if result:
                    results[rel_path].append(result)
        
        return dict(results)

# Global registry instance
registry = ProcessorRegistry()

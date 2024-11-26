"""
File type detection and processing module for LibLearner.
Handles detection of file types and routing to appropriate processors.
"""

import os
import mimetypes
import magic  # python-magic library for robust file type detection
from typing import Optional, Dict, Type, List
from abc import ABC, abstractmethod
from pathlib import Path

# Default directories to ignore
DEFAULT_IGNORE_DIRS = {"venv", ".git", "ds_venv", "dw_env", "__pycache__"}

class FileProcessor(ABC):
    """Base class for all file type processors."""
    
    @abstractmethod
    def process_file(self, file_path: str) -> dict:
        """Process a single file and return extracted information."""
        pass

    @abstractmethod
    def get_supported_types(self) -> List[str]:
        """Return list of MIME types this processor can handle."""
        pass

class FileTypeDetector:
    """Handles file type detection using multiple methods."""
    
    def __init__(self):
        self._mime = magic.Magic(mime=True)
        # Ensure all MIME types are loaded
        mimetypes.init()
        
        # Add common Python extensions
        mimetypes.add_type('text/x-python', '.py')
        mimetypes.add_type('text/x-python', '.pyw')
        mimetypes.add_type('text/x-python', '.pyi')
    
    def detect_type(self, file_path: str) -> str:
        """
        Detect file type using multiple methods.
        Returns MIME type string.
        """
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"File not found: {file_path}")
            
        try:
            # First check file extension
            ext_type = mimetypes.guess_type(file_path)[0]
            if ext_type:
                print(f"DEBUG: Extension-based MIME type for {file_path}: {ext_type}")
                return ext_type
            
            # Then try python-magic for content-based detection
            mime_type = self._mime.from_file(file_path)
            print(f"DEBUG: Content-based MIME type for {file_path}: {mime_type}")
            
            # Special case: if it's a text file and has .py extension, treat as Python
            if mime_type == 'text/plain' and file_path.endswith('.py'):
                return 'text/x-python'
                
            return mime_type or 'application/octet-stream'
            
        except Exception as e:
            print(f"DEBUG: Error detecting file type for {file_path}: {str(e)}")
            return 'application/octet-stream'

class ProcessorRegistry:
    """Registry for file processors."""
    
    def __init__(self):
        self._processors: Dict[str, Type[FileProcessor]] = {}
        self._detector = FileTypeDetector()
    
    def register_processor(self, processor_class: Type[FileProcessor]):
        """Register a processor for specific MIME types."""
        processor = processor_class()
        for mime_type in processor.get_supported_types():
            print(f"DEBUG: Registering processor for MIME type: {mime_type}")
            self._processors[mime_type] = processor_class
    
    def get_processor(self, file_path: str) -> Optional[FileProcessor]:
        """Get appropriate processor for a file."""
        mime_type = self._detector.detect_type(file_path)
        processor_class = self._processors.get(mime_type)
        print(f"DEBUG: Looking for processor for {mime_type}, found: {processor_class is not None}")
        return processor_class() if processor_class else None
    
    def process_file(self, file_path: str) -> Optional[dict]:
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

    def process_directory(self, directory_path: str, ignore_dirs: Optional[List[str]] = None) -> Dict[str, List[dict]]:
        """
        Process all files in a directory recursively.
        
        Args:
            directory_path: Path to the directory to process
            ignore_dirs: List of directory names to ignore (in addition to default ignored dirs)
            
        Returns:
            Dictionary mapping folders to their processed files
        """
        # Combine default ignore dirs with user-provided ones
        ignore_set = DEFAULT_IGNORE_DIRS.copy()
        if ignore_dirs:
            ignore_set.update(ignore_dirs)
            
        results = {}
        
        for root, dirs, files in os.walk(directory_path):
            # Remove ignored directories from dirs list to prevent walking into them
            dirs[:] = [d for d in dirs if d not in ignore_set]
            
            # Skip this directory if it's in the ignore list
            if any(d in ignore_set for d in Path(root).parts):
                continue
                
            relative_folder = os.path.relpath(root, directory_path)
            
            folder_results = []
            for file in files:
                file_path = os.path.join(root, file)
                print(f"DEBUG: Processing file: {file_path}")
                file_result = self.process_file(file_path)
                if file_result:
                    folder_results.append(file_result)
                    
            if folder_results:
                results[relative_folder] = folder_results
                
        return results

# Global registry instance
registry = ProcessorRegistry()

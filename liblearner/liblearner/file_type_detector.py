"""
File type detection utility for LibLearner.

This module provides functionality to detect file types using multiple methods:
1. File extension mapping
2. Magic library content detection
3. Python mimetypes fallback
"""

import os
import mimetypes
import magic
from pathlib import Path
from typing import Optional


class FileTypeDetector:
    """Detects file types using multiple methods."""

    def __init__(self):
        """Initialize the file type detector."""
        # Initialize mimetypes database
        mimetypes.init()
        
        # Common file extension overrides
        self.extension_overrides = {
            '.py': 'text/x-python',
            '.yaml': 'text/x-yaml',
            '.yml': 'text/x-yaml',
            '.md': 'text/markdown',
            '.rst': 'text/x-rst',
            '.ini': 'text/x-ini',
            '.toml': 'text/x-toml',
            '.json': 'application/json',
            '.txt': 'text/plain',
        }

    def detect_type(self, file_path: str) -> str:
        """
        Detect the MIME type of a file using multiple methods.
        
        Args:
            file_path: Path to the file
            
        Returns:
            Detected MIME type as string
        """
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"File not found: {file_path}")

        # Try extension override first
        ext = Path(file_path).suffix.lower()
        if ext in self.extension_overrides:
            mime_type = self.extension_overrides[ext]
            print(f"  Found extension mapping: {ext} -> {mime_type}")
            return mime_type

        # Try magic library
        try:
            mime = magic.Magic(mime=True)
            detected_type = mime.from_file(file_path)
            print(f"  Magic library detected: {detected_type}")
            if detected_type:
                # Special case: if it's text/plain but has .py extension, treat as Python
                if detected_type == 'text/plain' and ext == '.py':
                    return 'text/x-python'
                return detected_type
        except Exception as e:
            print(f"  Magic library failed: {str(e)}")
            pass  # Fall through to mimetypes

        # Fall back to mimetypes
        mime_type, _ = mimetypes.guess_type(file_path)
        if mime_type:
            print(f"  Mimetypes detected: {mime_type}")
            return mime_type
            
        # Default to application/octet-stream
        print("  Defaulting to application/octet-stream")
        return 'application/octet-stream'

    def is_text_file(self, file_path: str) -> bool:
        """
        Check if a file is a text file.
        
        Args:
            file_path: Path to the file
            
        Returns:
            True if the file is a text file, False otherwise
        """
        mime_type = self.detect_type(file_path)
        return mime_type.startswith('text/') or mime_type in {
            'application/json',
            'application/x-yaml',
            'application/xml'
        }

    def get_processor_type(self, file_path: str) -> Optional[str]:
        """
        Get the appropriate processor type for a file.
        
        Args:
            file_path: Path to the file
            
        Returns:
            Processor type string or None if no appropriate processor found
        """
        mime_type = self.detect_type(file_path)
        
        # Map MIME types to processor types
        processor_map = {
            'text/x-python': 'python',
            'text/x-yaml': 'yaml',
            'application/x-yaml': 'yaml',
            'text/yaml': 'yaml',
            'text/markdown': 'markdown',
            'text/x-rst': 'rst',
            'text/x-ini': 'ini',
            'text/x-toml': 'toml',
            'application/json': 'json',
        }
        
        return processor_map.get(mime_type)

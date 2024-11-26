"""
Python file processor for LibLearner.
Handles extraction of information from Python source files.
"""

from typing import List
from ..file_processor import FileProcessor
from ..python_extractor import process_file as process_python_file

class PythonProcessor(FileProcessor):
    """Processor for Python source files."""
    
    def process_file(self, file_path: str) -> dict:
        """
        Process a Python file using the existing extractor functionality.
        Returns a dictionary containing the extracted information.
        
        Args:
            file_path: Path to the Python file to process
            
        Returns:
            Dictionary containing:
                - type: "python"
                - path: file path
                - functions: list of extracted functions
                - error: error message if processing failed
        """
        try:
            functions = process_python_file(file_path)
            return {
                "type": "python",
                "path": file_path,
                "functions": functions
            }
        except Exception as e:
            return {
                "type": "python",
                "path": file_path,
                "error": str(e)
            }
    
    def get_supported_types(self) -> List[str]:
        """Return supported MIME types."""
        return [
            "text/x-python",
            "text/x-python-script",
            "text/plain",  # Added to handle python-magic detection
            "application/x-python",  # Added for completeness
            "application/x-python-code"  # Added for completeness
        ]

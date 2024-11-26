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
            with open(file_path, 'r') as f:
                source_code = f.read()
                if not source_code.strip():
                    return {
                        "type": "python",
                        "path": file_path,
                        "functions": []
                    }
            
            function_tuples = process_python_file(file_path)
            functions = []
            for func_tuple in function_tuples:
                functions.append({
                    "file": func_tuple[0],
                    "class": func_tuple[1],
                    "order": func_tuple[2],
                    "name": func_tuple[3],
                    "parameters": func_tuple[4],
                    "docstring": func_tuple[5],
                    "code": func_tuple[6]
                })
            return {
                "type": "python",
                "path": file_path,
                "functions": functions
            }
        except SyntaxError as e:
            return {
                "type": "python",
                "path": file_path,
                "functions": [],
                "error": f"Syntax error: {str(e)}"
            }
        except Exception as e:
            return {
                "type": "python",
                "path": file_path,
                "functions": [],
                "error": str(e)
            }
    
    def get_supported_types(self) -> List[str]:
        """Return supported MIME types."""
        return [
            "text/x-python",
            "text/x-python-script",
            "application/x-python",
            "application/x-python-code"
        ]

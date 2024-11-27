"""
Python file processor for LibLearner.
Handles extraction of information from Python source files.
"""

from typing import List
import pandas as pd
from ..file_processor import FileProcessor
from ..python_extractor import process_file as process_python_file

class PythonProcessor(FileProcessor):
    """Processor for Python source files."""
    
    def __init__(self):
        """Initialize the Python processor."""
        super().__init__()
    
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
                    self.results_df = pd.DataFrame(columns=['type', 'name', 'content', 'props'])
                    return {
                        "type": "python",
                        "path": file_path,
                        "functions": []
                    }
            
            function_tuples = process_python_file(file_path)
            functions = []
            results_data = []
            
            for func_tuple in function_tuples:
                func_dict = {
                    "file": func_tuple[0],
                    "class": func_tuple[1],
                    "order": func_tuple[2],
                    "name": func_tuple[3],
                    "parameters": func_tuple[4],
                    "docstring": func_tuple[5],
                    "code": func_tuple[6]
                }
                functions.append(func_dict)
                
                # Add to results DataFrame
                results_data.append({
                    'type': 'function',
                    'name': f"{func_dict['class']}.{func_dict['name']}" if func_dict['class'] else func_dict['name'],
                    'content': func_dict['code'],
                    'props': str({
                        'parameters': func_dict['parameters'],
                        'docstring': func_dict['docstring'],
                        'order': func_dict['order']
                    })
                })
            
            # Update the results DataFrame
            self.results_df = pd.DataFrame(results_data)
            
            return {
                "type": "python",
                "path": file_path,
                "functions": functions
            }
        except SyntaxError as e:
            self.results_df = pd.DataFrame(columns=['type', 'name', 'content', 'props'])
            return {
                "type": "python",
                "path": file_path,
                "functions": [],
                "error": f"Syntax error: {str(e)}"
            }
        except Exception as e:
            self.results_df = pd.DataFrame(columns=['type', 'name', 'content', 'props'])
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

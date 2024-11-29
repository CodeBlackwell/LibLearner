"""
Improved Python Processor for LibLearner.

This processor extracts structured information from Python source files, including:
- Function definitions
- Class definitions
- Docstrings
- Function parameters
- Code content
"""

import ast
import logging
import pandas as pd
from pathlib import Path
from typing import List, Dict, Any
from ..file_processor import FileProcessor
from ..processing_result import PythonProcessingResult

# Set up a logger for debug output
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class PythonProcessor(FileProcessor):
    """Processor for Python source files."""
    
    def __init__(self, debug: bool = False):
        """Initialize the Python processor."""
        super().__init__()
        self.debug = debug
        if self.debug:
            logger.setLevel(logging.DEBUG)
        self.supported_types = {
            'text/x-python',
            'text/x-python-script',
            'application/x-python',
            'application/x-python-code',
            'text/x-python-executable'  # For .pyw files
        }

    def get_supported_types(self) -> List[str]:
        """Return list of supported MIME types."""
        return list(self.supported_types)

    def process_file(self, file_path: str) -> PythonProcessingResult:
        """
        Process a Python file and extract structured information.
        
        Args:
            file_path: Path to the Python file
            
        Returns:
            PythonProcessingResult containing:
            - functions: List of extracted function information
            - classes: List of extracted class information 
            - errors: List of any errors encountered
            - file_info: Dictionary with file metadata
        """
        path = Path(file_path)
        result = PythonProcessingResult()
        results_data = []

        if not path.exists():
            error_msg = f"Error reading file: File not found - {file_path}"
            result.errors.append(error_msg)
            logger.error(error_msg)
            return result

        try:
            content = path.read_text()
        except Exception as e:
            error_msg = f"Error reading file: {str(e)}"
            result.errors.append(error_msg)
            logger.error(error_msg)
            return result

        result.file_info = {
            'name': path.name,
            'path': str(path.absolute()),
            'size': path.stat().st_size,
            'last_modified': path.stat().st_mtime
        }

        try:
            logger.debug("Parsing Python AST")
            tree = ast.parse(content)
            logger.debug("Processing Python nodes")
            self._process_node(tree, result, results_data, file_path)
        except SyntaxError as e:
            error_msg = f"Python syntax error: {str(e)}"
            result.errors.append(error_msg)
            logger.error(error_msg)
        except Exception as e:
            error_msg = f"Unexpected error: {str(e)}"
            result.errors.append(error_msg)
            logger.error(error_msg)

        # Create DataFrame from results data
        if results_data:
            self.results_df = pd.DataFrame(results_data)
            # Add file info to each row
            self.results_df['filepath'] = str(path.absolute())
            self.results_df['type'] = 'python'  # Use a consistent type name
            logger.debug(f"Created DataFrame with {len(results_data)} rows")
        else:
            self.results_df = pd.DataFrame()
        return result

    def _process_node(self, node: ast.AST, result: PythonProcessingResult, results_data: List[Dict], file_path: str) -> None:
        """Process a Python AST node and extract information."""
        if isinstance(node, ast.FunctionDef):
            self._process_function(node, result, results_data, file_path)
        elif isinstance(node, ast.ClassDef):
            self._process_class(node, result, results_data, file_path)
        else:
            for child in ast.iter_child_nodes(node):
                self._process_node(child, result, results_data, file_path)
    
    def _process_function(self, node: ast.FunctionDef, result: PythonProcessingResult, results_data: List[Dict], file_path: str) -> None:
        """Process a function definition node."""
        function_info = {
            'name': node.name,
            'docstring': ast.get_docstring(node) or '',
            'type': 'function',
            'args': [arg.arg for arg in node.args.args],
            'returns': None,  # We'll add return type hints later
            'content': ast.unparse(node),
            'filepath': file_path
        }
        
        result.functions.append(function_info)
        results_data.append({
            'type': 'function',
            'name': node.name,
            'content': function_info['content'],
            'props': str({'args': function_info['args'], 'returns': function_info['returns']}),
            'filepath': file_path
        })
        
        # Process nested functions
        for child in ast.iter_child_nodes(node):
            if isinstance(child, ast.FunctionDef):
                nested_function_info = {
                    'name': f"{node.name}.{child.name}",
                    'docstring': ast.get_docstring(child) or '',
                    'type': 'function',
                    'args': [arg.arg for arg in child.args.args],
                    'returns': None,
                    'content': ast.unparse(child),
                    'filepath': file_path
                }
                result.functions.append(nested_function_info)
                results_data.append({
                    'type': 'function',
                    'name': nested_function_info['name'],
                    'content': nested_function_info['content'],
                    'props': str({'args': nested_function_info['args'], 'returns': nested_function_info['returns']}),
                    'filepath': file_path
                })

    def _process_class(self, node: ast.ClassDef, result: PythonProcessingResult, results_data: List[Dict], file_path: str) -> None:
        """Process a class definition node."""
        class_info = {
            'name': node.name,
            'docstring': ast.get_docstring(node) or '',
            'type': 'class',
            'methods': [],
            'filepath': file_path
        }
        
        # Process class methods
        for child in ast.iter_child_nodes(node):
            if isinstance(child, ast.FunctionDef):
                method_info = {
                    'name': child.name,
                    'docstring': ast.get_docstring(child) or '',
                    'type': 'method',
                    'args': [arg.arg for arg in child.args.args],
                    'returns': None,
                    'content': ast.unparse(child)
                }
                class_info['methods'].append(method_info)
                results_data.append({
                    'type': 'method',
                    'name': f"{node.name}.{child.name}",
                    'content': method_info['content'],
                    'props': str({'args': method_info['args'], 'returns': method_info['returns']}),
                    'filepath': file_path
                })
        
        result.classes.append(class_info)
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

# Set up a logger for debug output
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class PythonProcessingResult:
    """Result object for Python processing."""

    def __init__(self):
        """Initialize the Python processing result."""
        self.errors: List[str] = []
        self.functions: List[Dict] = []
        self.classes: List[Dict] = []
        self.file_info: Dict[str, Any] = {}


class PythonProcessor(FileProcessor):
    """Processor for Python source files."""
    
    def __init__(self, debug: bool = False):
        """Initialize the Python processor."""
        super().__init__()
        self.debug = debug
        if self.debug:
            logger.setLevel(logging.DEBUG)
        self.supported_types = {'text/x-python', 'text/x-python-script', 'application/x-python', 'application/x-python-code'}

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

        self.results_df = pd.DataFrame(results_data)
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
        func_info = {
            'name': node.name,
            'lineno': node.lineno,
            'parameters': [a.arg for a in node.args.args],
            'docstring': ast.get_docstring(node) or '',
            'code': ast.unparse(node)
        }
        result.functions.append(func_info)
        
        results_data.append({
            'type': 'function',
            'name': func_info['name'],
            'content': func_info['code'],
            'props': str({
                'lineno': func_info['lineno'],
                'parameters': func_info['parameters'],
                'docstring': func_info['docstring']
            }),
            'filepath': file_path
        })

    def _process_class(self, node: ast.ClassDef, result: PythonProcessingResult, results_data: List[Dict], file_path: str) -> None:
        """Process a class definition node."""
        class_info = {
            'name': node.name,
            'lineno': node.lineno,
            'docstring': ast.get_docstring(node) or '',
            'code': ast.unparse(node)
        }
        result.classes.append(class_info)
        
        results_data.append({
            'type': 'class',
            'name': class_info['name'],
            'content': class_info['code'],
            'props': str({
                'lineno': class_info['lineno'],
                'docstring': class_info['docstring']
            }),
            'filepath': file_path
        })
        
        # Process methods and nested classes
        for child in node.body:
            self._process_node(child, result, results_data, file_path)
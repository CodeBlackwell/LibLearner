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
        self._all_results = []  # Store all results to combine later
        self._current_path = []  # Track current path in AST
        self._order_counter = 0  # Track order of elements
        
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
        # Reset order counter for each file
        self._order_counter = 0
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

        # Store results data for later DataFrame creation
        if results_data:
            # Add file info to each result
            for data in results_data:
                data['filepath'] = str(path.absolute())
            self._all_results.extend(results_data)
            logger.debug(f"Added {len(results_data)} rows from {file_path}")
            
            # Update the combined DataFrame with specific column order
            df = pd.DataFrame(self._all_results)
            # Rename 'type' to 'processor_type' for clarity
            df = df.rename(columns={'type': 'processor_type'})
            # Reorder columns
            column_order = ['filepath', 'parent_path', 'order', 'name', 'content', 'props', 'processor_type']
            self.results_df = df[column_order]
            
        return result

    def _get_current_path(self) -> str:
        """Get the current path in dot notation."""
        return '.'.join(self._current_path) if self._current_path else ''

    def _process_node(self, node: ast.AST, result: PythonProcessingResult, results_data: List[Dict], file_path: str) -> None:
        """Process a Python AST node and extract information."""
        if isinstance(node, ast.FunctionDef):
            self._process_function(node, result, results_data, file_path)
        elif isinstance(node, ast.ClassDef):
            self._process_class(node, result, results_data, file_path)
        elif isinstance(node, ast.Module):
            # Process module-level nodes
            for child in ast.iter_child_nodes(node):
                self._process_node(child, result, results_data, file_path)
        elif isinstance(node, (ast.Import, ast.ImportFrom)):
            self._process_import(node, results_data, file_path)
        elif isinstance(node, ast.Assign):
            self._process_assignment(node, results_data, file_path)
        else:
            # Recursively process other nodes
            for child in ast.iter_child_nodes(node):
                self._process_node(child, result, results_data, file_path)

    def _process_function(self, node: ast.FunctionDef, result: PythonProcessingResult, results_data: List[Dict], file_path: str) -> None:
        """Process a function definition node."""
        # Add function name to current path
        self._current_path.append(node.name)
        self._order_counter += 1  # Increment counter
        
        function_info = {
            'name': node.name,
            'docstring': ast.get_docstring(node) or '',
            'type': 'method' if self._current_path[:-1] else 'function',  # If has parent, it's a method
            'args': [arg.arg for arg in node.args.args],
            'returns': None,  # We'll add return type hints later
            'content': ast.unparse(node),
            'filepath': file_path,
            'parent_path': self._get_current_path(),
            'order': self._order_counter
        }
        
        result.functions.append(function_info)
        results_data.append({
            'type': function_info['type'],
            'name': node.name,
            'content': function_info['content'],
            'props': str({'args': function_info['args'], 'returns': function_info['returns']}),
            'filepath': file_path,
            'parent_path': self._get_current_path(),
            'order': self._order_counter
        })
        
        # Process nested functions
        for child in ast.iter_child_nodes(node):
            if isinstance(child, ast.FunctionDef):
                self._process_function(child, result, results_data, file_path)
        
        # Remove function name from current path
        self._current_path.pop()

    def _process_class(self, node: ast.ClassDef, result: PythonProcessingResult, results_data: List[Dict], file_path: str) -> None:
        """Process a class definition node."""
        # Add class name to current path
        self._current_path.append(node.name)
        self._order_counter += 1  # Increment counter
        
        class_info = {
            'name': node.name,
            'docstring': ast.get_docstring(node) or '',
            'type': 'class',
            'bases': [ast.unparse(base) for base in node.bases],
            'content': ast.unparse(node),
            'filepath': file_path,
            'parent_path': self._get_current_path(),
            'order': self._order_counter
        }
        
        results_data.append({
            'type': 'class',
            'name': node.name,
            'content': class_info['content'],
            'props': str({'bases': class_info['bases']}),
            'filepath': file_path,
            'parent_path': self._get_current_path(),
            'order': self._order_counter
        })
        
        # Process class methods and nested classes
        for child in ast.iter_child_nodes(node):
            if isinstance(child, (ast.FunctionDef, ast.ClassDef)):
                self._process_node(child, result, results_data, file_path)
        
        result.classes.append(class_info)
        
        # Remove class name from current path
        self._current_path.pop()

    def _process_import(self, node: ast.AST, results_data: List[Dict], file_path: str) -> None:
        """Process an import statement."""
        self._order_counter += 1  # Increment counter
        
        if isinstance(node, ast.Import):
            for name in node.names:
                results_data.append({
                    'type': 'import',
                    'name': name.name,
                    'content': ast.unparse(node),
                    'props': str({'asname': name.asname}),
                    'filepath': file_path,
                    'parent_path': self._get_current_path(),
                    'order': self._order_counter
                })
        elif isinstance(node, ast.ImportFrom):
            module = node.module or ''
            for name in node.names:
                results_data.append({
                    'type': 'import_from',
                    'name': f"{module}.{name.name}",
                    'content': ast.unparse(node),
                    'props': str({'asname': name.asname, 'module': module}),
                    'filepath': file_path,
                    'parent_path': self._get_current_path(),
                    'order': self._order_counter
                })

    def _process_assignment(self, node: ast.Assign, results_data: List[Dict], file_path: str) -> None:
        """Process an assignment statement."""
        # Only process module-level or class-level assignments
        if len(self._current_path) <= 1:
            self._order_counter += 1  # Increment counter
            for target in node.targets:
                if isinstance(target, ast.Name):
                    results_data.append({
                        'type': 'declaration',
                        'name': target.id,
                        'content': ast.unparse(node),
                        'props': str({}),
                        'filepath': file_path,
                        'parent_path': self._get_current_path(),
                        'order': self._order_counter
                    })
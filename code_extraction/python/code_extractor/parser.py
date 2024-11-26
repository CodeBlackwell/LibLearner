"""
Python code parser that extracts information about functions, classes, and other code structures.
"""

from dataclasses import dataclass
from pathlib import Path
from typing import List, Tuple, Optional
import astroid
import logging

logger = logging.getLogger(__name__)

@dataclass
class Function:
    """Represents a Python function."""
    name: str
    docstring: Optional[str]
    parameters: List[Tuple[str, str]]  # List of (name, type) tuples
    return_type: Optional[str]


@dataclass
class ParseResult:
    """Contains the results of parsing a Python file."""
    functions: List[Function]


class CodeParser:
    """Parser for Python source code that extracts code structure information."""
    
    def parse_file(self, file_path: Path) -> ParseResult:
        """
        Parse a Python file and extract information about its code structures.
        
        Args:
            file_path: Path to the Python file to parse
            
        Returns:
            ParseResult containing the extracted information
        """
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        module = astroid.parse(content)
        functions = []
        
        for node in module.body:
            if isinstance(node, astroid.FunctionDef):
                functions.append(self._parse_function(node))
        
        return ParseResult(functions=functions)
    
    def _parse_function(self, node: astroid.FunctionDef) -> Function:
        """Parse a function definition node."""
        # Get docstring
        docstring = None
        if (isinstance(node.doc_node, astroid.Const) and 
            isinstance(node.doc_node.value, str)):
            docstring = node.doc_node.value.strip()
        
        # Get parameters with type annotations
        parameters = []
        annotations = node.args.annotations
        for i, arg in enumerate(node.args.args):
            param_type = "Any"
            logger.debug(f"Processing argument {arg.name}")
            
            # Get type from annotations list
            if annotations[i]:
                param_type = annotations[i].as_string()
            
            logger.debug(f"Final param type: {param_type}")
            parameters.append((arg.name, param_type))
        
        # Get return type
        return_type = None
        if node.returns:
            return_type = node.returns.as_string()
        
        return Function(
            name=node.name,
            docstring=docstring,
            parameters=parameters,
            return_type=return_type
        )

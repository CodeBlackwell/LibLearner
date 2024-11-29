"""
Shell Script Processor for LibLearner.

This processor extracts structured information from shell scripts, including:
- Function definitions
- Variable declarations
- Aliases
- Source/Include statements
- Comments and documentation
"""

import re
import ast
import logging
from pathlib import Path
from typing import List, Dict, Optional, Set
import pandas as pd

from ..file_processor import FileProcessor
from ..processing_result import ShellProcessingResult

logger = logging.getLogger(__name__)

class ShellProcessor(FileProcessor):
    """Processor for shell script files."""
    
    def __init__(self, debug: bool = False):
        """Initialize the shell processor."""
        super().__init__()
        self.debug = debug
        if self.debug:
            logger.setLevel(logging.DEBUG)
            
        self.supported_types = {
            'text/x-shellscript',
            'application/x-shellscript',
            'text/x-sh',
            'application/x-sh'
        }
        
        # Initialize tracking variables
        self._all_results = []  # Store all results
        self._current_path = []  # Track path for nested functions
        self._order_counter = 0  # Track element order
        
        # Initialize regex patterns
        self._function_pattern = re.compile(r'^(?:function\s+)?(\w+)\s*\(\s*\)\s*{', re.MULTILINE)
        self._variable_pattern = re.compile(r'^([A-Za-z_][A-Za-z0-9_]*)\s*=\s*(.+)$', re.MULTILINE)
        self._alias_pattern = re.compile(r'^alias\s+([^=]+)=(.+)$', re.MULTILINE)
        self._source_pattern = re.compile(r'^(?:source|\.)\s+([^\s;]+)', re.MULTILINE)
        self._comment_pattern = re.compile(r'^#\s*(.+)$', re.MULTILINE)
        
    def get_supported_types(self) -> List[str]:
        """Return list of supported MIME types."""
        return list(self.supported_types)
        
    def process_file(self, file_path: str) -> ShellProcessingResult:
        """Process a shell script and extract structured information."""
        # Reset counters for new file
        self._order_counter = 0
        path = Path(file_path)
        result = ShellProcessingResult()
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
            # Process each element type
            self._process_functions(content, result, results_data, file_path)
            self._process_variables(content, result, results_data, file_path)
            self._process_aliases(content, result, results_data, file_path)
            self._process_sources(content, result, results_data, file_path)
        except Exception as e:
            error_msg = f"Error processing content: {str(e)}"
            result.errors.append(error_msg)
            logger.error(error_msg)
            
        # Create DataFrame from results
        if results_data:
            df = pd.DataFrame(results_data)
            df = df.rename(columns={'type': 'processor_type'})
            column_order = ['filepath', 'parent_path', 'order', 'name', 
                          'content', 'props', 'processor_type']
            self.results_df = df[column_order]
            
        return result
        
    def _process_functions(self, content: str, result: ShellProcessingResult, 
                         results_data: List[Dict], file_path: str) -> None:
        """Process shell function definitions."""
        for match in self._function_pattern.finditer(content):
            self._order_counter += 1
            func_name = match.group(1)
            
            # Find the function body
            start = match.start()
            body = self._extract_block(content[start:])
            
            # Get function documentation (comments above the function)
            doc = self._extract_doc_comment(content[:start])
            
            function_info = {
                'name': func_name,
                'type': 'function',
                'content': body,
                'props': str({'doc': doc}),
                'filepath': file_path,
                'parent_path': self._get_current_path(),
                'order': self._order_counter
            }
            
            result.functions.append(function_info)
            results_data.append(function_info)
            
    def _process_variables(self, content: str, result: ShellProcessingResult, 
                         results_data: List[Dict], file_path: str) -> None:
        """Process variable declarations."""
        for match in self._variable_pattern.finditer(content):
            self._order_counter += 1
            var_name = match.group(1)
            var_value = match.group(2).strip()
            
            variable_info = {
                'name': var_name,
                'type': 'variable',
                'content': f"{var_name}={var_value}",
                'props': str({'value': var_value}),
                'filepath': file_path,
                'parent_path': self._get_current_path(),
                'order': self._order_counter
            }
            
            result.variables.append(variable_info)
            results_data.append(variable_info)
            
    def _process_aliases(self, content: str, result: ShellProcessingResult, 
                        results_data: List[Dict], file_path: str) -> None:
        """Process alias definitions."""
        for match in self._alias_pattern.finditer(content):
            self._order_counter += 1
            alias_name = match.group(1).strip()
            alias_value = match.group(2).strip()
            
            alias_info = {
                'name': alias_name,
                'type': 'alias',
                'content': f"alias {alias_name}={alias_value}",
                'props': str({'value': alias_value}),
                'filepath': file_path,
                'parent_path': self._get_current_path(),
                'order': self._order_counter
            }
            
            result.aliases.append(alias_info)
            results_data.append(alias_info)
            
    def _process_sources(self, content: str, result: ShellProcessingResult, 
                        results_data: List[Dict], file_path: str) -> None:
        """Process source/include statements."""
        for match in self._source_pattern.finditer(content):
            self._order_counter += 1
            source_path = match.group(1)
            
            source_info = {
                'name': source_path,
                'type': 'source',
                'content': match.group(0),
                'props': str({}),
                'filepath': file_path,
                'parent_path': self._get_current_path(),
                'order': self._order_counter
            }
            
            result.sources.append(source_info)
            results_data.append(source_info)
            
    def _extract_block(self, content: str) -> str:
        """Extract a code block (between { and })."""
        level = 0
        in_quotes = False
        quote_char = None
        
        for i, char in enumerate(content):
            if char in '"\'':
                if not in_quotes:
                    in_quotes = True
                    quote_char = char
                elif quote_char == char:
                    in_quotes = False
            elif not in_quotes:
                if char == '{':
                    level += 1
                elif char == '}':
                    level -= 1
                    if level == 0:
                        return content[:i+1]
                        
        return content  # In case we don't find the end
        
    def _extract_doc_comment(self, content: str) -> str:
        """Extract documentation comments above an element."""
        lines = content.split('\n')
        doc_lines = []
        
        # Read lines in reverse until we find a non-comment line
        for line in reversed(lines):
            line = line.strip()
            if not line or line.startswith('#'):
                if line.startswith('#'):
                    doc_lines.insert(0, line[1:].strip())
            else:
                break
                
        return '\n'.join(doc_lines)
        
    def _get_current_path(self) -> str:
        """Get the current path in dot notation."""
        return '.'.join(self._current_path) if self._current_path else ''

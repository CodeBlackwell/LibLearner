"""
Improved YAML Processor for LibLearner.

This processor extracts structured information from YAML files, including:
- Document structure and hierarchy
- Configuration settings
- Environment variables
- Service definitions
- Dependencies and requirements
- API configurations
- Data types and schemas
"""

import re
import logging
import pandas as pd
from typing import List, Dict, Any, Set
from pathlib import Path
import yaml
from yaml.parser import ParserError
from yaml.scanner import ScannerError
from ..file_processor import FileProcessor

# Set up a logger for debug output
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class YAMLProcessingResult:
    """Result object for YAML processing."""

    def __init__(self):
        """Initialize the YAML processing result."""
        self.errors: List[str] = []
        self.documents: List[Dict] = []
        self.file_info: Dict[str, Any] = {}
        self.structure: List[Dict] = []
        self.env_vars: Set[str] = set()
        self.urls: Set[str] = set()
        self.types: Dict[str, str] = {}
        self.services: Set[str] = set()
        self.dependencies: Dict[str, str] = {}
        self.api_configs: Dict[str, Dict] = {}


class YAMLProcessor(FileProcessor):
    """Processor for YAML files."""
    
    def __init__(self, debug: bool = False):
        """Initialize the YAML processor."""
        super().__init__()
        self.debug = debug
        if self.debug:
            logger.setLevel(logging.DEBUG)
        self.supported_types = {'text/x-yaml', 'application/x-yaml', 'text/yaml'}
        self.env_var_pattern = re.compile(r'\$\{([^}]+)\}|\$([A-Za-z_][A-Za-z0-9_]*)')
        self.url_pattern = re.compile(r'https?://(?:[-\w.]|(?:%[\da-fA-F]{2}))+(?:[^\s.,;]*[^\s.,;:])?')

    def get_supported_types(self) -> List[str]:
        """Return list of supported MIME types."""
        return list(self.supported_types)

    def process_file(self, file_path: str) -> YAMLProcessingResult:
        """
        Process a YAML file and extract structured information.
        
        Args:
            file_path: Path to the YAML file
            
        Returns:
            YAMLProcessingResult object containing:
            - errors: List of any errors encountered
            - documents: List of parsed YAML documents
            - file_info: Basic file information
            - structure: Document structure analysis
            - env_vars: Set of environment variables found
            - urls: Set of URLs found
            - types: Dictionary of data types found
            - services: Set of service names found
            - dependencies: Dictionary of dependencies
            - api_configs: Dictionary of API configurations
        """
        path = Path(file_path)
        result = YAMLProcessingResult()
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
            logger.debug("Parsing YAML content")
            documents = list(yaml.safe_load_all(content))
            result.documents = documents
            logger.debug(f"Found {len(documents)} YAML documents")

            # Process each document 
            for doc in documents:
                if doc:  # Skip empty documents
                    logger.debug(f"Processing document: {doc}")
                    self._process_node('', doc, result, results_data)

        except (ParserError, ScannerError) as e:
            # Log parsing errors but continue processing
            error_msg = f"YAML parsing error: {str(e)}"
            result.errors.append(error_msg)
            logger.error(error_msg)

        # Update the results DataFrame
        self.results_df = pd.DataFrame(results_data)
        logger.debug(f"Final extracted URLs: {result.urls}")

        return result

    def _analyze_structure(self, data: Any) -> Dict:
        """Analyze the structure of a YAML node."""
        if isinstance(data, dict):
            return {
                'type': 'mapping',
                'keys': {k: self._analyze_structure(v) for k, v in data.items()}
            }
        elif isinstance(data, list):
            return {
                'type': 'sequence',
                'items': [self._analyze_structure(item) for item in data]
            }
        else:
            return {'type': type(data).__name__}

    def _extract_env_vars(self, data: Any) -> Set[str]:
        """Extract environment variables from YAML content."""
        env_vars = set()
        if isinstance(data, str):
            matches = self.env_var_pattern.findall(data)
            for match in matches:
                var_name = match[0] or match[1]
                # Keep the default value as part of the variable name
                env_vars.add(var_name)
        elif isinstance(data, dict):
            for value in data.values():
                env_vars.update(self._extract_env_vars(value))
        elif isinstance(data, list):
            for item in data:
                env_vars.update(self._extract_env_vars(item))
        return env_vars

    def _extract_urls(self, data: Any) -> Set[str]:
        """Extract URLs from YAML content."""
        urls = set()
        if isinstance(data, str):
            logger.debug(f"Checking string for URLs: {data}")
            matches = self.url_pattern.findall(data)
            logger.debug(f"Found URL matches: {matches}")
            urls.update(matches)
        elif isinstance(data, dict):
            logger.debug(f"Processing dictionary keys: {list(data.keys())}")
            for value in data.values():
                urls.update(self._extract_urls(value))
        elif isinstance(data, list):
            logger.debug("Processing list items")
            for item in data:
                urls.update(self._extract_urls(item))
        return urls

    def _analyze_types(self, data: Any, path: str = '') -> Dict[str, str]:
        """Analyze data types in YAML content."""
        types = {}
        if isinstance(data, dict):
            types[path] = 'mapping' if path else ''
            for key, value in data.items():
                new_path = f"{path}.{key}" if path else key
                types.update(self._analyze_types(value, new_path))
        elif isinstance(data, list):
            types[path] = 'sequence'
            for i, item in enumerate(data):
                new_path = f"{path}[{i}]"
                types.update(self._analyze_types(item, new_path))
        else:
            if path:
                type_name = 'null' if data is None else type(data).__name__
                types[path] = type_name
        return types

    def _infer_schemas(self, data: Any) -> Dict:
        """Infer JSON schemas from YAML content."""
        if isinstance(data, dict):
            properties = {}
            for key, value in data.items():
                properties[key] = self._infer_schemas(value)
                if key == 'config':
                    # Store the schema under the 'config' key
                    return {key: self._infer_schemas(value)}
            return {
                'type': 'object',
                'properties': properties
            }
        elif isinstance(data, list):
            if data:
                items = self._infer_schemas(data[0])
            else:
                items = {}
            return {
                'type': 'array',
                'items': items
            }
        else:
            return {
                'type': 'str' if isinstance(data, str) else
                       'int' if isinstance(data, int) else
                       'float' if isinstance(data, float) else
                       'bool' if isinstance(data, bool) else
                       'null' if data is None else
                       type(data).__name__
            }

    def to_csv(self, data: Any, sep: str = '.') -> List[Dict]:
        """Convert YAML data to CSV format."""
        if isinstance(data, list):
            # For lists, each item becomes a row
            rows = []
            for item in data:
                row = {}
                self._flatten_data(item, row, '', sep)
                if row:
                    rows.append(row)
            return rows
        else:
            # For dictionaries, create a single row
            row = {}
            self._flatten_data(data, row, '', sep)
            return [row] if row else []

    def _flatten_data(self, data: Any, current_row: Dict, prefix: str, sep: str = '.') -> None:
        """Helper method to flatten nested data for CSV conversion."""
        if isinstance(data, dict):
            for key, value in data.items():
                new_prefix = f"{prefix}{sep}{key}" if prefix else key
                if isinstance(value, (dict, list)):
                    self._flatten_data(value, current_row, new_prefix, sep)
                else:
                    current_row[new_prefix] = str(value) if value is not None else ''
        elif isinstance(data, list):
            for i, item in enumerate(data):
                new_prefix = f"{prefix}[{i}]" if prefix else str(i)
                if isinstance(item, (dict, list)):
                    self._flatten_data(item, current_row, new_prefix, sep)
                else:
                    current_row[new_prefix] = str(item) if item is not None else ''
        elif prefix:  # Only add value if we have a prefix
            current_row[prefix] = str(data) if data is not None else ''

    def _process_node(self, path: str, node: Any, result: YAMLProcessingResult, results_data: List[Dict]) -> None:
        """Process a YAML node and extract information."""
        if isinstance(node, dict):
            self._process_dict(path, node, result, results_data)
            for key, value in node.items():
                new_path = f"{path}.{key}" if path else key
                self._process_node(new_path, value, result, results_data)
        elif isinstance(node, list):
            for i, item in enumerate(node):
                new_path = f"{path}[{i}]" if path else str(i)
                self._process_node(new_path, item, result, results_data)
        else:
            # Extract URLs and env vars from string values
            if isinstance(node, str):
                urls = self._extract_urls(node)
                result.urls.update(urls)
                env_vars = self._extract_env_vars(node)
                result.env_vars.update(env_vars)
            
            # Store type information for all values
            if path:
                # Special handling for None/null values
                if node is None:
                    type_name = 'null'
                else:
                    type_name = type(node).__name__
                result.types[path] = type_name
                results_data.append({
                    'type': 'scalar',
                    'name': path,
                    'content': str(node),
                    'props': str({'value_type': type_name})
                })

    def _process_dict(self, path: str, node: Dict, result: YAMLProcessingResult, results_data: List[Dict]) -> None:
        """Process a dictionary node."""
        # Add to structure
        result.structure.append({
            'type': 'mapping',  # Keep old type name for backward compatibility
            'name': path if path else 'root',
            'children': list(node.keys())
        })

        # Store dictionary info
        results_data.append({
            'type': 'dict',
            'name': path if path else 'root',
            'content': str(node),
            'props': str({'num_keys': len(node)})
        })

        # Extract API configurations
        if path == 'api' or path.endswith('.api'):
            result.api_configs.update(node)

        # Check for special keys
        if 'services' in node:
            result.services.update(node['services'].keys())
        if 'dependencies' in node:
            result.dependencies.update(node['dependencies'])

        # Process children
        for key, value in node.items():
            new_path = f"{path}.{key}" if path else key
            self._process_node(new_path, value, result, results_data)

    def _process_list(self, path: str, node: List, result: YAMLProcessingResult, results_data: List[Dict]) -> None:
        """Process a list node."""
        # Add to structure
        result.structure.append({
            'type': 'sequence',
            'path': path,
            'length': len(node)
        })

        # Add to results DataFrame
        results_data.append({
            'type': 'sequence',
            'name': path,
            'content': str(len(node)),
            'props': str({'length': len(node)})
        })

        # Process items
        for i, item in enumerate(node):
            new_path = f"{path}[{i}]" if path else str(i)
            self._process_node(new_path, item, result, results_data)

    def _process_string(self, path: str, node: str, result: YAMLProcessingResult, results_data: List[Dict]) -> None:
        """Process a string node."""
        # Look for environment variables
        env_vars = self.env_var_pattern.findall(node)
        if env_vars:
            result.env_vars.update(var[0] or var[1] for var in env_vars)

        # Look for URLs
        urls = self.url_pattern.findall(node)
        if urls:
            result.urls.update(url[0] for url in urls)

        # Store type information
        if path:
            result.types[path] = 'str'
            results_data.append({
                'type': 'string',
                'name': path,
                'content': node,
                'props': str({'length': len(node)})
            })

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
from typing import List, Dict, Any
from pathlib import Path
import yaml
from yaml.parser import ParserError
from yaml.scanner import ScannerError

# Set up a logger for debug output
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class YAMLProcessingResult:
    """Class to represent the structured results from processing a YAML file."""
    def __init__(self):
        self.documents: List[Any] = []
        self.structure: List[Dict] = []
        self.env_vars: List[str] = []
        self.urls: List[str] = []
        self.types: Dict[str, str] = {}
        self.schemas: Dict[str, Dict] = {}
        self.services: Dict[str, Any] = {}
        self.dependencies: Dict[str, Any] = {}
        self.api_configs: Dict[str, Any] = {}
        self.file_info: Dict[str, Any] = {}
        self.errors: List[str] = []

    def add_error(self, message: str):
        logger.error(message)
        self.errors.append(message)


class YAMLProcessor:
    def __init__(self, debug: bool = False):
        self.debug = debug
        if self.debug:
            logger.setLevel(logging.DEBUG)
        self.env_var_pattern = re.compile(r'\$\{([^}]+)\}|\$([A-Za-z0-9_]+)')
        self.url_pattern = re.compile(
            r'https?:\/\/(www\.)?[-a-zA-Z0-9@:%._\+~#=]{1,256}\.[a-zA-Z0-9()]{1,6}\b([-a-zA-Z0-9()@:%_\+.~#?&//=]*)'
        )

    def process_file(self, file_path: str) -> YAMLProcessingResult:
        """
        Process a YAML file and extract structured information.
        
        Args:
            file_path: Path to the YAML file
            
        Returns:
            YAMLProcessingResult: Contains all extracted information.
        """
        result = YAMLProcessingResult()

        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
                logger.debug(f"Successfully read file: {file_path}")
        except Exception as e:
            result.add_error(f"Error reading file {file_path}: {str(e)}")
            return result

        # Add file metadata before attempting to parse
        path = Path(file_path)
        result.file_info = {
            'name': path.name,
            'path': str(path.absolute()),
            'size': path.stat().st_size,
            'last_modified': path.stat().st_mtime
        }
        logger.debug(f"File metadata added: {result.file_info}")

        try:
            # Parse all YAML documents in the file
            docs = list(yaml.safe_load_all(content))
            result.documents = docs
            logger.debug(f"Parsed {len(docs)} documents from the YAML file.")
        except (ParserError, ScannerError) as e:
            result.add_error(f"YAML parsing error: {str(e)}")
            return result

        # Process each document
        for idx, doc in enumerate(docs):
            if doc is not None:  # Skip empty documents
                logger.debug(f"Processing document {idx + 1}.")
                self._process_document(doc, result)

        return result

    def _process_document(self, doc: Any, result: YAMLProcessingResult) -> None:
        """Process a single YAML document and update the result."""
        # Structure Analysis
        structure = self._analyze_structure(doc)
        result.structure.append(structure)
        logger.debug(f"Document structure: {structure}")

        # Environment Variables Extraction
        env_vars = self._extract_env_vars(doc)
        result.env_vars.extend(env_vars)
        logger.debug(f"Extracted environment variables: {env_vars}")

        # URLs Extraction
        urls = self._extract_urls(doc)
        result.urls.extend(urls)
        logger.debug(f"Extracted URLs: {urls}")

        # Type Analysis
        types = self._analyze_types(doc)
        result.types.update(types)
        logger.debug(f"Analyzed data types: {types}")

        # Schema Inference
        schemas = self._infer_schemas(doc)
        result.schemas.update(schemas)
        logger.debug(f"Inferred schemas: {schemas}")

        # Configuration Extraction
        self._extract_configs(doc, result)

    def _analyze_structure(self, data: Any, path: str = '') -> Dict:
        """Analyze the hierarchical structure of YAML data."""
        if isinstance(data, dict):
            return {
                'type': 'mapping',
                'keys': {
                    k: self._analyze_structure(v, f"{path}.{k}" if path else k)
                    for k, v in data.items()
                }
            }
        elif isinstance(data, list):
            return {
                'type': 'sequence',
                'length': len(data),
                'items': [
                    self._analyze_structure(item, f"{path}[{i}]")
                    for i, item in enumerate(data)
                ] if len(data) > 0 else []
            }
        else:
            return {
                'type': type(data).__name__ if data is not None else 'null',
                'value_preview': str(data)[:100] if data is not None else None
            }

    def _extract_env_vars(self, data: Any) -> List[str]:
        """Extract environment variable references from YAML content."""
        env_vars = set()

        def extract_from_value(value: Any) -> None:
            if isinstance(value, str):
                for match in self.env_var_pattern.finditer(value):
                    env_var = match.group(1) or match.group(2)
                    if env_var:
                        # Remove default value if present (e.g., PORT:-80 -> PORT)
                        env_var = env_var.split(':-')[0] if ':-' in env_var else env_var
                        env_vars.add(env_var)
                        logger.debug(f"Found environment variable: {env_var}")
            elif isinstance(value, (dict, list)):
                for item in (value.values() if isinstance(value, dict) else value):
                    extract_from_value(item)

        extract_from_value(data)
        return list(env_vars)

    def _extract_urls(self, data: Any) -> List[str]:
        """Extract URLs from YAML content."""
        urls = set()

        def extract_from_value(value: Any) -> None:
            if isinstance(value, str):
                for match in self.url_pattern.finditer(value):
                    urls.add(match.group(0))
                    logger.debug(f"Found URL: {match.group(0)}")
            elif isinstance(value, (dict, list)):
                for item in (value.values() if isinstance(value, dict) else value):
                    extract_from_value(item)

        extract_from_value(data)
        return list(urls)

    def _analyze_types(self, data: Any, path: str = '') -> Dict[str, str]:
        """Analyze and record the types of values in the YAML content."""
        types = {}

        def record_type(value: Any, current_path: str) -> None:
            if isinstance(value, dict):
                types[current_path] = 'mapping'
                for k, v in value.items():
                    record_type(v, f"{current_path}.{k}" if current_path else k)
            elif isinstance(value, list):
                types[current_path] = 'sequence'
                if value:
                    record_type(value[0], f"{current_path}[]")
            else:
                types[current_path] = type(value).__name__ if value is not None else 'null'
                logger.debug(f"Recorded type for path '{current_path}': {types[current_path]}")

        record_type(data, path)
        return types

    def _infer_schemas(self, data: Any) -> Dict[str, Dict]:
        """Infer schemas from YAML content."""
        schemas = {}

        def infer_schema(value: Any, path: str = '') -> Dict:
            if isinstance(value, dict):
                return {
                    'type': 'object',
                    'properties': {
                        k: infer_schema(v, f"{path}.{k}")
                        for k, v in value.items()
                    }
                }
            elif isinstance(value, list):
                if value:
                    item_schema = infer_schema(value[0], f"{path}[]")
                    return {
                        'type': 'array',
                        'items': item_schema
                    }
                return {'type': 'array', 'items': {}}
            else:
                return {'type': type(value).__name__ if value is not None else 'null'}

        if isinstance(data, dict):
            for key, value in data.items():
                schemas[key] = infer_schema(value)
                logger.debug(f"Inferred schema for key '{key}': {schemas[key]}")

        return schemas

    def _extract_configs(self, data: Any, result: YAMLProcessingResult) -> None:
        """Extract specific configuration patterns from YAML content."""
        # Extract service configurations
        if isinstance(data, dict):
            if any(key in data for key in ['services', 'containers', 'pods']):
                service_configs = self._extract_service_configs(data)
                result.services.update(service_configs)
                logger.debug(f"Extracted service configurations: {service_configs}")

            if any(key in data for key in ['dependencies', 'requires', 'packages']):
                dependencies = self._extract_dependencies(data)
                result.dependencies.update(dependencies)
                logger.debug(f"Extracted dependencies: {dependencies}")

            if any(key in data for key in ['api', 'endpoints', 'routes']):
                api_configs = self._extract_api_configs(data)
                result.api_configs.update(api_configs)
                logger.debug(f"Extracted API configurations: {api_configs}")

    def _extract_service_configs(self, data: Any) -> Dict[str, Any]:
        """Extract service configurations from YAML content."""
        services = {}
        if isinstance(data, dict) and 'services' in data:
            services = data['services']
        elif isinstance(data, dict) and 'containers' in data:
            services = data['containers']
        elif isinstance(data, dict) and 'pods' in data:
            services = data['pods']
        return services

    def _extract_dependencies(self, data: Any) -> Dict[str, Any]:
        """Extract dependencies from YAML content."""
        deps = {}
        for key in ['dependencies', 'requires', 'packages']:
            if key in data and isinstance(data[key], dict):
                deps.update(data[key])
        return deps

    def _extract_api_configs(self, data: Any) -> Dict[str, Any]:
        """Extract API configurations from YAML content."""
        api_configs = {}
        if isinstance(data, dict) and 'api' in data:
            api_configs = data['api']
        elif isinstance(data, dict) and 'endpoints' in data:
            api_configs['endpoints'] = data['endpoints']
        elif isinstance(data, dict) and 'routes' in data:
            api_configs['routes'] = data['routes']
        return api_configs

    def get_supported_extensions(self) -> List[str]:
        """Return list of supported file extensions."""
        return ['.yml', '.yaml']

    def to_csv(self, data: Any, parent_key: str = '', sep: str = '.') -> List[Dict[str, str]]:
        """
        Convert YAML data to a flattened CSV-compatible format.
        
        Args:
            data: The YAML data to convert
            parent_key: The parent key for nested items (used recursively)
            sep: Separator to use between nested keys
            
        Returns:
            List of dictionaries where each dictionary represents a row in the CSV
        """
        rows = []
        
        def flatten_dict(d: Dict, parent: str = '') -> Dict[str, str]:
            items = {}
            for k, v in d.items():
                new_key = f"{parent}{sep}{k}" if parent else k
                if isinstance(v, dict):
                    items.update(flatten_dict(v, new_key))
                elif isinstance(v, list):
                    for i, item in enumerate(v):
                        list_key = f"{new_key}[{i}]"
                        if isinstance(item, dict):
                            items.update(flatten_dict(item, list_key))
                        else:
                            items[list_key] = str(item)
                else:
                    items[new_key] = str(v) if v is not None else ''
            return items

        if isinstance(data, dict):
            rows.append(flatten_dict(data, parent_key))
        elif isinstance(data, list):
            for item in data:
                if isinstance(item, dict):
                    rows.append(flatten_dict(item, parent_key))
                else:
                    rows.append({parent_key if parent_key else 'value': str(item)})
        else:
            rows.append({parent_key if parent_key else 'value': str(data) if data is not None else ''})

        return rows

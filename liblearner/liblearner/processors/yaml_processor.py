"""
YAML Processor for LibLearner.

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
from typing import Dict, List, Any, Tuple, Optional, Union
from pathlib import Path
import yaml
from yaml.parser import ParserError
from yaml.scanner import ScannerError

class YAMLProcessor:
    def __init__(self):
        self.env_var_pattern = re.compile(r'\$\{([^}]+)\}|\$([A-Za-z0-9_]+)')
        self.url_pattern = re.compile(
            r'https?:\/\/(www\.)?[-a-zA-Z0-9@:%._\+~#=]{1,256}\.[a-zA-Z0-9()]{1,6}\b([-a-zA-Z0-9()@:%_\+.~#?&//=]*)'
        )

    def process_file(self, file_path: str) -> Dict:
        """
        Process a YAML file and extract structured information.
        
        Args:
            file_path: Path to the YAML file
            
        Returns:
            Dictionary containing extracted information:
            {
                'documents': List of parsed YAML documents,
                'structure': Hierarchical structure information,
                'env_vars': List of environment variables,
                'urls': List of URLs found,
                'types': Data type information,
                'schemas': Inferred schemas,
                'services': Service configurations (if any),
                'dependencies': Dependencies (if found),
                'api_configs': API configurations (if any),
                'file_info': File metadata
            }
        """
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
        except Exception as e:
            raise RuntimeError(f"Error reading file {file_path}: {str(e)}")

        # Initialize result structure
        result = {
            'documents': [],
            'structure': [],
            'env_vars': [],
            'urls': [],
            'types': {},
            'schemas': {},
            'services': {},
            'dependencies': {},
            'api_configs': {},
            'errors': []
        }

        try:
            # Parse all YAML documents in the file
            docs = list(yaml.safe_load_all(content))
            result['documents'] = docs

            # Process each document
            for doc in docs:
                if doc is not None:  # Skip empty documents
                    self._process_document(doc, result)

        except (ParserError, ScannerError) as e:
            result['errors'].append(f"YAML parsing error: {str(e)}")
        except Exception as e:
            result['errors'].append(f"Processing error: {str(e)}")

        # Add file metadata
        path = Path(file_path)
        result['file_info'] = {
            'name': path.name,
            'path': str(path.absolute()),
            'size': path.stat().st_size,
            'last_modified': path.stat().st_mtime
        }

        return result

    def _process_document(self, doc: Any, result: Dict) -> None:
        """Process a single YAML document and update the result dictionary."""
        # Analyze structure
        structure = self._analyze_structure(doc)
        result['structure'].append(structure)

        # Extract environment variables
        env_vars = self._extract_env_vars(doc)
        result['env_vars'].extend(env_vars)

        # Extract URLs
        urls = self._extract_urls(doc)
        result['urls'].extend(urls)

        # Analyze types
        types = self._analyze_types(doc)
        result['types'].update(types)

        # Infer schemas
        schemas = self._infer_schemas(doc)
        result['schemas'].update(schemas)

        # Extract specific configurations
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
                        env_vars.add(env_var)
            elif isinstance(value, dict):
                for v in value.values():
                    extract_from_value(v)
            elif isinstance(value, list):
                for item in value:
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
            elif isinstance(value, dict):
                for v in value.values():
                    extract_from_value(v)
            elif isinstance(value, list):
                for item in value:
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
                    new_path = f"{current_path}.{k}" if current_path else k
                    record_type(v, new_path)
            elif isinstance(value, list):
                types[current_path] = 'sequence'
                if value:  # Only analyze first item for sequence type
                    record_type(value[0], f"{current_path}[]")
            else:
                types[current_path] = type(value).__name__ if value is not None else 'null'

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
                if isinstance(value, (dict, list)):
                    schemas[key] = infer_schema(value)

        return schemas

    def _extract_configs(self, data: Any, result: Dict) -> None:
        """Extract specific configuration patterns from YAML content."""
        # Extract service configurations
        if isinstance(data, dict):
            # Look for service definitions
            if any(key in data for key in ['services', 'containers', 'pods']):
                result['services'].update(self._extract_service_configs(data))

            # Look for dependencies
            if any(key in data for key in ['dependencies', 'requires', 'packages']):
                result['dependencies'].update(self._extract_dependencies(data))

            # Look for API configurations
            if any(key in data for key in ['api', 'endpoints', 'routes']):
                result['api_configs'].update(self._extract_api_configs(data))

    def _extract_service_configs(self, data: Dict) -> Dict:
        """Extract service configurations from YAML content."""
        services = {}
        service_keys = ['services', 'containers', 'pods']
        
        for key in service_keys:
            if key in data and isinstance(data[key], dict):
                services[key] = {
                    service_name: {
                        'type': 'service',
                        'config': config
                    }
                    for service_name, config in data[key].items()
                }
        
        return services

    def _extract_dependencies(self, data: Dict) -> Dict:
        """Extract dependency information from YAML content."""
        deps = {}
        dep_keys = ['dependencies', 'requires', 'packages']
        
        for key in dep_keys:
            if key in data:
                if isinstance(data[key], dict):
                    deps[key] = data[key]
                elif isinstance(data[key], list):
                    deps[key] = {str(i): dep for i, dep in enumerate(data[key])}
        
        return deps

    def _extract_api_configs(self, data: Dict) -> Dict:
        """Extract API configurations from YAML content."""
        apis = {}
        api_keys = ['api', 'endpoints', 'routes']
        
        for key in api_keys:
            if key in data and isinstance(data[key], (dict, list)):
                apis[key] = data[key]
        
        return apis

    def get_supported_extensions(self) -> List[str]:
        """Return list of supported file extensions."""
        return ['yaml', 'yml']

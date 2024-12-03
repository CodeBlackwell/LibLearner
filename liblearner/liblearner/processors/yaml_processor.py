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
import os
import logging
import pandas as pd
from typing import List, Dict, Any, Set
from pathlib import Path
import yaml
from yaml.parser import ParserError
from yaml.scanner import ScannerError

from ..file_processor import FileProcessor
from ..processing_result import YAMLProcessingResult

# Set up logging with a higher default level
logger = logging.getLogger(__name__)
logger.setLevel(logging.WARNING)  # Default to WARNING level

class YAMLProcessor(FileProcessor):
    """Processor for YAML files."""
    
    def __init__(self, debug: bool = False):
        """Initialize the YAML processor."""
        super().__init__()
        self.debug = debug
        if self.debug:
            logger.setLevel(logging.DEBUG)
        else:
            logger.setLevel(logging.WARNING)
            
        # Initialize results DataFrame
        self.results_df = pd.DataFrame()
            
        # Define supported MIME types
        self.supported_types = {
            'text/x-yaml',
            'application/x-yaml',
            'text/yaml',
            'application/yaml'
        }
        
        # Initialize patterns
        self.env_var_pattern = re.compile(r'\$\{([^}]+)\}|\$([A-Za-z_][A-Za-z0-9_]*)')
        self.url_pattern = re.compile(r'https?://(?:[-\w.]|(?:%[\da-fA-F]{2}))+(?:[^\s.,;]*[^\s.,;:])?')
        
        # Initialize tracking variables
        self._order_counter = 0
        self._current_path = []

    def get_supported_types(self) -> List[str]:
        """Return list of supported MIME types."""
        return list(self.supported_types)

    def process_file(self, file_path: str) -> YAMLProcessingResult:
        """Process a YAML file and extract structured information."""
        # Reset counters for new file
        self._order_counter = 0
        self._current_path = []
        
        if self.debug:
            logger.info(f"Starting to process YAML file: {file_path}")
        
        path = Path(file_path)
        result = YAMLProcessingResult()
        results_data = []

        # Validate file exists
        if not path.exists():
            error_msg = f"Error reading file: File not found - {file_path}"
            result.errors.append(error_msg)
            logger.error(error_msg)
            return result

        try:
            # Add file metadata
            result.file_info = {
                'name': path.name,
                'path': str(path.absolute()),
                'size': path.stat().st_size,
                'last_modified': path.stat().st_mtime
            }
        except Exception as e:
            error_msg = f"Error getting file info: {str(e)}"
            result.errors.append(error_msg)
            logger.error(error_msg)
            return result

        try:
            content = path.read_text()
            if self.debug:
                logger.debug(f"Read file content, size: {len(content)} bytes")
            
            # Parse YAML content
            documents = list(yaml.safe_load_all(content))
            if self.debug:
                logger.info(f"Found {len(documents)} YAML documents")
            
            # Process each document
            for doc_idx, doc in enumerate(documents):
                if doc:  # Skip empty documents
                    if self.debug:
                        logger.debug(f"Processing document {doc_idx}")
                    self._process_document(doc, doc_idx, result, results_data, file_path)
            
        except (ParserError, ScannerError) as e:
            error_msg = f"YAML parsing error: {str(e)}"
            result.errors.append(error_msg)
            logger.error(error_msg)
            return result
        except Exception as e:
            error_msg = f"Error processing YAML: {str(e)}"
            result.errors.append(error_msg)
            logger.error(error_msg)
            return result

        # Create DataFrame from results
        if results_data:
            try:
                df = pd.DataFrame(results_data)
                df = df.rename(columns={'type': 'processor_type'})
                column_order = ['filepath', 'parent_path', 'order', 'name', 
                              'content', 'props', 'processor_type']
                df = df[column_order]
                
                # Concatenate with existing results
                if not self.results_df.empty:
                    self.results_df = pd.concat([self.results_df, df], ignore_index=True)
                else:
                    self.results_df = df
            except Exception as e:
                error_msg = f"Error creating DataFrame: {str(e)}"
                result.errors.append(error_msg)
                logger.error(error_msg)

        return result
        
    def _process_document(self, doc: Dict, doc_idx: int, result: YAMLProcessingResult,
                         results_data: List[Dict], file_path: str) -> None:
        """Process a single YAML document."""
        self._order_counter += 1
        
        # Store document in result
        result.data[f'doc_{doc_idx}'] = doc
        
        # Create document info
        doc_name = f"document_{doc_idx}"
        doc_props = {
            'env_vars': list(self._extract_env_vars(doc)),
            'urls': list(self._extract_urls(doc)),
            'structure': self._analyze_structure(doc)
        }
        
        # Create document entry
        doc_info = {
            'name': doc_name,
            'type': 'document',
            'content': yaml.dump(doc),
            'props': str(doc_props),
            'filepath': file_path,
            'parent_path': '',  # Documents are top-level
            'order': self._order_counter
        }
        results_data.append(doc_info)
        
        # Process document contents
        if isinstance(doc, dict):
            self._process_mapping(doc, doc_name, results_data, file_path)
        elif isinstance(doc, list):
            self._process_sequence(doc, doc_name, results_data, file_path)
            
    def _process_mapping(self, data: Dict, parent_path: str,
                        results_data: List[Dict], file_path: str) -> None:
        """Process a YAML mapping node."""
        for key, value in data.items():
            self._order_counter += 1
            current_path = f"{parent_path}.{key}" if parent_path else key
            
            # Create mapping entry
            props = {
                'key': key,
                'value_type': type(value).__name__,
                'env_vars': list(self._extract_env_vars(value)),
                'urls': list(self._extract_urls(value))
            }
            
            mapping_info = {
                'name': key,
                'type': 'mapping',
                'content': yaml.dump({key: value}),
                'props': str(props),
                'filepath': file_path,
                'parent_path': parent_path,
                'order': self._order_counter
            }
            results_data.append(mapping_info)
            
            # Process nested structures
            if isinstance(value, dict):
                self._process_mapping(value, current_path, results_data, file_path)
            elif isinstance(value, list):
                self._process_sequence(value, current_path, results_data, file_path)
                
    def _process_sequence(self, data: List, parent_path: str,
                         results_data: List[Dict], file_path: str) -> None:
        """Process a YAML sequence node."""
        for idx, item in enumerate(data):
            self._order_counter += 1
            current_path = f"{parent_path}[{idx}]"
            
            # Create sequence entry
            props = {
                'index': idx,
                'value_type': type(item).__name__,
                'env_vars': list(self._extract_env_vars(item)),
                'urls': list(self._extract_urls(item))
            }
            
            sequence_info = {
                'name': f"item_{idx}",
                'type': 'sequence',
                'content': yaml.dump([item]),
                'props': str(props),
                'filepath': file_path,
                'parent_path': parent_path,
                'order': self._order_counter
            }
            results_data.append(sequence_info)
            
            # Process nested structures
            if isinstance(item, dict):
                self._process_mapping(item, current_path, results_data, file_path)
            elif isinstance(item, list):
                self._process_sequence(item, current_path, results_data, file_path)
                
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
                # Extract just the variable name before any default value
                var_name = var_name.split(':-')[0] if ':-' in var_name else var_name
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
            matches = self.url_pattern.findall(data)
            urls.update(matches)
        elif isinstance(data, dict):
            for value in data.values():
                urls.update(self._extract_urls(value))
        elif isinstance(data, list):
            for item in data:
                urls.update(self._extract_urls(item))
        return urls

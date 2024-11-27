"""
Improved MDX Processor for LibLearner.

This processor extracts structured information from MDX files, including:
- Frontmatter metadata
- Import and Export declarations
- JSX Components
- File metadata
"""

import os
import re
import yaml
import logging
from typing import Dict, List, Any, Optional
from pathlib import Path
import csv
from datetime import date, datetime
import pandas as pd

from ..file_processor import FileProcessor

# Set up a logger for debug output
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class MDXProcessor(FileProcessor):
    """Process MDX files and extract structured information."""
    
    def __init__(self, debug: bool = False):
        """Initialize the MDX processor."""
        super().__init__()
        self.debug = debug
        if self.debug:
            logger.setLevel(logging.DEBUG)
        self.frontmatter_pattern = re.compile(r'^---\s*(.*?)\s*---', re.DOTALL)
        self.import_pattern = re.compile(r'import\s+(?:\{\s*([^}]+)\s*\}|\s*(\w+)(?:,\s*(\w+))?)\s+from\s+[\'"]([^\'"]+)[\'"]')
        self.export_pattern = re.compile(r'export\s+.*$', re.MULTILINE)
        self.component_pattern = re.compile(r'<([A-Z][a-zA-Z0-9]*)\s*([^>]*)>(?:(.*?)<\/\1>|[^<]*)', re.DOTALL)
        self.prop_pattern = re.compile(r'(\w+)=(?:{([^}]+)}|"([^"]+)")')

    def get_supported_types(self) -> List[str]:
        """Return list of supported MIME types."""
        return ['text/markdown']

    def process_file(self, file_path: str) -> Dict[str, Any]:
        """
        Process an MDX file and extract structured information.
        
        Args:
            file_path: Path to the MDX file
            
        Returns:
            Dictionary containing extracted information
        """
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()

            # Extract components
            components = []
            for match in self.component_pattern.finditer(content):
                component_name = match.group(1)
                props_str = match.group(2)
                content = match.group(3)
                props = self._extract_props(props_str) if props_str else {}
                components.append({
                    'name': component_name,
                    'props': props,
                    'content': content
                })

            # Extract imports
            imports = []
            for match in self.import_pattern.finditer(content):
                imports.append({
                    'items': match.group(1) or match.group(2),
                    'source': match.group(4)
                })

            # Extract frontmatter
            frontmatter = {}
            fm_match = self.frontmatter_pattern.match(content)
            if fm_match:
                try:
                    frontmatter = yaml.safe_load(fm_match.group(1))
                except yaml.YAMLError as e:
                    logger.error(f"Error parsing frontmatter in {file_path}: {str(e)}")

            # Create results DataFrame
            results_data = []
            
            # Add components to DataFrame
            for comp in components:
                results_data.append({
                    'type': 'component',
                    'name': comp['name'],
                    'content': comp.get('content', ''),
                    'props': str(comp.get('props', {})),
                    'file_path': file_path
                })
            
            # Add imports to DataFrame
            for imp in imports:
                results_data.append({
                    'type': 'import',
                    'name': imp['items'],
                    'content': imp['source'],
                    'props': '',
                    'file_path': file_path
                })
            
            # Add frontmatter to DataFrame
            for key, value in frontmatter.items():
                results_data.append({
                    'type': 'frontmatter',
                    'name': key,
                    'content': str(value),
                    'props': '',
                    'file_path': file_path
                })

            # Update the results DataFrame
            self.results_df = pd.DataFrame(results_data)

            return {
                'components': components,
                'imports': imports,
                'frontmatter': frontmatter,
                'file_info': {
                    'path': file_path,
                    'size': os.path.getsize(file_path),
                    'modified': datetime.fromtimestamp(os.path.getmtime(file_path))
                }
            }

        except Exception as e:
            logger.error(f"Error processing {file_path}: {str(e)}")
            return None

    def _extract_props(self, component_str: str) -> Dict[str, str]:
        """Extract properties from a component string."""
        props = {}
        for match in self.prop_pattern.finditer(component_str):
            name = match.group(1)
            value = match.group(2) or match.group(3)
            props[name] = value
        return props

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

# Set up a logger for debug output
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class MDXProcessingResult:
    """Class to represent the structured results from processing an MDX file."""
    def __init__(self):
        self.frontmatter: Dict[str, Any] = {}
        self.imports: List[str] = []
        self.exports: List[str] = []
        self.components: List[Dict[str, Any]] = []
        self.file_info: Dict[str, Any] = {}
        self.errors: List[str] = []

    def add_error(self, message: str):
        logger.error(message)
        self.errors.append(message)

    def to_csv(self, csv_path: str):
        """Write the MDX processing results to a CSV file."""
        try:
            with open(csv_path, 'w', newline='') as csvfile:
                writer = csv.writer(csvfile)
                writer.writerow(['Filename', 'Type', 'Name', 'Content', 'Props', 'Metadata'])
                
                # Write components
                for comp in self.components:
                    writer.writerow([
                        self.file_info.get('name', ''),
                        'component',
                        comp['name'],
                        comp.get('content', ''),
                        comp.get('props', ''),
                        ''
                    ])

                # Write imports
                for imp in self.imports:
                    source = imp[imp.find('from')+4:].strip().strip("'").strip('"') if 'from' in imp else ''
                    name = imp[imp.find('import')+6:imp.find('from')].strip() if 'from' in imp else imp[imp.find('import')+6:].strip()
                    writer.writerow([
                        self.file_info.get('name', ''),
                        'import',
                        name,
                        source,
                        '',
                        ''
                    ])

                # Write exports
                for exp in self.exports:
                    if 'export default' in exp:
                        name = 'default'
                        value = exp.replace('export default', '').strip()
                    else:
                        name = exp[exp.find('export')+6:].split('=')[0].strip()
                        value = exp[exp.find('=')+1:].strip() if '=' in exp else ''
                    writer.writerow([
                        self.file_info.get('name', ''),
                        'export',
                        name,
                        value,
                        '',
                        ''
                    ])

            logger.info(f"CSV successfully written to {csv_path}")
        except Exception as e:
            self.add_error(f"Error writing to CSV: {str(e)}")


class MDXProcessor:
    def __init__(self, debug: bool = False):
        self.debug = debug
        if self.debug:
            logger.setLevel(logging.DEBUG)
        self.frontmatter_pattern = re.compile(r'^---\s*(.*?)\s*---', re.DOTALL)
        self.import_pattern = re.compile(r'^import\s+.*?;?', re.MULTILINE)
        self.export_pattern = re.compile(r'^export\s+.*?;?', re.MULTILINE)
        self.component_pattern = re.compile(r'<([A-Z][a-zA-Z0-9]*)\s*([^>]*)>(.*?)<\/\1>', re.DOTALL)

    def process_file(self, file_path: str) -> MDXProcessingResult:
        """
        Process an MDX file and extract structured information.

        Args:
            file_path: Path to the MDX file

        Returns:
            MDXProcessingResult: Contains all extracted information.
        """
        result = MDXProcessingResult()

        # Read file content
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            logger.debug(f"Successfully read file: {file_path}")
        except Exception as e:
            result.add_error(f"Error reading file {file_path}: {str(e)}")
            return result

        # File metadata
        path = Path(file_path)
        result.file_info = {
            'name': path.name,
            'path': str(path.absolute()),
            'size': path.stat().st_size,
            'modified': path.stat().st_mtime
        }
        logger.debug(f"File metadata added: {result.file_info}")

        # Extract frontmatter
        frontmatter_match = self.frontmatter_pattern.search(content)
        if frontmatter_match:
            frontmatter_str = frontmatter_match.group(1)
            try:
                result.frontmatter = yaml.safe_load(frontmatter_str)
                logger.debug(f"Extracted frontmatter: {result.frontmatter}")
            except yaml.YAMLError as e:
                result.add_error(f"YAML parsing error in frontmatter: {str(e)}")

        # Extract imports
        result.imports = self.import_pattern.findall(content)
        logger.debug(f"Extracted imports: {result.imports}")

        # Extract exports
        result.exports = self.export_pattern.findall(content)
        logger.debug(f"Extracted exports: {result.exports}")

        # Extract components
        for match in self.component_pattern.finditer(content):
            component_name = match.group(1)
            component_props = match.group(2)
            component_content = match.group(3).strip()
            component_data = {
                'name': component_name,
                'props': component_props,
                'content': component_content
            }
            result.components.append(component_data)
            logger.debug(f"Extracted component: {component_data}")

        return result

    def _extract_props(self, component_str: str) -> Dict[str, str]:
        """Extract properties from a component string."""
        props = {}
        prop_pattern = re.compile(r'([a-zA-Z0-9_-]+)\s*=\s*["\'](.*?)["\']|([a-zA-Z0-9_-]+)\s*=\s*{(.*?)}')
        matches = prop_pattern.findall(component_str)
        for match in matches:
            key = match[0] if match[0] else match[2]
            value = match[1] if match[1] else match[3]
            props[key] = value
            logger.debug(f"Extracted prop '{key}': '{value}'")
        return props

    def get_supported_extensions(self) -> List[str]:
        """Return list of supported file extensions."""
        return ['mdx']

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

# Set up a logger for debug output
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class MDXProcessingResult:
    """Class to represent the structured results from processing an MDX file."""
    def __init__(self, frontmatter=None, imports=None, exports=None, components=None, file_info=None):
        self.frontmatter = frontmatter or {}
        self.imports = imports or []
        self.exports = exports or []
        self.components = components or []
        self.file_info = file_info or {}
        self.errors = []
        self.import_pattern = re.compile(r'import\s+(?:\{\s*([^}]+)\s*\}|\s*(\w+)(?:,\s*(\w+))?)\s+from\s+[\'"]([^\'"]+)[\'"]')

    def add_error(self, message: str):
        logger.error(message)
        self.errors.append(message)

    def to_csv(self, csv_path: str):
        """Write the processing results to a CSV file."""
        if not hasattr(self, 'file_info'):
            logger.error("No file info available. Process a file first.")
            return  
        try:
            with open(csv_path, 'w', newline='') as csvfile:
                writer = csv.writer(csvfile)
                writer.writerow(['Filename', 'Type', 'Name', 'Content', 'Props', 'Metadata'])

                # Write imports first
                for imp in self.imports:
                    match = self.import_pattern.search(imp)
                    if match:
                        # Handle named imports
                        if match.group(1):
                            components = [c.strip() for c in match.group(1).split(',')]
                            source = match.group(4)
                            for component in components:
                                writer.writerow([
                                    self.file_info.get('name', ''),
                                    'import',
                                    component,
                                    source,
                                    '',
                                    ''
                                ])
                        # Handle default imports
                        elif match.group(2):
                            writer.writerow([
                                self.file_info.get('name', ''),
                                'import',
                                match.group(2),
                                match.group(4),
                                '',
                                ''
                            ])

                # Write components
                for comp in self.components:
                    if not comp['name'].startswith('Default'):  # Skip DefaultLayout
                        writer.writerow([
                            self.file_info.get('name', ''),
                            'component',
                            comp['name'],
                            comp.get('content', ''),
                            ', '.join(f"{k}=\"{v}\"" for k, v in comp['props'].items()),
                            ''
                        ])

                # Write exports
                for exp in self.exports:
                    if 'export default' in exp:
                        name = 'default'
                        content = exp.replace('export default', '').strip()
                    else:
                        name = exp.split()[2] if len(exp.split()) > 2 else ''
                        content = exp
                    writer.writerow([
                        self.file_info.get('name', ''),
                        'export',
                        name,
                        content,
                        '',
                        ''
                    ])
            logger.info(f"CSV successfully written to {csv_path}")
        except Exception as e:
            logger.error(f"Error writing to CSV: {e}")


class MDXProcessor:
    def __init__(self, debug: bool = False):
        """Initialize the MDX processor."""
        self.debug = debug
        if self.debug:
            logger.setLevel(logging.DEBUG)
        self.frontmatter_pattern = re.compile(r'^---\s*(.*?)\s*---', re.DOTALL)
        self.import_pattern = re.compile(r'import\s+(?:\{\s*([^}]+)\s*\}|\s*(\w+)(?:,\s*(\w+))?)\s+from\s+[\'"]([^\'"]+)[\'"]')
        self.export_pattern = re.compile(r'export\s+.*$', re.MULTILINE)
        self.component_pattern = re.compile(r'<([A-Z][a-zA-Z0-9]*)\s*([^>]*)>(?:(.*?)<\/\1>|[^<]*)', re.DOTALL)
        self.prop_pattern = re.compile(r'(\w+)=(?:{([^}]+)}|"([^"]+)")')

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
                
                # Convert date to string format if it's a date object
                if isinstance(result.frontmatter.get('date'), date):
                    result.frontmatter['date'] = result.frontmatter['date'].strftime('%Y-%m-%d')
            except yaml.YAMLError as e:
                result.add_error(f"YAML parsing error in frontmatter: {str(e)}")

        # Extract imports
        result.imports = []
        for match in self.import_pattern.finditer(content):
            import_statement = content[match.start():match.end()]
            result.imports.append(import_statement)
        logger.debug(f"Extracted imports: {result.imports}")

        # Extract exports
        result.exports = []
        for match in self.export_pattern.finditer(content):
            export_statement = content[match.start():match.end()]
            result.exports.append(export_statement)
        logger.debug(f"Extracted exports: {result.exports}")

        # Extract components
        for match in self.component_pattern.finditer(content):
            component_name = match.group(1)
            if not component_name.startswith('Default'):  # Skip DefaultLayout
                component_props = match.group(2)
                component_content = match.group(3).strip() if match.group(3) else ''
                props = {}
                for prop_match in self.prop_pattern.finditer(component_props):
                    prop_name = prop_match.group(1)
                    prop_value = prop_match.group(2) or prop_match.group(3)
                    props[prop_name] = prop_value
                component_data = {
                    'name': component_name,
                    'props': props,
                    'content': component_content
                }
                result.components.append(component_data)
                logger.debug(f"Extracted component: {component_data}")

        return result

    def process(self, file_path):
        """Process an MDX file and extract its components."""
        try:
            with open(file_path, 'r') as f:
                content = f.read()
                logger.debug(f"Successfully read file: {file_path}")
                
                # Add file metadata
                file_info = Path(file_path)
                self.file_info = {
                    'name': file_info.name,
                    'path': str(file_info.absolute()),
                    'size': file_info.stat().st_size,
                    'modified': file_info.stat().st_mtime
                }
                logger.debug(f"File metadata added: {self.file_info}")

                # Extract frontmatter
                frontmatter_match = self.frontmatter_pattern.search(content)
                if frontmatter_match:
                    try:
                        self.frontmatter = yaml.safe_load(frontmatter_match.group(1))
                        # Convert date to string format if it exists
                        if 'date' in self.frontmatter and isinstance(self.frontmatter['date'], datetime.date):
                            self.frontmatter['date'] = self.frontmatter['date'].strftime('%Y-%m-%d')
                        logger.debug(f"Extracted frontmatter: {self.frontmatter}")
                    except yaml.YAMLError as e:
                        logger.error(f"YAML parsing error in frontmatter: {e}")
                        self.frontmatter = {}

                # Extract imports
                self.imports = []
                for match in self.import_pattern.finditer(content):
                    import_statement = content[match.start():match.end()]
                    self.imports.append(import_statement)
                logger.debug(f"Extracted imports: {self.imports}")

                # Extract exports
                self.exports = []
                for match in self.export_pattern.finditer(content):
                    export_statement = content[match.start():match.end()]
                    self.exports.append(export_statement)
                logger.debug(f"Extracted exports: {self.exports}")

                # Extract components
                self.components = []
                for match in self.component_pattern.finditer(content):
                    component = {
                        'name': match.group(1),
                        'props': self._extract_props(match.group(2) or ''),
                        'content': match.group(3) or ''
                    }
                    if not component['name'].startswith('Default'):  # Skip DefaultLayout
                        self.components.append(component)
                        logger.debug(f"Extracted component: {component}")

                return MDXProcessingResult(
                    frontmatter=self.frontmatter,
                    imports=self.imports,
                    exports=self.exports,
                    components=self.components,
                    file_info=self.file_info
                )

        except Exception as e:
            logger.error(f"Error reading file {file_path}: {e}")
            return None

    def get_supported_extensions(self) -> List[str]:
        """Return list of supported file extensions."""
        return ['mdx']

"""MDX Processor for LibLearner.

This processor extracts information from MDX files, including:
- JSX components and their props
- Markdown content
- Exports and imports
- Frontmatter
- Layouts and themes
- Remark/Rehype plugins
"""

import re
import yaml
from datetime import date, datetime
from typing import Dict, List, Optional, Any, Union
from pathlib import Path

class MDXProcessor:
    """Processor for MDX files."""

    def __init__(self):
        """Initialize the MDX processor."""
        self.jsx_component_pattern = re.compile(r'<([A-Z][A-Za-z0-9]*)[^>]*>')
        self.export_pattern = re.compile(r'export\s+(?:default|(?:const|let|var|function|class)\s+([A-Za-z0-9_$]+))')
        self.import_pattern = re.compile(r'import\s+(?:{[^}]+}|\*\s+as\s+[^;]+|[^;]+)\s+from\s+[\'"]([^\'"]+)[\'"]')
        self.frontmatter_pattern = re.compile(r'^---\s*\n(.*?)\n---\s*\n', re.DOTALL)
        self.layout_pattern = re.compile(r'(layout|Layout):\s*[\'"]([^\'"]+)[\'"]')

    def get_supported_extensions(self) -> List[str]:
        """Return list of supported file extensions."""
        return ['mdx']

    def process_file(self, file_path: Union[str, Path]) -> Dict[str, Any]:
        """Process an MDX file and extract information.

        Args:
            file_path: Path to the MDX file

        Returns:
            Dict containing extracted information:
            {
                'components': List of JSX components found
                'exports': List of exported items
                'imports': List of imported modules
                'frontmatter': Dict of frontmatter data
                'layout': Layout information
                'content': Markdown content
                'file_info': File metadata
                'errors': List of any errors encountered
            }
        """
        file_path = Path(file_path)
        if not file_path.exists():
            return {
                'error': f'File not found: {file_path}',
                'components': [],
                'exports': [],
                'imports': [],
                'frontmatter': {},
                'layout': None,
                'content': '',
                'file_info': {},
                'errors': [f'File not found: {file_path}']
            }

        try:
            content = file_path.read_text(encoding='utf-8')
            return self._process_content(content, file_path)
        except Exception as e:
            return {
                'error': str(e),
                'components': [],
                'exports': [],
                'imports': [],
                'frontmatter': {},
                'layout': None,
                'content': '',
                'file_info': self._get_file_info(file_path),
                'errors': [str(e)]
            }

    def _process_content(self, content: str, file_path: Path) -> Dict[str, Any]:
        """Process the content of an MDX file.

        Args:
            content: String content of the MDX file
            file_path: Path to the MDX file

        Returns:
            Dict containing extracted information
        """
        result = {
            'components': [],
            'exports': [],
            'imports': [],
            'frontmatter': {},
            'layout': None,
            'content': content,
            'file_info': self._get_file_info(file_path),
            'errors': []
        }

        # Extract frontmatter
        frontmatter_match = self.frontmatter_pattern.match(content)
        if frontmatter_match:
            try:
                frontmatter_content = frontmatter_match.group(1)
                frontmatter = yaml.safe_load(frontmatter_content)
                
                # Convert dates to strings
                for key, value in frontmatter.items():
                    if isinstance(value, (date, datetime)):
                        frontmatter[key] = value.isoformat().split('T')[0]
                
                result['frontmatter'] = frontmatter
                
                # Extract layout from frontmatter
                if 'layout' in frontmatter:
                    result['layout'] = frontmatter['layout']
                
                content = content[frontmatter_match.end():]
            except yaml.YAMLError as e:
                result['errors'].append(f'Error parsing frontmatter: {str(e)}')

        # Find JSX components
        components = set()
        for match in self.jsx_component_pattern.finditer(content):
            components.add(match.group(1))
        result['components'] = sorted(list(components))

        # Find exports
        exports = []
        for match in self.export_pattern.finditer(content):
            if match.group(0).startswith('export default'):
                exports.append('default')
            elif match.group(1):
                exports.append(match.group(1))
        result['exports'] = exports

        # Find imports
        imports = []
        for match in self.import_pattern.finditer(content):
            imports.append(match.group(1))
        result['imports'] = imports

        return result

    def _get_file_info(self, file_path: Path) -> Dict[str, Any]:
        """Get file metadata.

        Args:
            file_path: Path to the MDX file

        Returns:
            Dict containing file metadata
        """
        return {
            'name': file_path.name,
            'path': str(file_path),
            'size': file_path.stat().st_size if file_path.exists() else 0,
            'modified': file_path.stat().st_mtime if file_path.exists() else 0,
        }

    def _extract_props(self, component_str: str) -> Dict[str, str]:
        """Extract props from a JSX component string.

        Args:
            component_str: String containing the JSX component

        Returns:
            Dict of prop names and values
        """
        props = {}
        prop_pattern = re.compile(r'(\w+)=(?:\"([^\"]*)\"|{([^}]*)})')
        
        for match in prop_pattern.finditer(component_str):
            prop_name = match.group(1)
            prop_value = match.group(2) or match.group(3)
            props[prop_name] = prop_value

        return props

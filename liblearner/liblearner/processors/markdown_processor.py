"""
Markdown Processor for LibLearner.

This processor extracts structured information from Markdown files, including:
- Headers and their hierarchy
- Code blocks with language information
- Lists (ordered and unordered)
- Links and references
- Blockquotes
- Tables
- Emphasis and strong text
"""

import re
import pandas as pd
from typing import Dict, List, Optional, Tuple
from pathlib import Path
from ..file_processor import FileProcessor

class MarkdownProcessor(FileProcessor):
    def __init__(self):
        """Initialize the Markdown processor."""
        super().__init__()
        # Regular expressions for Markdown elements
        self.header_pattern = re.compile(r'^(#{1,6})\s+(.+)$', re.MULTILINE)
        self.code_block_pattern = re.compile(r'```(\w*)\n(.*?)```', re.DOTALL)
        self.inline_code_pattern = re.compile(r'(?<!`)`([^`]+)`(?!`)')  # Updated to avoid matching code blocks
        self.list_pattern = re.compile(r'^\s*[-*+]\s+(.+)$|\s*\d+\.\s+(.+)$', re.MULTILINE)
        self.link_pattern = re.compile(r'\[([^\]]+)\]\(([^)]+)\)')
        self.blockquote_pattern = re.compile(r'^\s*>\s+(.+)$', re.MULTILINE)
        self.table_pattern = re.compile(r'^\|(.+)\|$', re.MULTILINE)
        self.emphasis_pattern = re.compile(r'(?<!\*)\*(?!\*)([^*]+)\*(?!\*)|(?<!_)_(?!_)([^_]+)_(?!_)')
        self.strong_pattern = re.compile(r'\*\*([^*]+)\*\*|__([^_]+)__')

    def get_supported_types(self) -> List[str]:
        """Return list of supported MIME types."""
        return ['text/markdown']

    def get_supported_extensions(self) -> List[str]:
        """Return list of supported file extensions."""
        return ['md', 'markdown']

    def process_file(self, file_path: str) -> Dict:
        """
        Process a Markdown file and extract structured information.
        
        Args:
            file_path: Path to the Markdown file
            
        Returns:
            Dictionary containing extracted information:
            {
                'headers': List of (level, text) tuples,
                'code_blocks': List of (language, code) tuples,
                'inline_code': List of code snippets,
                'lists': List of list items,
                'links': List of (text, url) tuples,
                'blockquotes': List of quoted text,
                'tables': List of table rows,
                'emphasized_text': List of emphasized text,
                'strong_text': List of strong text,
                'metadata': Dictionary of metadata (if present),
                'toc': List of headers in table of contents format
            }
        """
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
        except Exception as e:
            self.results_df = pd.DataFrame(columns=['type', 'name', 'content', 'props', 'filepath'])
            raise RuntimeError(f"Error reading file {file_path}: {str(e)}")

        # First, remove code blocks to avoid interference with inline code matching
        code_blocks = []
        def store_code_block(match):
            code_blocks.append((match.group(1), match.group(2).strip()))
            return ''  # Remove the code block from the content

        content_without_blocks = self.code_block_pattern.sub(store_code_block, content)

        # Extract all elements
        headers = self._extract_headers(content)
        inline_code = self._extract_inline_code(content_without_blocks)
        lists = self._extract_lists(content)
        links = self._extract_links(content)
        blockquotes = self._extract_blockquotes(content)
        tables = self._extract_tables(content)
        emphasized = self._extract_emphasis(content)
        strong = self._extract_strong(content)
        metadata = self._extract_metadata(content)
        toc = self._generate_toc(headers)

        # Create results data for DataFrame
        results_data = []

        # Add headers
        for level, text in headers:
            results_data.append({
                'type': 'header',
                'name': f'h{level}',
                'content': text,
                'props': str({'level': level}),
                'filepath': file_path
            })

        # Add code blocks
        for idx, (lang, code) in enumerate(code_blocks):
            results_data.append({
                'type': 'code_block',
                'name': f'code_{idx}',
                'content': code,
                'props': str({'language': lang or 'text'}),
                'filepath': file_path
            })

        # Add inline code
        for idx, code in enumerate(inline_code):
            results_data.append({
                'type': 'inline_code',
                'name': f'inline_{idx}',
                'content': code,
                'props': str({}),
                'filepath': file_path
            })

        # Add lists
        for idx, item in enumerate(lists):
            results_data.append({
                'type': 'list_item',
                'name': f'item_{idx}',
                'content': item,
                'props': str({}),
                'filepath': file_path
            })

        # Add links
        for idx, (text, url) in enumerate(links):
            results_data.append({
                'type': 'link',
                'name': text,
                'content': url,
                'props': str({}),
                'filepath': file_path
            })

        # Add blockquotes
        for idx, quote in enumerate(blockquotes):
            results_data.append({
                'type': 'blockquote',
                'name': f'quote_{idx}',
                'content': quote,
                'props': str({}),
                'filepath': file_path
            })

        # Add tables
        for idx, row in enumerate(tables):
            results_data.append({
                'type': 'table_row',
                'name': f'row_{idx}',
                'content': row,
                'props': str({}),
                'filepath': file_path
            })

        # Add emphasized text
        for idx, text in enumerate(emphasized):
            results_data.append({
                'type': 'emphasis',
                'name': f'em_{idx}',
                'content': text,
                'props': str({}),
                'filepath': file_path
            })

        # Add strong text
        for idx, text in enumerate(strong):
            results_data.append({
                'type': 'strong',
                'name': f'strong_{idx}',
                'content': text,
                'props': str({}),
                'filepath': file_path
            })

        # Update the results DataFrame
        self.results_df = pd.DataFrame(results_data)

        # Return the legacy format for backward compatibility
        return {
            'type': 'markdown',
            'path': file_path,
            'headers': headers,
            'code_blocks': code_blocks,
            'inline_code': inline_code,
            'lists': lists,
            'links': links,
            'blockquotes': blockquotes,
            'tables': tables,
            'emphasized_text': emphasized,
            'strong_text': strong,
            'metadata': metadata,
            'toc': toc
        }

    def _extract_headers(self, content: str) -> List[Tuple[int, str]]:
        """Extract headers with their levels."""
        headers = []
        for match in self.header_pattern.finditer(content):
            level = len(match.group(1))  # Number of # symbols
            text = match.group(2).strip()
            headers.append((level, text))
        return headers

    def _extract_inline_code(self, content: str) -> List[str]:
        """Extract inline code snippets."""
        return [match.group(1) for match in self.inline_code_pattern.finditer(content)]

    def _extract_lists(self, content: str) -> List[str]:
        """Extract list items."""
        return [match.group(1) or match.group(2) for match in self.list_pattern.finditer(content)]

    def _extract_links(self, content: str) -> List[Tuple[str, str]]:
        """Extract links with their text and URLs."""
        return [(match.group(1), match.group(2)) for match in self.link_pattern.finditer(content)]

    def _extract_blockquotes(self, content: str) -> List[str]:
        """Extract blockquotes."""
        return [match.group(1) for match in self.blockquote_pattern.finditer(content)]

    def _extract_tables(self, content: str) -> List[str]:
        """Extract table rows."""
        return [match.group(1).strip() for match in self.table_pattern.finditer(content)]

    def _extract_emphasis(self, content: str) -> List[str]:
        """Extract emphasized text."""
        return [match.group(1) or match.group(2) for match in self.emphasis_pattern.finditer(content)]

    def _extract_strong(self, content: str) -> List[str]:
        """Extract strong text."""
        return [match.group(1) or match.group(2) for match in self.strong_pattern.finditer(content)]

    def _extract_metadata(self, content: str) -> Dict:
        """Extract YAML frontmatter if present."""
        metadata = {}
        # Look for YAML frontmatter between --- markers
        frontmatter_pattern = re.compile(r'^---\s*\n(.*?)\n---\s*\n', re.DOTALL)
        match = frontmatter_pattern.match(content)
        if match:
            # Parse simple key-value pairs
            for line in match.group(1).split('\n'):
                if ':' in line:
                    key, value = line.split(':', 1)
                    metadata[key.strip()] = value.strip()
        return metadata

    def _generate_toc(self, headers: List[Tuple[int, str]]) -> List[Dict]:
        """Generate a table of contents from headers."""
        toc = []
        for level, text in headers:
            # Create a slug for the header (simplified version)
            slug = re.sub(r'[^\w\s-]', '', text.lower())
            slug = re.sub(r'[-\s]+', '-', slug).strip('-')
            toc.append({
                'level': level,
                'text': text,
                'slug': slug
            })
        return toc

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
from typing import Dict, List, Optional, Tuple
from pathlib import Path

class MarkdownProcessor:
    def __init__(self):
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
            raise RuntimeError(f"Error reading file {file_path}: {str(e)}")

        # First, remove code blocks to avoid interference with inline code matching
        code_blocks = []
        def store_code_block(match):
            code_blocks.append((match.group(1), match.group(2).strip()))
            return ''  # Remove the code block from the content

        content_without_blocks = self.code_block_pattern.sub(store_code_block, content)

        result = {
            'headers': self._extract_headers(content),
            'code_blocks': code_blocks,
            'inline_code': self._extract_inline_code(content_without_blocks),  # Use content without code blocks
            'lists': self._extract_lists(content),
            'links': self._extract_links(content),
            'blockquotes': self._extract_blockquotes(content),
            'tables': self._extract_tables(content),
            'emphasized_text': self._extract_emphasis(content),
            'strong_text': self._extract_strong(content),
            'metadata': self._extract_metadata(content),
            'toc': self._generate_toc(content)
        }

        # Add file metadata
        path = Path(file_path)
        result['file_info'] = {
            'name': path.name,
            'path': str(path.absolute()),
            'size': path.stat().st_size,
            'last_modified': path.stat().st_mtime
        }

        return result

    def _extract_headers(self, content: str) -> List[Tuple[int, str]]:
        """Extract headers with their levels."""
        headers = []
        for match in self.header_pattern.finditer(content):
            level = len(match.group(1))  # Number of # symbols
            text = match.group(2).strip()
            headers.append((level, text))
        return headers

    def _extract_code_blocks(self, content: str) -> List[Tuple[str, str]]:
        """Extract code blocks with language information."""
        code_blocks = []
        for match in self.code_block_pattern.finditer(content):
            language = match.group(1) or 'text'  # Default to 'text' if no language specified
            code = match.group(2).strip()
            code_blocks.append((language, code))
        return code_blocks

    def _extract_inline_code(self, content: str) -> List[str]:
        """Extract inline code snippets."""
        return [m.group(1) for m in self.inline_code_pattern.finditer(content)]

    def _extract_lists(self, content: str) -> List[str]:
        """Extract list items (both ordered and unordered)."""
        items = []
        for match in self.list_pattern.finditer(content):
            # Group 1 is for unordered lists, group 2 for ordered lists
            item = match.group(1) or match.group(2)
            items.append(item.strip())
        return items

    def _extract_links(self, content: str) -> List[Tuple[str, str]]:
        """Extract links with their text and URLs."""
        return [(m.group(1), m.group(2)) for m in self.link_pattern.finditer(content)]

    def _extract_blockquotes(self, content: str) -> List[str]:
        """Extract blockquoted text."""
        return [m.group(1).strip() for m in self.blockquote_pattern.finditer(content)]

    def _extract_tables(self, content: str) -> List[List[str]]:
        """Extract tables and parse them into rows."""
        tables = []
        for match in self.table_pattern.finditer(content):
            row = [cell.strip() for cell in match.group(1).split('|')]
            tables.append(row)
        return tables

    def _extract_emphasis(self, content: str) -> List[str]:
        """Extract emphasized text (italic)."""
        return [m.group(1) or m.group(2) for m in self.emphasis_pattern.finditer(content)]

    def _extract_strong(self, content: str) -> List[str]:
        """Extract strong text (bold)."""
        return [m.group(1) or m.group(2) for m in self.strong_pattern.finditer(content)]

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

    def _generate_toc(self, content: str) -> List[Dict]:
        """Generate a table of contents from headers."""
        headers = self._extract_headers(content)
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

    def get_supported_extensions(self) -> List[str]:
        """Return list of supported file extensions."""
        return ['md', 'markdown']

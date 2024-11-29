"""
Markdown Processor for LibLearner.

This processor extracts structured information from Markdown and MDX files, including:
- Headers and their hierarchy
- Code blocks with language information
- Lists (ordered and unordered)
- Links and references
- Blockquotes
- Tables
- Emphasis and strong text
- JSX/TSX components (for MDX)
- Frontmatter metadata
"""

import re
import logging
import pandas as pd
from typing import Dict, List, Optional, Tuple, Union, Set
from pathlib import Path
import yaml
import frontmatter
import os
import json

from ..file_processor import FileProcessor
from ..processing_result import MarkdownProcessingResult

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class MarkdownProcessor(FileProcessor):
    """Processor for Markdown and MDX files."""
    
    def __init__(self, debug: bool = False):
        """Initialize the Markdown processor."""
        super().__init__()
        self.debug = debug
        if self.debug:
            logger.setLevel(logging.DEBUG)
            
        # Initialize results DataFrame
        self.results_df = pd.DataFrame()
            
        # Define supported MIME types
        self.supported_types = {
            'text/markdown',
            'text/x-markdown',
            'text/mdx'
        }
            
        # Initialize patterns
        self._init_patterns()
        
        # Initialize tracking variables
        self._order_counter = 0
        self._current_path = []
        
    def _init_patterns(self):
        """Initialize regex patterns for markdown parsing."""
        self.patterns = {
            'header': re.compile(r'^(#{1,6})\s+(.+)$', re.MULTILINE),
            'code_block': re.compile(r'```(\w*)\n(.*?)\n```', re.DOTALL),
            'jsx_component': re.compile(r'<([A-Z][a-zA-Z]*)[^>]*>.*?</\1>', re.DOTALL),
            'inline_jsx': re.compile(r'<([A-Z][a-zA-Z]*)[^>]*/>', re.MULTILINE),
            'list_item': re.compile(r'^\s*[-*+]\s+(.+)$', re.MULTILINE),
            'ordered_list': re.compile(r'^\s*\d+\.\s+(.+)$', re.MULTILINE),
            'link': re.compile(r'\[([^\]]+)\]\(([^)"]+)(?:\s+"[^"]*")?\)'),
            'reference_link': re.compile(r'\[([^\]]+)\]\[([^\]]+)\]'),
            'reference_def': re.compile(r'^\[([^\]]+)\]:\s*(.+)$', re.MULTILINE),
            'direct_link': re.compile(r'<(https?://[^>]+)>', re.MULTILINE),
            'blockquote': re.compile(r'^\s*>\s+(.+)$', re.MULTILINE),
            'table': re.compile(r'^\|(.+)\|$\n\|[-:\s|]+\|\n((?:\|.+\|\n?)+)', re.MULTILINE),
            'emphasis': re.compile(r'\*([^*]+)\*|_([^_]+)_'),
            'strong': re.compile(r'\*\*([^*]+)\*\*|__([^_]+)__')
        }
        
    def get_supported_types(self) -> List[str]:
        """Return list of supported MIME types."""
        return list(self.supported_types)
        
    def _validate_content(self, content: str) -> List[str]:
        """Validate markdown content for malformed elements."""
        errors = []
        
        # Check for unclosed code blocks
        code_blocks = re.findall(r'```[^\n]*\n(?:(?!```).)*(?:```)?', content, re.DOTALL)
        for block in code_blocks:
            if not block.strip().endswith('```'):
                errors.append("Found unclosed code block")
                break
        
        # Check for unclosed links
        # Count opening and closing brackets to handle nested brackets
        link_text = re.findall(r'\[([^\[\]]*)\](?!\()', content)
        for text in link_text:
            if '[' in text or ']' in text:
                errors.append(f"Found unclosed links: {text}")
        
        # Check for unclosed blockquotes
        lines = content.split('\n')
        in_blockquote = False
        empty_lines = 0
        for line in lines:
            stripped = line.strip()
            if stripped.startswith('>'):
                in_blockquote = True
                empty_lines = 0
            elif in_blockquote:
                if not stripped:
                    empty_lines += 1
                elif empty_lines > 1 and not stripped.startswith('>'):
                    in_blockquote = False
                elif not stripped.startswith('>') and empty_lines == 0:
                    in_blockquote = False
        
        return errors

    def process_file(self, file_path: str) -> MarkdownProcessingResult:
        """Process a markdown or MDX file and extract structured information."""
        self._order_counter = 0
        result = MarkdownProcessingResult()
        results_data = []
        
        path = Path(file_path)
        
        # Check file existence first
        if not os.path.exists(file_path):
            logger.error(f"Error processing {file_path}: File not found")
            raise FileNotFoundError(f"File not found: {file_path}")
        
        try:
            # Read file content
            content = path.read_text()
            
            # Parse frontmatter
            try:
                # Parse frontmatter using frontmatter v3.0.8 API
                parsed = frontmatter.parse(content)
                frontmatter_data = parsed[0] if parsed and len(parsed) > 0 else {}
                content = parsed[1] if parsed and len(parsed) > 1 else content
                # Store frontmatter data directly in result.metadata
                result.metadata = frontmatter_data
            except Exception as e:
                error_msg = f"Failed to parse frontmatter: {str(e)}"
                logger.warning(f"Failed to parse frontmatter in {file_path}: {e}")
                result.metadata = {}
                result.errors.append(error_msg)
            
            # Store file info
            result.file_info = {
                'name': path.name,
                'path': str(path.absolute()),
                'size': path.stat().st_size,
                'last_modified': path.stat().st_mtime,
                'type': 'markdown'
            }
            
            # Validate content for malformed elements
            validation_errors = self._validate_content(content)
            if validation_errors:
                for error in validation_errors:
                    result.errors.append(error)
                    logger.warning(f"Validation error in {file_path}: {error}")
            
            # Process imports (MDX specific)
            if str(path).endswith('.mdx'):
                self._process_imports(content, results_data, file_path)
            
            # Process markdown elements
            self._process_headers(content, results_data, file_path)
            self._process_code_blocks(content, results_data, file_path)
            self._process_jsx_components(content, results_data, file_path)
            self._process_lists(content, results_data, file_path)
            self._process_links(content, results_data, file_path)
            self._process_blockquotes(content, results_data, file_path)
            self._process_tables(content, results_data, file_path)
            
            # Create DataFrame
            df = pd.DataFrame(results_data) if results_data else pd.DataFrame(columns=[
                'filepath', 'parent_path', 'order', 'name', 
                'content', 'props', 'processor_type'
            ])
            
            if not df.empty:
                df = df.rename(columns={'type': 'processor_type'})
                column_order = ['filepath', 'parent_path', 'order', 'name', 
                              'content', 'props', 'processor_type']
                df = df[column_order]
                
                # Concatenate with existing results
                if not self.results_df.empty:
                    self.results_df = pd.concat([self.results_df, df], ignore_index=True)
                else:
                    self.results_df = df
            
            # Set the DataFrame in the result object
            result.df = df
                    
        except Exception as e:
            result.errors.append(str(e))
            logger.error(f"Error processing {file_path}: {e}")
            
            # Initialize empty DataFrame for error cases
            result.df = pd.DataFrame(columns=[
                'filepath', 'parent_path', 'order', 'name', 'content', 'props', 'processor_type'
            ])
            
        return result
        
    def _process_imports(self, content: str, results_data: List[Dict], file_path: str):
        """Process MDX import statements."""
        import_lines = re.finditer(r'^import\s+.*$', content, re.MULTILINE)
        for match in import_lines:
            self._order_counter += 1
            results_data.append({
                'filepath': str(file_path),
                'parent_path': '',
                'order': self._order_counter,
                'name': 'import',
                'content': match.group(0),
                'props': '{}',
                'type': 'import'
            })
            
    def _process_headers(self, content: str, results_data: List[Dict], file_path: str):
        """Process markdown headers."""
        for match in self.patterns['header'].finditer(content):
            level = len(match.group(1))
            text = match.group(2)
            self._order_counter += 1
            results_data.append({
                'filepath': str(file_path),
                'parent_path': '.'.join(self._current_path),
                'order': self._order_counter,
                'name': f'h{level}',
                'content': text,
                'props': f'{{"level": {level}}}',
                'type': 'header'
            })
            
    def _process_code_blocks(self, content: str, results_data: List[Dict], file_path: str):
        """Process code blocks with language information."""
        for match in self.patterns['code_block'].finditer(content):
            lang = match.group(1) or 'text'
            code = match.group(2)
            self._order_counter += 1
            results_data.append({
                'filepath': str(file_path),
                'parent_path': '.'.join(self._current_path),
                'order': self._order_counter,
                'name': 'code',
                'content': code,
                'props': f'{{"language": "{lang}"}}',
                'type': 'code_block'
            })
            
    def _process_jsx_components(self, content: str, results_data: List[Dict], file_path: str):
        """Process JSX/TSX components in MDX files."""
        # Process full components
        for match in self.patterns['jsx_component'].finditer(content):
            component_name = match.group(1)
            component_content = match.group(0)
            self._order_counter += 1
            results_data.append({
                'filepath': str(file_path),
                'parent_path': '.'.join(self._current_path),
                'order': self._order_counter,
                'name': component_name,
                'content': component_content,
                'props': '{}',  # Could be enhanced to parse actual props
                'type': 'jsx_component'
            })
            
        # Process self-closing components
        for match in self.patterns['inline_jsx'].finditer(content):
            component_name = match.group(1)
            self._order_counter += 1
            results_data.append({
                'filepath': str(file_path),
                'parent_path': '.'.join(self._current_path),
                'order': self._order_counter,
                'name': component_name,
                'content': match.group(0),
                'props': '{}',
                'type': 'jsx_component'
            })
            
    def _process_lists(self, content: str, results_data: List[Dict], file_path: str):
        """Process markdown lists."""
        # Process unordered lists
        for match in self.patterns['list_item'].finditer(content):
            self._order_counter += 1
            results_data.append({
                'filepath': str(file_path),
                'parent_path': '.'.join(self._current_path),
                'order': self._order_counter,
                'name': 'list_item',
                'content': match.group(1),
                'props': '{"ordered": false}',
                'type': 'list_item'
            })
            
        # Process ordered lists
        for match in self.patterns['ordered_list'].finditer(content):
            self._order_counter += 1
            results_data.append({
                'filepath': str(file_path),
                'parent_path': '.'.join(self._current_path),
                'order': self._order_counter,
                'name': 'list_item',
                'content': match.group(1),
                'props': '{"ordered": true}',
                'type': 'list_item'
            })
            
    def _process_links(self, content: str, results_data: List[Dict], file_path: str):
        """Process links."""
        # Process standard links
        for match in self.patterns['link'].finditer(content):
            self._order_counter += 1
            text, url = match.groups()
            results_data.append({
                'filepath': str(file_path),
                'parent_path': '.'.join(self._current_path),
                'order': self._order_counter,
                'name': text,
                'content': url,
                'props': json.dumps({"text": text}),
                'type': 'link'
            })
            
        # Process reference-style links
        references = {}
        for match in self.patterns['reference_def'].finditer(content):
            ref_id, url = match.groups()
            references[ref_id.lower()] = url.strip()
            
        for match in self.patterns['reference_link'].finditer(content):
            text, ref_id = match.groups()
            url = references.get(ref_id.lower())
            if url:
                self._order_counter += 1
                results_data.append({
                    'filepath': str(file_path),
                    'parent_path': '.'.join(self._current_path),
                    'order': self._order_counter,
                    'name': text,
                    'content': url,
                    'props': json.dumps({"text": text, "reference": ref_id}),
                    'type': 'link'
                })
                
        # Process direct links
        for match in self.patterns['direct_link'].finditer(content):
            url = match.group(1)
            self._order_counter += 1
            results_data.append({
                'filepath': str(file_path),
                'parent_path': '.'.join(self._current_path),
                'order': self._order_counter,
                'name': url,
                'content': url,
                'props': json.dumps({"text": url, "direct": True}),
                'type': 'link'
            })
            
    def _process_blockquotes(self, content: str, results_data: List[Dict], file_path: str):
        """Process blockquotes."""
        for idx, match in enumerate(self.patterns['blockquote'].finditer(content)):
            self._order_counter += 1
            results_data.append({
                'filepath': str(file_path),
                'parent_path': '.'.join(self._current_path),
                'order': self._order_counter,
                'name': f'quote_{idx}',
                'content': match.group(1).strip(),
                'props': '{}',
                'type': 'blockquote'
            })
            
    def _process_tables(self, content: str, results_data: List[Dict], file_path: str):
        """Process tables."""
        for idx, match in enumerate(self.patterns['table'].finditer(content)):
            self._order_counter += 1
            cells = [cell.strip() for cell in match.group(1).split('|')]
            results_data.append({
                'filepath': str(file_path),
                'parent_path': '.'.join(self._current_path),
                'order': self._order_counter,
                'name': f'row_{idx}',
                'content': '|'.join(cells),
                'props': f'{{"cells": {cells}}}',
                'type': 'table_row'
            })
            
    def _process_emphasis(self, content: str, results_data: List[Dict], file_path: str):
        """Process emphasized text."""
        for idx, match in enumerate(self.patterns['emphasis'].finditer(content)):
            self._order_counter += 1
            text = match.group(1) or match.group(2)
            results_data.append({
                'filepath': str(file_path),
                'parent_path': '.'.join(self._current_path),
                'order': self._order_counter,
                'name': f'em_{idx}',
                'content': text,
                'props': '{}',
                'type': 'emphasis'
            })
            
    def _process_strong(self, content: str, results_data: List[Dict], file_path: str):
        """Process strong text."""
        for idx, match in enumerate(self.patterns['strong'].finditer(content)):
            self._order_counter += 1
            text = match.group(1) or match.group(2)
            results_data.append({
                'filepath': str(file_path),
                'parent_path': '.'.join(self._current_path),
                'order': self._order_counter,
                'name': f'strong_{idx}',
                'content': text,
                'props': '{}',
                'type': 'strong'
            })

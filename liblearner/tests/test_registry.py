"""Tests for the ProcessorRegistry."""

import os
import tempfile
import unittest
from pathlib import Path
from liblearner.file_processor import ProcessorRegistry
from liblearner.processors import (
    PythonProcessor,
    JavaScriptProcessor,
    MarkdownProcessor,
    YAMLProcessor,
    MDXProcessor,
    JupyterProcessor
)

class TestRegistry(unittest.TestCase):
    """Test cases for the ProcessorRegistry."""

    def setUp(self):
        """Set up test environment."""
        self.registry = ProcessorRegistry()
        self.test_dir = tempfile.mkdtemp()
        
        # Create test files
        self.create_test_files()
        
    def create_test_files(self):
        """Create test files with different extensions."""
        test_files = {
            'test.py': 'def test(): pass',
            'test.js': 'function test() { }',
            'test.md': '# Test',
            'test.yaml': 'key: value',
            'test.mdx': '# Test MDX',
            'test.ipynb': '{"cells": [], "metadata": {}, "nbformat": 4, "nbformat_minor": 4}',
            'test.txt': 'Plain text',
            'test.unknown': 'Unknown type'
        }
        
        for filename, content in test_files.items():
            with open(os.path.join(self.test_dir, filename), 'w') as f:
                f.write(content)

    def test_processor_registration(self):
        """Test processor registration and retrieval."""
        # Register processors
        processors = [
            PythonProcessor(),
            JavaScriptProcessor(),
            MarkdownProcessor(),
            YAMLProcessor(),
            MDXProcessor(),
            JupyterProcessor()
        ]
        
        for processor in processors:
            self.registry.register_processor(processor)
        
        # Test processor retrieval
        self.assertEqual(
            self.registry.get_processor(os.path.join(self.test_dir, 'test.py')),
            processors[0]
        )
        self.assertEqual(
            self.registry.get_processor(os.path.join(self.test_dir, 'test.js')),
            processors[1]
        )
        self.assertEqual(
            self.registry.get_processor(os.path.join(self.test_dir, 'test.md')),
            processors[2]
        )
        self.assertEqual(
            self.registry.get_processor(os.path.join(self.test_dir, 'test.yaml')),
            processors[3]
        )
        self.assertEqual(
            self.registry.get_processor(os.path.join(self.test_dir, 'test.mdx')),
            processors[4]
        )
        self.assertEqual(
            self.registry.get_processor(os.path.join(self.test_dir, 'test.ipynb')),
            processors[5]
        )

    def test_mime_type_detection(self):
        """Test MIME type detection for different file types."""
        # Register all processors
        processors = [
            PythonProcessor(),
            JavaScriptProcessor(),
            MarkdownProcessor(),
            YAMLProcessor(),
            MDXProcessor(),
            JupyterProcessor()
        ]
        for processor in processors:
            self.registry.register_processor(processor)
        
        # Test MIME type detection
        test_cases = {
            'test.py': 'text/x-python',
            'test.js': 'text/javascript',
            'test.md': 'text/markdown',
            'test.yaml': 'text/x-yaml',
            'test.mdx': 'text/mdx',
            'test.ipynb': 'application/x-ipynb+json'
        }
        
        for filename, expected_mime in test_cases.items():
            file_path = os.path.join(self.test_dir, filename)
            processor = self.registry.get_processor(file_path)
            self.assertIsNotNone(processor, f"No processor found for {filename}")
            self.assertIn(
                expected_mime,
                processor.get_supported_types(),
                f"Processor for {filename} doesn't support {expected_mime}"
            )

    def test_unsupported_file_types(self):
        """Test handling of unsupported file types."""
        # Test with text file
        text_file = os.path.join(self.test_dir, 'test.txt')
        self.assertIsNone(self.registry.get_processor(text_file))
        
        # Test with unknown extension
        unknown_file = os.path.join(self.test_dir, 'test.unknown')
        self.assertIsNone(self.registry.get_processor(unknown_file))

    def test_processor_override(self):
        """Test processor override behavior."""
        # Register initial processor
        self.registry.register_processor(PythonProcessor())
        
        # Register new processor for same type
        new_processor = PythonProcessor()
        self.registry.register_processor(new_processor)
        
        # Verify new processor is used
        test_file = os.path.join(self.test_dir, 'test.py')
        self.assertEqual(
            self.registry.get_processor(test_file),
            new_processor
        )

    def test_multiple_mime_types(self):
        """Test processors supporting multiple MIME types."""
        processor = PythonProcessor()
        self.registry.register_processor(processor)
        
        # Test with different Python file extensions
        test_files = ['test.py', 'test.pyw', 'test.pyi']
        for filename in test_files:
            file_path = os.path.join(self.test_dir, filename)
            with open(file_path, 'w') as f:
                f.write('# Test Python file')
            
            retrieved_processor = self.registry.get_processor(file_path)
            self.assertEqual(
                retrieved_processor,
                processor,
                f"Failed to get correct processor for {filename}"
            )

    def test_registry_error_handling(self):
        """Test registry error handling."""
        # Register Python processor for testing empty Python files
        self.registry.register_processor(PythonProcessor())
        
        # Test with non-existent file
        non_existent = os.path.join(self.test_dir, 'non_existent.py')
        self.assertIsNone(self.registry.get_processor(non_existent))
        
        # Test with directory instead of file
        self.assertIsNone(self.registry.get_processor(self.test_dir))
        
        # Test with empty file
        empty_file = os.path.join(self.test_dir, 'empty.py')
        Path(empty_file).touch()
        processor = self.registry.get_processor(empty_file)
        self.assertIsNotNone(processor)
        self.assertIsInstance(processor, PythonProcessor)

if __name__ == '__main__':
    unittest.main()

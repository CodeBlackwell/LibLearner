"""Tests for file processor functionality."""

import os
import tempfile
from pathlib import Path
import unittest
from unittest.mock import Mock, patch
import shutil

from liblearner.file_processor import FileProcessor, ProcessorRegistry, FileTypeDetector

class TestFileTypeDetector(unittest.TestCase):
    """Test file type detection functionality."""
    
    def setUp(self):
        """Set up test environment."""
        self.detector = FileTypeDetector()
        self.temp_dir = tempfile.mkdtemp()
    
    def tearDown(self):
        """Clean up test environment."""
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def create_test_file(self, filename: str, content: str = "") -> str:
        """Create a test file with given content."""
        file_path = os.path.join(self.temp_dir, filename)
        with open(file_path, 'w') as f:
            f.write(content)
        return file_path
    
    def test_python_file_detection(self):
        """Test detection of Python files."""
        python_file = self.create_test_file("test.py", "def test(): pass")
        mime_type = self.detector.detect_type(python_file)
        self.assertEqual(mime_type, "text/x-python")
    
    def test_text_file_detection(self):
        """Test detection of text files."""
        text_file = self.create_test_file("test.txt", "This is a test")
        mime_type = self.detector.detect_type(text_file)
        self.assertEqual(mime_type, "text/plain")
    
    def test_jupyter_notebook_detection(self):
        """Test detection of Jupyter notebooks."""
        notebook_content = '''{
 "cells": [],
 "metadata": {},
 "nbformat": 4,
 "nbformat_minor": 4
}'''
        notebook_file = self.create_test_file("test.ipynb", notebook_content)
        mime_type = self.detector.detect_type(notebook_file)
        self.assertEqual(mime_type, "application/x-ipynb+json")

class TestProcessorRegistry(unittest.TestCase):
    """Test processor registry functionality."""
    
    def setUp(self):
        """Set up test environment."""
        self.registry = ProcessorRegistry()
        self.temp_dir = tempfile.mkdtemp()
    
    def tearDown(self):
        """Clean up test environment."""
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def create_test_file(self, filename: str, content: str = "") -> str:
        """Create a test file with given content."""
        file_path = os.path.join(self.temp_dir, filename)
        with open(file_path, 'w') as f:
            f.write(content)
        return file_path
    
    def test_processor_registration(self):
        """Test registering a processor."""
        class TestProcessor(FileProcessor):
            def get_supported_types(self):
                return ["test/type"]
            def process_file(self, file_path):
                return {"type": "test", "path": file_path}
        
        self.registry.register_processor(TestProcessor)
        processor = self.registry.get_processor(self.create_test_file("test.txt"))
        self.assertIsNone(processor)  # Should be None as it's not a supported type
    
    def test_text_file_handling(self):
        """Test handling of text files."""
        text_file = self.create_test_file("test.txt", "This is a test")
        processor = self.registry.get_processor(text_file)
        self.assertIsNone(processor)  # Should be None for text files
    
    def test_python_file_handling(self):
        """Test handling of Python files."""
        class PythonTestProcessor(FileProcessor):
            def get_supported_types(self):
                return ["text/x-python"]
            def process_file(self, file_path):
                return {"type": "python", "path": file_path}
        
        self.registry.register_processor(PythonTestProcessor)
        python_file = self.create_test_file("test.py", "def test(): pass")
        processor = self.registry.get_processor(python_file)
        self.assertIsNotNone(processor)
    
    def test_verbose_mode(self):
        """Test verbose mode functionality."""
        self.registry.set_verbose(True)
        with patch('builtins.print') as mock_print:
            self.registry._debug("Test message")
            mock_print.assert_called_once_with("DEBUG: Test message")
        
        self.registry.set_verbose(False)
        with patch('builtins.print') as mock_print:
            self.registry._debug("Test message")
            mock_print.assert_not_called()
    
    def test_directory_processing(self):
        """Test directory processing with ignore patterns."""
        # Create test directory structure
        os.makedirs(os.path.join(self.temp_dir, "venv"))
        os.makedirs(os.path.join(self.temp_dir, "src"))
        os.makedirs(os.path.join(self.temp_dir, "test.egg-info"))
        
        # Create test files
        self.create_test_file(os.path.join("src", "test.py"), "def test(): pass")
        self.create_test_file(os.path.join("venv", "ignore.py"), "# ignore this")
        self.create_test_file(os.path.join("test.egg-info", "ignore.txt"), "ignore")
        
        class TestProcessor(FileProcessor):
            def get_supported_types(self):
                return ["text/x-python"]
            def process_file(self, file_path):
                return {"type": "test", "path": file_path}
        
        self.registry.register_processor(TestProcessor)
        results = self.registry.process_directory(self.temp_dir)
        
        # Should only process files in src, ignoring venv and .egg-info
        self.assertEqual(len(results), 1)
        self.assertIn("src", results)

if __name__ == '__main__':
    unittest.main()

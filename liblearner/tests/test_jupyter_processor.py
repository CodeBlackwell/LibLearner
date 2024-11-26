"""Tests for Jupyter notebook processor functionality."""

import os
import json
import tempfile
import unittest
import shutil
from unittest.mock import patch

from liblearner.processors.jupyter_processor import JupyterProcessor

class TestJupyterProcessor(unittest.TestCase):
    """Test Jupyter notebook processor functionality."""
    
    def setUp(self):
        """Set up test environment."""
        self.processor = JupyterProcessor()
        self.temp_dir = tempfile.mkdtemp()
    
    def tearDown(self):
        """Clean up test environment."""
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def create_test_notebook(self, cells=None) -> str:
        """Create a test notebook with given cells."""
        if cells is None:
            cells = []
            
        notebook = {
            "cells": cells,
            "metadata": {},
            "nbformat": 4,
            "nbformat_minor": 4
        }
        
        file_path = os.path.join(self.temp_dir, "test.ipynb")
        with open(file_path, 'w') as f:
            json.dump(notebook, f)
        return file_path
    
    def test_supported_types(self):
        """Test supported MIME types."""
        supported_types = self.processor.get_supported_types()
        self.assertIn("application/x-ipynb+json", supported_types)
    
    def test_process_empty_notebook(self):
        """Test processing an empty notebook."""
        file_path = self.create_test_notebook()
        result = self.processor.process_file(file_path)
        
        self.assertEqual(result["type"], "jupyter")
        self.assertEqual(result["path"], file_path)
        self.assertEqual(len(result["cells"]), 0)
    
    def test_process_code_cells(self):
        """Test processing notebook with code cells."""
        cells = [
            {
                "cell_type": "code",
                "execution_count": 1,
                "metadata": {},
                "outputs": [],
                "source": ["def test_function():\n", "    return True"]
            },
            {
                "cell_type": "code",
                "execution_count": 2,
                "metadata": {},
                "outputs": [],
                "source": ["x = 42\n", "print(x)"]
            }
        ]
        
        file_path = self.create_test_notebook(cells)
        result = self.processor.process_file(file_path)
        
        self.assertEqual(result["type"], "jupyter")
        self.assertEqual(len(result["cells"]), 2)
        
        # Check first cell
        self.assertEqual(result["cells"][0]["cell_type"], "code")
        self.assertEqual(result["cells"][0]["execution_count"], 1)
        self.assertEqual("".join(result["cells"][0]["source"]), "def test_function():\n    return True")
        
        # Check second cell
        self.assertEqual(result["cells"][1]["cell_type"], "code")
        self.assertEqual(result["cells"][1]["execution_count"], 2)
        self.assertEqual("".join(result["cells"][1]["source"]), "x = 42\nprint(x)")
    
    def test_process_markdown_cells(self):
        """Test processing notebook with markdown cells."""
        cells = [
            {
                "cell_type": "markdown",
                "metadata": {},
                "source": ["# Test Heading\n", "This is a test."]
            }
        ]
        
        file_path = self.create_test_notebook(cells)
        result = self.processor.process_file(file_path)
        
        self.assertEqual(result["type"], "jupyter")
        self.assertEqual(len(result["cells"]), 1)
        self.assertEqual(result["cells"][0]["cell_type"], "markdown")
        self.assertEqual("".join(result["cells"][0]["source"]), "# Test Heading\nThis is a test.")
    
    def test_process_mixed_cells(self):
        """Test processing notebook with mixed cell types."""
        cells = [
            {
                "cell_type": "markdown",
                "metadata": {},
                "source": ["# Test"]
            },
            {
                "cell_type": "code",
                "execution_count": 1,
                "metadata": {},
                "outputs": [],
                "source": ["print('test')"]
            },
            {
                "cell_type": "raw",
                "metadata": {},
                "source": ["raw content"]
            }
        ]
        
        file_path = self.create_test_notebook(cells)
        result = self.processor.process_file(file_path)
        
        self.assertEqual(result["type"], "jupyter")
        self.assertEqual(len(result["cells"]), 3)
        self.assertEqual(result["cells"][0]["cell_type"], "markdown")
        self.assertEqual(result["cells"][1]["cell_type"], "code")
        self.assertEqual(result["cells"][2]["cell_type"], "raw")
    
    def test_process_invalid_notebook(self):
        """Test processing an invalid notebook file."""
        file_path = os.path.join(self.temp_dir, "invalid.ipynb")
        with open(file_path, 'w') as f:
            f.write("This is not a valid notebook")
        
        result = self.processor.process_file(file_path)
        
        self.assertEqual(result["type"], "jupyter")
        self.assertIn("error", result)
    
    def test_process_missing_file(self):
        """Test processing a non-existent file."""
        file_path = os.path.join(self.temp_dir, "nonexistent.ipynb")
        result = self.processor.process_file(file_path)
        
        self.assertEqual(result["type"], "jupyter")
        self.assertIn("error", result)

if __name__ == '__main__':
    unittest.main()

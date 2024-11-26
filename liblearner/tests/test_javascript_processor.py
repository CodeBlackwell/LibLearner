"""Tests for JavaScript processor functionality."""

import os
import json
import tempfile
import unittest
import shutil

from liblearner.processors.javascript_processor import JavaScriptProcessor

class TestJavaScriptProcessor(unittest.TestCase):
    """Test JavaScript processor functionality."""
    
    def setUp(self):
        """Set up test environment."""
        self.processor = JavaScriptProcessor()
        self.temp_dir = tempfile.mkdtemp()
    
    def tearDown(self):
        """Clean up test environment."""
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def create_test_file(self, content: str) -> str:
        """Create a test JavaScript file with given content."""
        file_path = os.path.join(self.temp_dir, "test.js")
        with open(file_path, 'w') as f:
            f.write(content)
        return file_path
    
    def test_supported_types(self):
        """Test supported MIME types."""
        supported_types = self.processor.get_supported_types()
        self.assertIn("application/javascript", supported_types)
        self.assertIn("text/javascript", supported_types)
    
    def test_process_empty_file(self):
        """Test processing an empty file."""
        file_path = self.create_test_file("")
        result = self.processor.process_file(file_path)
        
        self.assertEqual(result["type"], "javascript")
        self.assertEqual(result["path"], file_path)
        self.assertEqual(len(result["elements"]), 0)
    
    def test_process_simple_function(self):
        """Test processing a file with a simple function."""
        content = """
        function test() {
            return true;
        }
        """
        file_path = self.create_test_file(content)
        result = self.processor.process_file(file_path)
        
        self.assertEqual(result["type"], "javascript")
        self.assertEqual(len(result["elements"]), 1)
        element = result["elements"][0]
        self.assertEqual(element["type"], "Function")
        self.assertEqual(element["name"], "test")
    
    def test_process_class(self):
        """Test processing a file with a class definition."""
        content = """
        class TestClass {
            constructor() {
                this.value = 42;
            }
            
            getValue() {
                return this.value;
            }
        }
        """
        file_path = self.create_test_file(content)
        result = self.processor.process_file(file_path)
        
        self.assertEqual(result["type"], "javascript")
        elements = result["elements"]
        
        # Should find the class and its method
        class_element = next(e for e in elements if e["type"] == "Class")
        self.assertEqual(class_element["name"], "TestClass")
        
        method_element = next(e for e in elements if e["type"] == "Function" and e["name"] == "getValue")
        self.assertGreater(method_element["nestingLevel"], 0)
    
    def test_process_nested_functions(self):
        """Test processing nested functions."""
        content = """
        function outer() {
            function inner() {
                return 42;
            }
            return inner;
        }
        """
        file_path = self.create_test_file(content)
        result = self.processor.process_file(file_path)
        
        self.assertEqual(result["type"], "javascript")
        elements = result["elements"]
        
        outer_func = next(e for e in elements if e["name"] == "outer")
        inner_func = next(e for e in elements if e["name"] == "inner")
        
        self.assertEqual(outer_func["nestingLevel"], 0)
        self.assertGreater(inner_func["nestingLevel"], 0)
    
    def test_process_invalid_file(self):
        """Test processing an invalid JavaScript file."""
        content = "this is not valid javascript {"
        file_path = self.create_test_file(content)
        result = self.processor.process_file(file_path)
        
        self.assertEqual(result["type"], "javascript")
        self.assertIn("error", result)
        self.assertEqual(len(result["elements"]), 0)
    
    def test_process_missing_file(self):
        """Test processing a non-existent file."""
        file_path = os.path.join(self.temp_dir, "nonexistent.js")
        result = self.processor.process_file(file_path)
        
        self.assertEqual(result["type"], "javascript")
        self.assertIn("error", result)
        self.assertEqual(len(result["elements"]), 0)

if __name__ == '__main__':
    unittest.main()

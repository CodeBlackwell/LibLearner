"""Tests for Python processor functionality."""

import os
import tempfile
import unittest
from unittest.mock import patch
import shutil
import csv

from liblearner.processors.python_processor import PythonProcessor

class TestPythonProcessor(unittest.TestCase):
    """Test Python processor functionality."""
    
    def setUp(self):
        """Set up test environment."""
        self.processor = PythonProcessor()
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
    
    def test_supported_types(self):
        """Test supported MIME types."""
        supported_types = self.processor.get_supported_types()
        self.assertIn("text/x-python", supported_types)
        self.assertIn("application/x-python", supported_types)
        self.assertNotIn("text/plain", supported_types)
    
    def test_process_simple_function(self):
        """Test processing a file with a simple function."""
        content = '''def test_function():
    """Test function docstring."""
    return True'''
        
        file_path = self.create_test_file("test.py", content)
        result = self.processor.process_file(file_path)
        
        self.assertIsNotNone(result)
        self.assertEqual(result["type"], "python")
        self.assertEqual(result["path"], file_path)
        self.assertEqual(len(result["functions"]), 1)
        
        function = result["functions"][0]
        self.assertEqual(function["name"], "test_function")
        self.assertEqual(function["docstring"], "Test function docstring.")
    
    def test_process_multiple_functions(self):
        """Test processing a file with multiple functions."""
        content = '''def func1():
    """First function."""
    pass

def func2():
    """Second function."""
    return True'''
        
        file_path = self.create_test_file("test.py", content)
        result = self.processor.process_file(file_path)
        
        self.assertIsNotNone(result)
        self.assertEqual(len(result["functions"]), 2)
        
        names = [f["name"] for f in result["functions"]]
        self.assertIn("func1", names)
        self.assertIn("func2", names)
    
    def test_process_class_methods(self):
        """Test processing a file with class methods."""
        content = '''class TestClass:
    """Test class docstring."""
    
    def method1(self):
        """First method."""
        pass
    
    def method2(self):
        """Second method."""
        return True'''
        
        file_path = self.create_test_file("test.py", content)
        result = self.processor.process_file(file_path)
        
        self.assertIsNotNone(result)
        self.assertEqual(len(result["functions"]), 2)
        
        names = [f["name"] for f in result["functions"]]
        self.assertIn("TestClass.method1", names)
        self.assertIn("TestClass.method2", names)
    
    def test_process_nested_functions(self):
        """Test processing a file with nested functions."""
        content = '''def outer():
    """Outer function."""
    def inner():
        """Inner function."""
        pass
    return inner'''
        
        file_path = self.create_test_file("test.py", content)
        result = self.processor.process_file(file_path)
        
        self.assertIsNotNone(result)
        self.assertEqual(len(result["functions"]), 2)
        
        names = [f["name"] for f in result["functions"]]
        self.assertIn("outer", names)
        self.assertIn("outer.inner", names)
    
    def test_process_invalid_python(self):
        """Test processing a file with invalid Python code."""
        content = '''def invalid_syntax:
    this is not valid python'''
        
        file_path = self.create_test_file("test.py", content)
        result = self.processor.process_file(file_path)
        
        self.assertIsNotNone(result)
        self.assertEqual(result["type"], "python")
        self.assertIn("error", result)

    def test_csv_output(self):
        """Test that the CSV output is as expected."""
        test_code = '''
def test_function():
    """Test function docstring."""
    pass
'''
        from liblearner.python_extractor import extract_functions, write_results_to_csv
        
        functions = extract_functions(test_code, 'test.py')
        csv_path = os.path.join(self.temp_dir, "output.csv")
        write_results_to_csv(functions, csv_path)

        with open(csv_path, newline='') as csvfile:
            reader = csv.reader(csvfile)
            # Skip header row
            next(reader)
            row = next(reader)
            self.assertEqual(row[0], 'test.py')  # Filename
            self.assertEqual(row[1], 'Global')   # Parent
            self.assertEqual(row[2], '1')        # Order
            self.assertEqual(row[3], 'test_function')  # Function name
            self.assertEqual(row[4], '[]')       # Parameters
            self.assertEqual(row[5], 'Test function docstring.')  # Docstring

    def test_csv_output_with_sample_code(self):
        """Test that the CSV output is as expected with sample code."""
        sample_code = '''
class Calculator:
    def add(self, a, b):
        return a + b

def global_function(x):
    return x * 2

square = lambda x: x * x
'''
        from liblearner.python_extractor import extract_functions, write_results_to_csv
        
        functions = extract_functions(sample_code, 'example.py')
        csv_path = os.path.join(self.temp_dir, "output.csv")
        write_results_to_csv(functions, csv_path)

        with open(csv_path, newline='') as csvfile:
            reader = csv.reader(csvfile)
            output_content = list(reader)
            
            # Verify header
            self.assertEqual(output_content[0], 
                ['Filename', 'Parent', 'Order', 'Function/Method Name', 'Parameters', 'Docstring', 'Code'])
            
            # Verify Calculator.add method
            row = output_content[1]
            self.assertEqual(row[0], 'example.py')
            self.assertEqual(row[1], 'Calculator')
            self.assertEqual(row[2], '1')
            self.assertEqual(row[3], 'Calculator.add')
            self.assertEqual(row[4], "['self', 'a', 'b']")
            self.assertEqual(row[5], 'N/A')
            self.assertIn('def add(self, a, b):', row[6])
            self.assertIn('return', row[6])
            
            # Verify global_function
            row = output_content[2]
            self.assertEqual(row[0], 'example.py')
            self.assertEqual(row[1], 'Global')
            self.assertEqual(row[2], '2')
            self.assertEqual(row[3], 'global_function')
            self.assertEqual(row[4], "['x']")
            self.assertEqual(row[5], 'N/A')
            self.assertIn('def global_function(x):', row[6])
            self.assertIn('return', row[6])
            
            # Verify lambda function
            row = output_content[3]
            self.assertEqual(row[0], 'example.py')
            self.assertEqual(row[1], 'Global')
            self.assertEqual(row[2], '3')
            self.assertEqual(row[3], 'lambda_0')
            self.assertEqual(row[4], "['x']")
            self.assertEqual(row[5], 'N/A')
            self.assertIn('lambda x:', row[6])
            self.assertIn('x * x', row[6])
    
if __name__ == '__main__':
    unittest.main()

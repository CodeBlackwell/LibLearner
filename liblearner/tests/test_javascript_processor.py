"""Tests for JavaScript processor functionality."""

import os
import json
import csv
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
    
    def create_test_file(self, filename: str, content: str) -> str:
        """Create a test JavaScript file with given content."""
        file_path = os.path.join(self.temp_dir, filename)
        with open(file_path, 'w') as f:
            f.write(content)
        return file_path

    def test_csv_output(self):
        """Test that the CSV output format is correct for JavaScript code."""
        # Create a test file with a Calculator class
        content = '''
        /**
         * A simple calculator class
         */
        class Calculator {
            /**
             * Create a new Calculator
             * @param {number} precision - Number of decimal places
             */
            constructor(precision) {
                this.precision = precision;
            }

            /**
             * Add two numbers
             * @param {number} a - First number
             * @param {number} b - Second number
             * @returns {number} Sum of a and b
             */
            add(a, b) {
                return +(a + b).toFixed(this.precision);
            }
        }

        /**
         * Global utility function
         * @param {number} num - Number to format
         * @returns {string} Formatted number
         */
        function formatNumber(num) {
            return num.toLocaleString();
        }
        '''
        
        temp_path = self.create_test_file('calculator.js', content)
        
        try:
            result = self.processor.process_file(temp_path)
            
            csv_path = os.path.join(tempfile.gettempdir(), "output.csv")
            with open(csv_path, 'w', newline='') as csvfile:
                writer = csv.writer(csvfile)
                writer.writerow(['Filename', 'Type', 'Name', 'Parent', 'Parameters', 'Comments', 'Code'])
                
                # Write elements
                for element in result["elements"]:
                    writer.writerow([
                        'calculator.js',
                        element["type"],
                        element["name"],
                        element["parentName"] if "parentName" in element else "",
                        json.dumps(element.get("parameters", [])),  
                        "\n".join(element.get("comments", [])),
                        element.get("code", "")
                    ])

            # Read and verify the CSV content
            with open(csv_path, newline='') as csvfile:
                reader = csv.reader(csvfile)
                header = next(reader)
                self.assertEqual(header, ['Filename', 'Type', 'Name', 'Parent', 'Parameters', 'Comments', 'Code'])
                
                # Verify Calculator class
                row = next(reader)
                self.assertEqual(row[0], 'calculator.js')
                self.assertEqual(row[1], 'Class')
                self.assertEqual(row[2], 'Calculator')
                self.assertEqual(row[3], '')  # Top-level class has no parent
                
                # Verify constructor
                row = next(reader)
                self.assertEqual(row[1], 'Function')
                self.assertEqual(row[2], 'constructor')
                self.assertEqual(row[3], 'Class:Calculator')  # Parent is the Calculator class
                self.assertEqual(row[4], '["precision"]')
                
                # Verify add method
                row = next(reader)
                self.assertEqual(row[1], 'Function')
                self.assertEqual(row[2], 'add')
                self.assertEqual(row[3], 'Class:Calculator')  # Parent is the Calculator class
                self.assertEqual(row[4], '["a", "b"]')
                self.assertIn('Add two numbers', row[5])
                
                # Verify formatNumber function
                row = next(reader)
                self.assertEqual(row[1], 'Function')
                self.assertEqual(row[2], 'formatNumber')
                self.assertEqual(row[3], '')  # Top-level function has no parent
                self.assertEqual(row[4], '["num"]')
                self.assertIn('Global utility function', row[5])
        finally:
            os.remove(temp_path)

    def test_supported_types(self):
        """Test supported MIME types."""
        supported_types = self.processor.get_supported_types()
        self.assertIn("application/javascript", supported_types)
        self.assertIn("text/javascript", supported_types)
    
    def test_process_empty_file(self):
        """Test processing an empty file."""
        file_path = self.create_test_file("empty.js", "")
        result = self.processor.process_file(file_path)
        
        self.assertEqual(result["type"], "javascript")
        self.assertEqual(result["path"], file_path)
        self.assertEqual(len(result["elements"]), 0)
    
    def test_process_simple_function(self):
        """Test processing a file with a simple function."""
        js_code = '''
        function add(a, b) {
            return a + b;
        }
        '''
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.js', delete=False) as f:
            f.write(js_code)
            temp_path = f.name

        try:
            result = self.processor.process_file(temp_path)
            elements = result["elements"]
            self.assertEqual(len(elements), 1)
            
            func = elements[0]
            self.assertEqual(func["name"], "add")
            self.assertEqual(func["type"], "Function")
        finally:
            os.remove(temp_path)

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
        file_path = self.create_test_file("test.js", content)
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
        file_path = self.create_test_file("test.js", content)
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
        file_path = self.create_test_file("test.js", content)
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

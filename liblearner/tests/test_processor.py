#!/usr/bin/env python3



import os
import unittest
import pandas as pd
from liblearner.processors.python_processor import PythonProcessor
from liblearner.processors.yaml_processor import YAMLProcessor
from liblearner.processors.markdown_processor import MarkdownProcessor


def main():
    # Create processor
    processor = PythonProcessor()
    
    # Get test file path
    test_file = os.path.join(os.path.dirname(__file__), 'test_files', 'test_script.py')
    print(f"Processing file: {test_file}")
    
    # Process the file
    result = processor.process_file(test_file)
    
    # Print the result dictionary
    print("\nProcessor Result:")
    print(f"Type: {result['type']}")
    print(f"Path: {result['path']}")
    print(f"Number of functions: {len(result['functions'])}")
    
    # Print DataFrame info
    print("\nDataFrame Info:")
    print(processor.results_df.info())
    
    # Print DataFrame contents
    print("\nDataFrame Contents:")
    print(processor.results_df)

if __name__ == "__main__":
    main()


TEST_FILES_DIR = os.path.join(os.path.dirname(__file__), "test_files")

class TestProcessors(unittest.TestCase):
    """Test suite for file processors."""

    def test_python_processor_filepath(self):
        """Test that Python processor includes filepath in DataFrame."""
        processor = PythonProcessor()
        test_file = os.path.join(TEST_FILES_DIR, "test_script.py")
        
        # Process the file
        result = processor.process_file(test_file)
        df = processor.results_df
        
        # Check that filepath column exists and contains correct path
        self.assertIn('filepath', df.columns)
        self.assertTrue(all(df['filepath'] == test_file))

    def test_yaml_processor_filepath(self):
        """Test that YAML processor includes filepath in DataFrame."""
        processor = YAMLProcessor()
        test_file = os.path.join(TEST_FILES_DIR, "nested.yaml")
        
        # Process the file
        result = processor.process_file(test_file)
        df = processor.results_df
        
        # Check that filepath column exists and contains correct path
        self.assertIn('filepath', df.columns)
        self.assertTrue(all(df['filepath'] == test_file))

    def test_markdown_processor_filepath(self):
        """Test that Markdown processor includes filepath in DataFrame."""
        processor = MarkdownProcessor()
        test_file = os.path.join(TEST_FILES_DIR, "readme.md")
        
        # Process the file
        result = processor.process_file(test_file)
        df = processor.results_df
        
        # Check that filepath column exists and contains correct path
        self.assertIn('filepath', df.columns)
        self.assertTrue(all(df['filepath'] == test_file))

    def test_combined_dataframe_filepath(self):
        """Test that combined DataFrame preserves filepath information."""
        # Process files with different processors
        py_processor = PythonProcessor()
        yaml_processor = YAMLProcessor()
        md_processor = MarkdownProcessor()
        
        py_file = os.path.join(TEST_FILES_DIR, "test_script.py")
        yaml_file = os.path.join(TEST_FILES_DIR, "nested.yaml")
        md_file = os.path.join(TEST_FILES_DIR, "readme.md")
        
        py_processor.process_file(py_file)
        yaml_processor.process_file(yaml_file)
        md_processor.process_file(md_file)
        
        # Combine DataFrames
        combined_df = pd.concat([
            py_processor.results_df,
            yaml_processor.results_df,
            md_processor.results_df
        ], ignore_index=True)
        
        # Verify filepath column exists and contains all source files
        self.assertIn('filepath', combined_df.columns)
        self.assertIn(py_file, combined_df['filepath'].values)
        self.assertIn(yaml_file, combined_df['filepath'].values)
        self.assertIn(md_file, combined_df['filepath'].values)
        
        # Verify each row has the correct filepath
        for _, row in combined_df.iterrows():
            if 'test_func' in str(row['content']):
                self.assertEqual(row['filepath'], py_file)
            elif 'nested' in str(row['content']):
                self.assertEqual(row['filepath'], yaml_file)
            elif '# Test' in str(row['content']):
                self.assertEqual(row['filepath'], md_file)

if __name__ == '__main__':
    unittest.main()

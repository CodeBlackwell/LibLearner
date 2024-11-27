import os
import pandas as pd
import shutil
import tempfile
import unittest
from pathlib import Path

from liblearner.file_processor import registry
from liblearner.processors import (
    PythonProcessor,
    YAMLProcessor,
    MarkdownProcessor,
    JupyterProcessor
)

class TestProcessorIntegration(unittest.TestCase):
    def setUp(self):
        # Create a temporary directory for test files
        self.test_dir = tempfile.mkdtemp()
        self.output_dir = tempfile.mkdtemp()
        
        # Create test files
        self.create_test_files()
        
        # Register processors
        registry.register_processor(PythonProcessor)
        registry.register_processor(YAMLProcessor)
        registry.register_processor(MarkdownProcessor)
        registry.register_processor(JupyterProcessor)
        
    def tearDown(self):
        # Clean up test directories
        shutil.rmtree(self.test_dir)
        shutil.rmtree(self.output_dir)
        
    def create_test_files(self):
        # Create a Python file
        python_content = """
def test_function():
    '''Test docstring'''
    return True
        """
        with open(os.path.join(self.test_dir, "test.py"), "w") as f:
            f.write(python_content)
            
        # Create a YAML file
        yaml_content = """
services:
  web:
    image: nginx:latest
    environment:
      - API_KEY=${API_KEY}
    """
        with open(os.path.join(self.test_dir, "test.yaml"), "w") as f:
            f.write(yaml_content)
            
        # Create a Markdown file
        md_content = """
# Test Header

```python
def example():
    pass
```
        """
        with open(os.path.join(self.test_dir, "test.md"), "w") as f:
            f.write(md_content)
            
        # Create a subdirectory with more files
        os.makedirs(os.path.join(self.test_dir, "subdir"))
        with open(os.path.join(self.test_dir, "subdir", "nested.py"), "w") as f:
            f.write("def nested_function(): pass")
            
    def test_process_directory(self):
        """Test processing a directory with multiple file types"""
        # Process the test directory
        results = registry.process_directory(self.test_dir)
        
        # Verify results structure
        self.assertIn('.', results)  # Root directory results
        self.assertIn('subdir', results)  # Subdirectory results
        
        # Verify file processing
        root_files = [r['path'] for r in results['.'] if isinstance(r, dict)]
        self.assertTrue(any('test.py' in f for f in root_files))
        self.assertTrue(any('test.yaml' in f for f in root_files))
        self.assertTrue(any('test.md' in f for f in root_files))
        
        # Verify subdirectory processing
        subdir_files = [r['path'] for r in results['subdir'] if isinstance(r, dict)]
        self.assertTrue(any('nested.py' in f for f in subdir_files))
        
    def test_csv_output(self):
        """Test CSV output generation"""
        # Process directory
        registry.process_directory(self.test_dir)
        
        # Write results to CSV
        registry.write_results_to_csv(self.output_dir)
        
        # Check combined results file
        results_file = os.path.join(self.output_dir, 'all_results.csv')
        self.assertTrue(os.path.exists(results_file))
        
        # Read and verify CSV content
        df = pd.read_csv(results_file)
        
        # Verify required columns
        required_columns = ['file_type', 'filename', 'type', 'name', 'content', 'props']
        for col in required_columns:
            self.assertIn(col, df.columns)
            
        # Verify different file types are present
        file_types = df['file_type'].unique()
        self.assertTrue(len(file_types) >= 3)  # At least Python, YAML, and Markdown
        
        # Verify content from different files
        self.assertTrue(any(df['content'].str.contains('test_function', na=False)))
        self.assertTrue(any(df['content'].str.contains('nginx:latest', na=False)))
        self.assertTrue(any(df['content'].str.contains('Test Header', na=False)))
        
    def test_separate_csv_output(self):
        """Test separate CSV output files for each type"""
        # Process directory
        registry.process_directory(self.test_dir)
        
        # Write separate CSV files
        registry.write_results_to_csv(self.output_dir, combined=False)
        
        # Check for type-specific CSV files
        csv_files = list(Path(self.output_dir).glob('*_results.csv'))
        self.assertTrue(len(csv_files) >= 3)  # At least Python, YAML, and Markdown
        
        # Verify content of each file
        for csv_file in csv_files:
            df = pd.read_csv(csv_file)
            self.assertIn('filename', df.columns)
            self.assertIn('type', df.columns)
            self.assertIn('content', df.columns)
            
if __name__ == '__main__':
    unittest.main()

import os
import pandas as pd
import shutil
import tempfile
import unittest
from pathlib import Path
import subprocess
import sys
from liblearner.file_type_detector import FileTypeDetector

from liblearner.file_processor import registry
from liblearner.processors import (
    PythonProcessor,
    YAMLProcessor,
    MarkdownProcessor,
    JupyterProcessor
)
from liblearner.processors.yaml_processor import YAMLProcessingResult

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
            
    def test_dataframe_csv_output(self):
        """Test that processor DataFrames are correctly written to CSV files."""
        import subprocess
        import sys
        
        # Create a temporary directory for test files
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create test files
            test_yaml = os.path.join(temp_dir, 'sample.yaml')
            with open(test_yaml, 'w') as f:
                f.write("""name: test
version: 1.0
dependencies:
  - python>=3.7
  - pandas""")
            
            test_python = os.path.join(temp_dir, 'sample.py')
            with open(test_python, 'w') as f:
                f.write("""def sample_function():
    \"\"\"This is a sample function.\"\"\"
    return "Hello, World!\"""")

            # Create output directory
            output_dir = os.path.join(temp_dir, 'output')
            os.makedirs(output_dir, exist_ok=True)

            # Run process_files script
            script_path = os.path.join(os.path.dirname(__file__), '..', 'bin', 'process_files')
            result = subprocess.run([sys.executable, script_path, temp_dir, '-o', output_dir, '-v'],
                                 capture_output=True, text=True)
            self.assertEqual(result.returncode, 0, f"Script failed with error: {result.stderr}")

            # Verify combined CSV exists and has correct format
            combined_csv = os.path.join(output_dir, f"{os.path.basename(temp_dir)}_combined.csv")
            self.assertTrue(os.path.exists(combined_csv), "Combined CSV file not found")

            # Read and verify combined CSV
            df = pd.read_csv(combined_csv)
            self.assertGreater(len(df), 0, "Combined CSV is empty")
            
            # Required columns from processors
            required_columns = {'type', 'name', 'content', 'props'}
            self.assertTrue(required_columns.issubset(df.columns), 
                          f"Missing required columns. Found: {df.columns}")

            # Verify type-specific CSVs exist
            yaml_csv = os.path.join(output_dir, f"{os.path.basename(temp_dir)}_text_x_yaml.csv")
            python_csv = os.path.join(output_dir, f"{os.path.basename(temp_dir)}_text_x_python.csv")

            # At least one type-specific CSV should exist
            self.assertTrue(os.path.exists(yaml_csv) or os.path.exists(python_csv),
                          "No type-specific CSV files found")

            # If YAML CSV exists, verify its content
            if os.path.exists(yaml_csv):
                yaml_df = pd.read_csv(yaml_csv)
                self.assertGreater(len(yaml_df), 0, "YAML CSV is empty")
                self.assertTrue(all(yaml_df['type'] == 'text/x-yaml'),
                              f"YAML CSV contains non-YAML entries such as {yaml_df[yaml_df['type'] != 'text/x-yaml']['type'].unique()}")

            # If Python CSV exists, verify its content
            if os.path.exists(python_csv):
                python_df = pd.read_csv(python_csv)
                self.assertGreater(len(python_df), 0, "Python CSV is empty")
                
                # Verify each file in the DataFrame is a Python file
                for file_path in python_df['filepath'].unique():
                    # Check file extension
                    ext = Path(file_path).suffix.lower()
                    self.assertEqual(ext, '.py',
                                  f"File {file_path} does not have .py extension")
                    
                    # Check it's a text file
                    detector = FileTypeDetector()
                    mime_type = detector.detect_type(file_path)
                    self.assertTrue(mime_type in ['text/plain', 'text/x-python'],
                                  f"File {file_path} is not a text file: {mime_type}")
            
    def test_yaml_processing(self):
        """Test YAML file processing specifically"""
        print("\n=== Testing YAML Processing ===")
        
        # Create a YAML file with known content
        yaml_content = """
services:
  web:
    image: nginx:latest
    environment:
      - API_KEY=${API_KEY}
    ports:
      - "8080:80"
dependencies:
  - nginx>=1.19.0
  - python>=3.8
        """
        yaml_path = os.path.join(self.test_dir, "test.yaml")
        with open(yaml_path, "w") as f:
            f.write(yaml_content)
        print(f"\nCreated YAML file: {yaml_path}")
        print(f"Content:\n{yaml_content}")
            
        # Process the file directly
        print("\nProcessing file...")
        result = registry.process_file(yaml_path)
        print(f"\nProcessor result:")
        print(f"  File info: {result.file_info}")
        print(f"  Documents: {result.documents}")
        print(f"  Services: {result.services}")
        print(f"  Environment vars: {result.env_vars}")
        print(f"  Dependencies: {result.dependencies}")
        print(f"  URLs: {result.urls}")
        print(f"  Types: {result.types}")
        print(f"  Errors: {result.errors}")
        
        # Validate result type
        print("\nValidating result structure...")
        self.assertIsInstance(result, YAMLProcessingResult, "Result should be a YAMLProcessingResult")
        self.assertIn('path', result.file_info, "Result should contain file path")
        self.assertEqual(result.file_info['path'], str(Path(yaml_path).absolute()), "File path should match")
        
        # Validate file info
        print("\nValidating file info...")
        self.assertGreater(result.file_info.get('size', 0), 0, "File size should be positive")
        
        # Validate content extraction
        print("\nValidating content extraction...")
        self.assertGreater(len(result.services), 0, "Should extract services")
        self.assertIn('web', result.services, "Should find web service")
        
        self.assertGreater(len(result.env_vars), 0, "Should extract environment variables")
        self.assertIn('API_KEY', result.env_vars, "Should find API_KEY variable")
        
        self.assertGreater(len(result.dependencies), 0, "Should extract dependencies")
        self.assertIn('nginx', [dep.split('>=')[0] for dep in result.dependencies], "Should find nginx dependency")
        self.assertIn('python', [dep.split('>=')[0] for dep in result.dependencies], "Should find python dependency")
        
        # Validate no errors occurred
        self.assertEqual(len(result.errors), 0, f"Processing had errors: {result.errors}")
        print("\nAll validations passed!")
        
if __name__ == '__main__':
    unittest.main()

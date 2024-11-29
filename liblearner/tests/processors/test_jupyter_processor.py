"""Test module for JupyterProcessor."""

import os
from pathlib import Path
import pytest
import pandas as pd

from liblearner.processors import JupyterProcessor
from liblearner.file_processor import FileTypeDetector
from liblearner.processing_result import JupyterProcessingResult

# Get test files directory
TEST_FILES_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'test_files')

def test_mime_type_detection():
    """Test MIME type detection for Jupyter notebooks."""
    detector = FileTypeDetector()
    notebook_path = os.path.join(TEST_FILES_DIR, 'example.ipynb')
    assert detector.detect_type(notebook_path) == 'application/x-ipynb+json'
    
def test_supported_types():
    """Test supported MIME types."""
    processor = JupyterProcessor()
    supported = processor.get_supported_types()
    assert 'application/x-ipynb+json' in supported
    assert 'application/x-jupyter' in supported
    assert 'text/x-ipynb+json' in supported
    
def test_process_notebook():
    """Test processing a Jupyter notebook."""
    processor = JupyterProcessor()
    notebook_path = os.path.join(TEST_FILES_DIR, 'example.ipynb')
    result = processor.process_file(notebook_path)
    
    # Check result type
    assert isinstance(result, JupyterProcessingResult)
    
    # Check file info
    assert result.file_info['name'] == 'example.ipynb'
    assert os.path.samefile(result.file_info['path'], notebook_path)
    
    # Check metadata
    assert 'kernelspec' in result.metadata
    assert result.metadata['kernelspec']['language'] == 'python'
    
    # Check cells
    assert len(result.cells) > 0  # Should have cells and outputs
    
    # Check DataFrame
    df = processor.get_results_dataframe()
    assert not df.empty
    assert all(col in df.columns for col in [
        'filepath', 'parent_path', 'order', 'name', 
        'content', 'props', 'processor_type'
    ])
    
    # Check cell types
    cell_types = set(eval(props)['cell_type'] 
                    for props in df[df['processor_type'] == 'cell']['props'])
    assert 'markdown' in cell_types
    assert 'code' in cell_types
    
    # Check outputs
    outputs = df[df['processor_type'] == 'output']
    assert not outputs.empty
    output_types = set(eval(props)['output_type'] 
                      for props in outputs['props'])
    assert 'execute_result' in output_types
    assert 'stream' in output_types
    
def test_results_accumulation():
    """Test that results accumulate across multiple files."""
    processor = JupyterProcessor()
    notebook_path = os.path.join(TEST_FILES_DIR, 'example.ipynb')
    
    # Process the same file twice
    processor.process_file(notebook_path)
    len1 = len(processor.results_df)
    processor.process_file(notebook_path)
    len2 = len(processor.results_df)
    
    # Results should accumulate
    assert len2 > len1
    
def test_error_handling():
    """Test error handling for invalid notebooks."""
    processor = JupyterProcessor()
    
    # Test with non-existent file
    result = processor.process_file('nonexistent.ipynb')
    assert len(result.errors) > 0
    
    # Test with invalid JSON
    invalid_notebook = os.path.join(TEST_FILES_DIR, 'invalid.ipynb')
    Path(invalid_notebook).write_text('{invalid json}')
    result = processor.process_file(invalid_notebook)
    assert len(result.errors) > 0
    
    # Clean up
    os.remove(invalid_notebook)

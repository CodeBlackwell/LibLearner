"""Tests for the YAML processor."""

import os
from pathlib import Path
import pytest
import pandas as pd

from liblearner.processors.yaml_processor import YAMLProcessor
from liblearner.processing_result import YAMLProcessingResult

# Get the absolute path to the test files directory
TEST_FILES_DIR = Path(__file__).parent.parent / 'test_files'
EXAMPLE_YAML = TEST_FILES_DIR / 'example.yaml'

def test_mime_type_detection():
    """Test MIME type detection for YAML files."""
    processor = YAMLProcessor()
    supported_types = processor.get_supported_types()
    
    assert 'text/x-yaml' in supported_types
    assert 'application/x-yaml' in supported_types
    assert 'text/yaml' in supported_types
    assert 'application/yaml' in supported_types

def test_supported_types():
    """Test that processor supports YAML files."""
    processor = YAMLProcessor()
    assert processor.get_supported_types()
    assert len(processor.get_supported_types()) == 4

def test_process_yaml():
    """Test processing a YAML file."""
    processor = YAMLProcessor()
    result = processor.process_file(str(EXAMPLE_YAML))
    
    # Check result type
    assert isinstance(result, YAMLProcessingResult)
    assert not result.errors
    
    # Check file info
    assert result.file_info
    assert result.file_info['name'] == 'example.yaml'
    assert result.file_info['path'] == str(EXAMPLE_YAML)
    
    # Check data extraction
    assert 'doc_0' in result.data
    doc = result.data['doc_0']
    assert doc['name'] == 'Example Config'
    assert doc['version'] == '1.0.0'
    
    # Check DataFrame creation
    df = processor.results_df
    assert not df.empty
    assert 'filepath' in df.columns
    assert 'parent_path' in df.columns
    assert 'order' in df.columns
    assert 'name' in df.columns
    assert 'content' in df.columns
    assert 'props' in df.columns
    assert 'processor_type' in df.columns
    
    # Check document structure
    doc_row = df[df['name'] == 'document_0'].iloc[0]
    assert doc_row['processor_type'] == 'document'
    assert doc_row['parent_path'] == ''
    
    # Check mapping entries
    database_rows = df[df['parent_path'].str.contains('database', na=False)]
    assert not database_rows.empty
    
    # Check sequence entries
    deps_rows = df[df['parent_path'].str.contains('dependencies', na=False)]
    assert not deps_rows.empty

def test_results_accumulation():
    """Test that results accumulate correctly across multiple files."""
    processor = YAMLProcessor()
    
    # Process the file twice
    result1 = processor.process_file(str(EXAMPLE_YAML))
    initial_len = len(processor.results_df)
    
    result2 = processor.process_file(str(EXAMPLE_YAML))
    final_len = len(processor.results_df)
    
    # Check that results accumulated
    assert final_len == 2 * initial_len
    assert not result1.errors
    assert not result2.errors

def test_error_handling():
    """Test error handling for invalid files."""
    processor = YAMLProcessor()
    
    # Test non-existent file
    result = processor.process_file('nonexistent.yaml')
    assert result.errors
    assert 'File not found' in result.errors[0]
    
    # Test invalid YAML content
    invalid_yaml = TEST_FILES_DIR / 'invalid.yaml'
    try:
        invalid_yaml.write_text("""
        invalid:
          - unclosed bracket: [
          - missing colon value
        """)
        
        result = processor.process_file(str(invalid_yaml))
        assert result.errors
        assert any('YAML parsing error' in error for error in result.errors)
        
    finally:
        # Clean up
        if invalid_yaml.exists():
            invalid_yaml.unlink()

def test_env_vars_extraction():
    """Test extraction of environment variables."""
    processor = YAMLProcessor()
    result = processor.process_file(str(EXAMPLE_YAML))
    
    # Check environment variables in props
    df = processor.results_df
    database_rows = df[df['parent_path'].str.contains('database', na=False)]
    
    # Convert string props to eval-able form and check env vars
    for _, row in database_rows.iterrows():
        props = eval(row['props'])
        if 'env_vars' in props:
            env_vars = props['env_vars']
            if row['name'] == 'host':
                assert 'DB_HOST' in env_vars
            elif row['name'] == 'port':
                assert 'DB_PORT' in env_vars
            elif row['name'] == 'user':
                assert 'DB_USER' in env_vars

def test_url_extraction():
    """Test extraction of URLs."""
    processor = YAMLProcessor()
    result = processor.process_file(str(EXAMPLE_YAML))
    
    # Check URLs in props
    df = processor.results_df
    endpoint_rows = df[df['parent_path'].str.contains('endpoints', na=False)]
    
    # Convert string props to eval-able form and check URLs
    for _, row in endpoint_rows.iterrows():
        props = eval(row['props'])
        if 'urls' in props:
            urls = props['urls']
            if row['name'] == 'api':
                assert 'https://api.example.com/v1' in urls
            elif row['name'] == 'docs':
                assert 'http://docs.example.com' in urls

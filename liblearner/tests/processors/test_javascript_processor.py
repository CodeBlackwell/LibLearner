"""Tests for the JavaScript processor."""

import pytest
import os
import json
from pathlib import Path
from liblearner.processors.javascript_processor import JavaScriptProcessor
from liblearner.processing_result import JavaScriptProcessingResult

@pytest.fixture
def javascript_processor():
    """Create a JavaScript processor instance."""
    return JavaScriptProcessor()

@pytest.fixture
def create_temp_js(tmp_path):
    """Create a temporary JavaScript file."""
    def _create_temp_js(content: str) -> Path:
        js_file = tmp_path / "test.js"
        js_file.write_text(content)
        return js_file
    return _create_temp_js

def test_javascript_processor_initialization(javascript_processor):
    """Test JavaScript processor initialization."""
    assert isinstance(javascript_processor, JavaScriptProcessor)
    assert javascript_processor.results_df.empty
    assert javascript_processor._order_counter == 0
    assert not javascript_processor._current_path

def test_supported_mime_types(javascript_processor):
    """Test supported MIME types."""
    supported_types = javascript_processor.get_supported_types()
    assert 'application/javascript' in supported_types
    assert 'text/javascript' in supported_types
    assert 'application/x-javascript' in supported_types

def test_process_javascript_file(javascript_processor, create_temp_js):
    """Test processing a basic JavaScript file."""
    content = """
    class TestClass {
        constructor(name) {
            this.name = name;
        }
        
        sayHello() {
            console.log(`Hello ${this.name}`);
        }
    }
    
    function greet(person) {
        console.log(`Hi ${person}`);
    }
    """
    js_file = create_temp_js(content)
    result = javascript_processor.process_file(str(js_file))
    
    assert isinstance(result, JavaScriptProcessingResult)
    assert not result.errors
    assert result.file_info['type'] == 'javascript'
    
    df = result.df
    assert not df.empty
    assert 'TestClass' in df['name'].values
    assert 'greet' in df['name'].values
    assert 'sayHello' in df['name'].values

def test_javascript_validation(javascript_processor, create_temp_js):
    """Test JavaScript content validation."""
    # Test unclosed braces
    content = """
    function test() {
        if (true) {
            console.log('test');
        // Missing closing brace
    """
    js_file = create_temp_js(content)
    result = javascript_processor.process_file(str(js_file))
    assert len(result.errors) > 0
    assert any('unclosed braces' in error.lower() for error in result.errors)

def test_environment_variables(javascript_processor, create_temp_js):
    """Test environment variable extraction."""
    content = """
    function loadConfig() {
        const apiKey = process.env.API_KEY;
        const dbUrl = process.env['DATABASE_URL'];
        console.log(process.env.NODE_ENV);
        return { apiKey, dbUrl };
    }
    """
    js_file = create_temp_js(content)
    result = javascript_processor.process_file(str(js_file))
    
    # Check extracted env vars in DataFrame props
    assert not result.errors, f"Unexpected errors: {result.errors}"
    assert not result.df.empty, "DataFrame should not be empty"
    assert len(result.df) == 1, "Should have one function"
    assert result.df.iloc[0]['name'] == 'loadConfig'
    
    # Get props from the first row
    props = json.loads(result.df.iloc[0]['props'])
    env_vars = props['env_vars']
    assert 'API_KEY' in env_vars
    assert 'DATABASE_URL' in env_vars
    assert 'NODE_ENV' in env_vars

def test_url_extraction(javascript_processor, create_temp_js):
    """Test URL extraction."""
    content = """
    class ApiClient {
        constructor() {
            this.baseUrl = 'https://api.example.com/v1';
        }
        
        async fetchData() {
            await fetch('https://api.test.com/data');
            return fetch('/api/users');
        }
    }
    """
    js_file = create_temp_js(content)
    result = javascript_processor.process_file(str(js_file))
    
    # Check extracted URLs in DataFrame props
    assert not result.errors, f"Unexpected errors: {result.errors}"
    assert not result.df.empty, "DataFrame should not be empty"
    assert len(result.df) >= 2, "Should have class and method"
    
    # Get props from the class definition
    class_props = json.loads(result.df[result.df['processor_type'] == 'class'].iloc[0]['props'])
    method_props = json.loads(result.df[result.df['processor_type'] == 'function'].iloc[0]['props'])
    
    # URLs should be found in both class and method
    urls = set(class_props['urls']).union(set(method_props['urls']))
    assert 'https://api.example.com/v1' in urls
    assert 'https://api.test.com/data' in urls
    assert '/api/users' in urls

def test_error_handling(javascript_processor, create_temp_js):
    """Test error handling for various scenarios."""
    # Test non-existent file
    with pytest.raises(FileNotFoundError):
        javascript_processor.process_file("nonexistent.js")
    
    # Test invalid JavaScript with syntax error
    content = """
    class TestClass {
        constructor() {
            console.log('test'
        }
    }
    """
    js_file = create_temp_js(content)
    result = javascript_processor.process_file(str(js_file))
    assert len(result.errors) > 0
    
    # Check for validation errors
    validation_errors = [error for error in result.errors if 'unclosed' in error.lower() or 'missing' in error.lower()]
    assert len(validation_errors) > 0, "Should have validation errors"
    
    # Check for extraction errors
    extraction_errors = [error for error in result.errors if 'extraction failed' in error.lower()]
    assert len(extraction_errors) > 0, "Should have extraction errors"

def test_multiple_files_processing(javascript_processor, tmp_path):
    """Test processing multiple files."""
    def _create_temp_js_with_name(content: str, name: str) -> Path:
        js_file = tmp_path / name
        js_file.write_text(content)
        return js_file
    
    # Process first file
    content1 = """
    class File1Class {
        method1() {}
    }
    """
    file1 = _create_temp_js_with_name(content1, "file1.js")
    result1 = javascript_processor.process_file(str(file1))
    
    # Process second file
    content2 = """
    class File2Class {
        method2() {}
    }
    """
    file2 = _create_temp_js_with_name(content2, "file2.js")
    result2 = javascript_processor.process_file(str(file2))
    
    # Check results accumulation
    assert not javascript_processor.results_df.empty
    assert len(javascript_processor.results_df) == 4  # 2 classes + 2 methods
    
    # Check file paths
    file_paths = javascript_processor.results_df["filepath"].unique()
    assert len(file_paths) == 2
    
    # Check content from both files
    classes = javascript_processor.results_df[javascript_processor.results_df["processor_type"] == "class"]
    assert "File1Class" in classes["name"].values
    assert "File2Class" in classes["name"].values

def test_import_export_statements(javascript_processor, create_temp_js):
    """Test processing of import and export statements."""
    content = '''
    export * from "d3-array";
    import assert from "assert";
    import {readdir, readFile, stat} from "fs/promises";
    '''
    js_file = create_temp_js(content)
    result = javascript_processor.process_file(str(js_file))
    
    # Check for errors in processing
    assert not result.errors, f"Errors found: {result.errors}"

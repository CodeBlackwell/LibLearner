"""
Tests for the Python code parser.
"""

import textwrap
from pathlib import Path
import pytest
from code_extractor.parser import CodeParser

def test_parse_simple_function(test_files_dir):
    """Test parsing a simple function definition."""
    # Create a test file with a simple function
    code = textwrap.dedent('''
        def hello(name: str) -> str:
            """Say hello to someone."""
            return f"Hello, {name}!"
    ''')
    test_file = test_files_dir / "simple_function.py"
    test_file.write_text(code)
    
    # Parse the file
    parser = CodeParser()
    result = parser.parse_file(test_file)
    
    # Check the results
    assert len(result.functions) == 1
    func = result.functions[0]
    assert func.name == "hello"
    assert func.docstring == "Say hello to someone."
    assert func.parameters == [("name", "str")]
    assert func.return_type == "str"

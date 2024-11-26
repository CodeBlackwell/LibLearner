"""
Pytest configuration and shared fixtures.
"""

import os
import pytest
from pathlib import Path

@pytest.fixture
def test_files_dir():
    """Return the path to the test files directory."""
    return Path(os.path.dirname(__file__)) / "test_files"

@pytest.fixture(autouse=True)
def setup_test_files(test_files_dir):
    """Create test files directory if it doesn't exist."""
    test_files_dir.mkdir(exist_ok=True)
    yield
    # Cleanup can be added here if needed

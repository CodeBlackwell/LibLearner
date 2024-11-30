import pytest
from pathlib import Path
from liblearner.processors.json_processor import JSONProcessor, JSONProcessingResult

# Get the test files directory
TEST_FILES_DIR = Path(__file__).parent.parent / "test_files"

@pytest.fixture
def processor():
    """Fixture to create a JSON processor instance."""
    return JSONProcessor(debug=True)

@pytest.fixture
def config_json_path():
    """Fixture for the path to config.json test file."""
    return str(TEST_FILES_DIR / "config.json")

@pytest.fixture
def people_json_path():
    """Fixture for the path to people.json test file."""
    return str(TEST_FILES_DIR / "people.json")

def test_supported_types(processor):
    """Test that the processor supports correct MIME types."""
    supported_types = processor.get_supported_types()
    assert 'application/json' in supported_types
    assert 'text/json' in supported_types

def test_process_config_json(processor, config_json_path):
    """Test processing of a single-object JSON file."""
    result = processor.process_file(config_json_path)
    
    # Check basic result properties
    assert isinstance(result, JSONProcessingResult)
    assert result.is_valid()
    assert not result.errors
    
    # Check file info
    assert result.file_info['name'] == 'config.json'
    assert 'path' in result.file_info
    assert 'size' in result.file_info
    assert 'last_modified' in result.file_info
    
    # Check processed elements
    assert len(result.elements) == 1  # Single object
    element = result.elements[0]
    assert element['name'] == 'test-project'
    assert element['version'] == '1.0.0'
    assert element['settings.debug'] is True
    assert element['database.credentials.user'] == 'test_user'

def test_process_people_json(processor, people_json_path):
    """Test processing of a JSON array file."""
    result = processor.process_file(people_json_path)
    
    # Check basic result properties
    assert isinstance(result, JSONProcessingResult)
    assert result.is_valid()
    assert not result.errors
    
    # Check processed elements
    assert len(result.elements) == 3  # Three people objects
    
    # Check first person's data is correctly flattened
    person1 = result.elements[0]
    assert person1['name'] == 'Alice Smith'
    assert person1['age'] == 30
    assert person1['address.street'] == '123 Elm St'
    assert person1['address.city'] == 'Springfield'

def test_dataframe_creation(processor, people_json_path):
    """Test the creation and structure of the results DataFrame."""
    result = processor.process_file(people_json_path)
    df = processor.results_df
    
    # Check DataFrame structureliblearner/tests/test_files
    expected_columns = ['filepath', 'parent_path', 'order', 'name', 'content', 'props', 'processor_type']
    assert all(col in df.columns for col in expected_columns)
    
    # Check DataFrame content
    assert len(df) == 3  # Three people records
    assert df['processor_type'].iloc[0] == 'json'
    assert df['name'].iloc[0] == 'people.json'

def test_invalid_json_handling(processor, tmp_path):
    """Test handling of invalid JSON content."""
    # Create a temporary invalid JSON file
    invalid_file = tmp_path / "invalid.json"
    invalid_file.write_text("{invalid json content")
    
    result = processor.process_file(str(invalid_file))
    
    assert not result.is_valid()
    assert len(result.errors) > 0
    assert "Invalid JSON format" in result.errors[0]

def test_nested_json_flattening(processor):
    """Test the flattening of nested JSON structures."""
    nested_data = {
        "a": 1,
        "b": {
            "c": 2,
            "d": {
                "e": 3
            }
        },
        "f": [1, 2, {"g": 3}]
    }
    
    flattened = processor.to_csv(nested_data)
    assert len(flattened) == 1
    
    flat_dict = flattened[0]
    assert flat_dict['a'] == 1
    assert flat_dict['b.c'] == 2
    assert flat_dict['b.d.e'] == 3
    assert flat_dict['f.0'] == 1
    assert flat_dict['f.2.g'] == 3


def test_multiple_files_processing(processor, config_json_path, people_json_path):
    """Test processing multiple JSON files and result accumulation."""
    # Process first file (config.json)
    result1 = processor.process_file(config_json_path)
    initial_len = len(processor.results_df)
    
    # Process second file (people.json)
    result2 = processor.process_file(people_json_path)
    final_len = len(processor.results_df)
    
    # Check that both files were processed successfully
    assert result1.is_valid()
    assert result2.is_valid()
    assert not result1.errors
    assert not result2.errors
    
    # Check results accumulation in DataFrame
    assert final_len > initial_len
    assert final_len == initial_len + len(result2.elements)
    
    # Check file paths in results
    file_paths = processor.results_df["filepath"].unique()
    assert len(file_paths) == 2
    
    # Verify content from both files
    df = processor.results_df
    config_rows = df[df["name"] == "config.json"]
    people_rows = df[df["name"] == "people.json"]
    
    assert not config_rows.empty
    assert not people_rows.empty
    
    # Verify order is sequential
    assert df["order"].is_monotonic_increasing
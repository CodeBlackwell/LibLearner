## LibLearner Processor Development Guide

This guide provides detailed instructions for developing new file processors in LibLearner. Follow these guidelines to ensure your processor integrates seamlessly with the established architecture.

## Architecture Overview

LibLearner processors follow a consistent architecture:
1. Each processor inherits from the base `FileProcessor` class
2. Processors use a corresponding `ProcessingResult` class for type-safe results
3. Results are accumulated in a pandas DataFrame with standardized columns
4. The processor registry handles MIME type detection and processor routing

## Step-by-Step Processor Development

### 1. Create Processing Result Class

First, define a result class in `processing_result.py`:

```python
@dataclass
class YourProcessingResult(ProcessingResult):
    # Add type-specific fields
    elements: List[Dict] = field(default_factory=list)
    errors: List[str] = field(default_factory=list)
    file_info: Dict = field(default_factory=dict)
    
    def is_valid(self) -> bool:
        return True  # Define validation logic
```

### 2. Create Processor Class

Create your processor in `processors/your_processor.py`:

```python
class YourProcessor(FileProcessor):
    def __init__(self, debug: bool = False):
        super().__init__()
        self.debug = debug
        if self.debug:
            logger.setLevel(logging.DEBUG)
        
        # Define supported MIME types
        self.supported_types = {
            'your/mime-type',
            'alternative/mime-type'
        }
        
        # Initialize tracking variables
        self._all_results = []  # Store all results
        self._current_path = []  # Track AST path
        self._order_counter = 0  # Track element order
```

### 3. Implement Required Methods

Your processor must implement these methods:

#### a. get_supported_types()
```python
def get_supported_types(self) -> List[str]:
    """Return list of supported MIME types."""
    return list(self.supported_types)
```

#### b. process_file()
```python
def process_file(self, file_path: str) -> YourProcessingResult:
    """Process a file and extract structured information."""
    # Reset counters for new file
    self._order_counter = 0
    path = Path(file_path)
    result = YourProcessingResult()
    results_data = []

    # Add file metadata
    result.file_info = {
        'name': path.name,
        'path': str(path.absolute()),
        'size': path.stat().st_size,
        'last_modified': path.stat().st_mtime
    }

    # Process file contents
    try:
        content = path.read_text()
        # Parse and process content
        self._process_content(content, result, results_data, file_path)
    except Exception as e:
        result.errors.append(str(e))
        logger.error(f"Error processing {file_path}: {e}")

    # Create DataFrame
    if results_data:
        df = pd.DataFrame(results_data)
        df = df.rename(columns={'type': 'processor_type'})
        column_order = ['filepath', 'parent_path', 'order', 'name', 
                       'content', 'props', 'processor_type']
        self.results_df = df[column_order]

    return result
```

### 4. Implement Processing Logic

Develop methods to process your file type:

```python
def _process_content(self, content: str, result: YourProcessingResult, 
                    results_data: List[Dict], file_path: str) -> None:
    """Process file content and extract elements."""
    # Parse content (use appropriate parser for your file type)
    elements = your_parser.parse(content)
    
    for element in elements:
        self._order_counter += 1
        element_info = {
            'name': element.name,
            'type': element.type,  # Use specific types (class, function, etc.)
            'content': element.content,
            'props': str(element.properties),
            'filepath': file_path,
            'parent_path': self._get_current_path(),
            'order': self._order_counter
        }
        results_data.append(element_info)
```

### 5. DataFrame Structure

Ensure your processor outputs these standardized columns:
- `filepath`: Absolute path to the source file
- `parent_path`: Dot notation path showing element location
- `order`: Sequential order of element discovery
- `name`: Element name
- `content`: Actual code/content
- `props`: Element-specific properties as string
- `processor_type`: Type of element (class, function, etc.)

### 6. Best Practices

1. **Error Handling**
   - Catch and log all exceptions
   - Store errors in the result object
   - Continue processing when possible

2. **Path Tracking**
   - Maintain accurate parent paths
   - Use dot notation for nested elements
   - Update paths when entering/leaving scopes

3. **Type Information**
   - Use specific, descriptive type names
   - Be consistent with type naming
   - Document supported types

4. **Performance**
   - Process files efficiently
   - Minimize memory usage
   - Use appropriate data structures

### 7. Testing

Create tests in `tests/processors/`:
1. Test file type detection
2. Test element extraction
3. Test error handling
4. Test DataFrame structure
5. Test nested element handling

### 8. Registration

Register your processor in `bin/process_files`:

```python
registry.register_processor(YourProcessor())
```

## Example Processor Types

Common processor types include:
- Python (.py)
- JavaScript (.js)
- TypeScript (.ts)
- JSON (.json)
- YAML (.yml, .yaml)
- Markdown (.md)
- Jupyter Notebooks (.ipynb)

## Integration Checklist

✓ Processing result class defined  
✓ Processor class inherits FileProcessor  
✓ Supported MIME types declared  
✓ File processing logic implemented  
✓ Error handling in place  
✓ Path tracking implemented  
✓ Order tracking implemented  
✓ Standard DataFrame columns  
✓ Tests written  
✓ Processor registered

## Troubleshooting

Common issues and solutions:
1. **MIME Type Detection**: Ensure types match python-magic output
2. **Path Tracking**: Verify _current_path management
3. **DataFrame Structure**: Check column names and order
4. **Memory Usage**: Monitor result accumulation
5. **Performance**: Profile file processing

## Need Help?

1. Check the Python processor implementation
2. Review the processor registry
3. Examine test cases
4. Consult the development team

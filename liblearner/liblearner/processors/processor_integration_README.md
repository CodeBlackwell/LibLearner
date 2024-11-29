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

        # Validate content
        validation_errors = self._validate_content(content)
        if validation_errors:
            for error in validation_errors:
                result.errors.append(error)
                logger.warning(f"Validation error in {file_path}: {error}")

        # Continue processing even with validation errors
        self._process_content(content, result, results_data, file_path)
    except Exception as e:
        result.errors.append(str(e))
        logger.error(f"Error processing {file_path}: {e}")

    # Create DataFrame
    if results_data:
        df = pd.DataFrame(results_data)
        df = df.rename(columns={'type': 'processor_type'})
        column_order = ['filepath', 'parent_path', 'order', 'name', 'content', 'props', 'processor_type']
        df = df[column_order]

    # IMPORTANT: Concatenate with existing results
    if hasattr(self, 'results_df') and not self.results_df.empty:
        self.results_df = pd.concat([self.results_df, df], ignore_index=True)
    else:
        self.results_df = df

    return result
```

### 4. MIME Type Support

Proper MIME type support is critical for file detection. Follow these steps:

1. **Declare All MIME Types**:

```python
self.supported_types = {
    'text/x-yourtype',
    'application/x-yourtype',
    'text/x-alternative',
    'application/x-alternative'
}
```

2. **Update FileTypeDetector**:

   Ensure your file extensions are mapped in `file_processor.py`:

```python
self._extension_mime_types = {
    '.yourext': 'application/x-yourtype',
    '.altext': 'application/x-yourtype'
}
```

3. **Handle Empty Files**:

   Add extension handling for empty files:

```python
if ext in ['.yourext', '.altext']:
    return 'application/x-yourtype'
```

4. **Text File Handling**:

   Add handling for text/plain detection:

```python
elif ext in ['.yourext', '.altext']:
    mime_type = 'application/x-yourtype'
```

### 5. Results Management

Proper results management is essential:

1. **Initialize Results**:

```python
def __init__(self):
    super().__init__()
    self.results_df = pd.DataFrame()  # Empty DataFrame
```

2. **Empty File Handling**:

```python
# Create DataFrame with standard columns even for empty files
df = pd.DataFrame(results_data) if results_data else pd.DataFrame(columns=[
    'filepath', 'parent_path', 'order', 'name', 'content', 'props', 'processor_type'
])
```

3. **Accumulate Results**:

- Never overwrite `results_df`
- Always concatenate new results
- Preserve order of discovery
- Maintain consistent column structure
- Handle empty DataFrames properly

4. **Reset State**:

```python
def process_file(self, file_path: str):
    self._order_counter = 0  # Reset counter
    self._current_path = []  # Reset path tracking
```

5. **Track Order**:

```python
self._order_counter += 1
element_info['order'] = self._order_counter
```

### 6. Content Validation

Implement content validation to detect malformed elements:

```python
def _validate_content(self, content: str) -> List[str]:
    """Validate content for malformed elements."""
    errors = []
    
    # Example validation checks
    try:
        # Check for structural issues
        self._check_structure(content)
        
        # Check for malformed elements
        self._check_elements(content)
        
        # Check for unclosed elements
        self._check_unclosed_elements(content)
    except Exception as e:
        errors.append(f"Validation error: {str(e)}")
    
    return errors
```

### 7. Error Recovery

Implement strategies for handling and recovering from errors:

1. **Partial Processing**:
- Continue processing after encountering errors
- Mark problematic sections in results
- Provide detailed error context

2. **Error Categories**:
- Validation errors (malformed content)
- Processing errors (parsing failures)
- System errors (IO, memory, etc.)

3. **Error Reporting**:

```python
def _handle_error(self, error: Exception, context: str) -> Dict:
    """Create standardized error entry."""
    return {
        'error_type': type(error).__name__,
        'message': str(error),
        'context': context,
        'timestamp': datetime.now().isoformat()
    }
```

### 8. Common Pitfalls

1. **Results Overwriting**:

- ❌ `self.results_df = new_df`
- ✓ Use `pd.concat()` to append results

2. **MIME Type Mismatches**:

- ❌ Inconsistent MIME types across detection methods
- ✓ Align FileTypeDetector with processor's supported types

3. **State Management**:

- ❌ Forgetting to reset counters/trackers
- ✓ Reset all state at start of processing

4. **Missing Registration**:

- ❌ Processor not in __init__.py
- ❌ Processor not registered with registry
- ✓ Complete all registration steps

5. **Incomplete Error Handling**:

- ❌ Failing on recoverable errors
- ✓ Catch and log errors, continue processing

### 9. Implement Processing Logic

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

### 10. DataFrame Structure

Ensure your processor outputs these standardized columns:

- `filepath`: Absolute path to the source file
- `parent_path`: Dot notation path showing element location
- `order`: Sequential order of element discovery
- `name`: Element name
- `content`: Actual code/content
- `props`: Element-specific properties as string
- `processor_type`: Type of element (class, function, etc.)

### 11. Best Practices

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

### 12. Testing

Create tests in `tests/processors/`:

1. Test file type detection
2. Test element extraction
3. Test error handling
4. Test DataFrame structure
5. Test nested element handling

### 13. Registration

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

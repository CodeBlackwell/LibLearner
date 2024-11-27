# LibLearner Language Processor Implementation Guide

This guide provides a comprehensive checklist and examples for implementing new language processors in the LibLearner library. Follow these guidelines to ensure consistent implementation across different language processors.

## Implementation Checklist

### 1. Basic Setup
- [ ] Create a new processor class in `processors/` directory
- [ ] Define proper class inheritance
- [ ] Import required libraries
- [ ] Set up logging configuration

Example:
```python
import re
import os
import logging
from typing import List, Dict, Any, Set
from pathlib import Path

logger = logging.getLogger(__name__)

class JavaProcessor:
    """Processor for Java files.
    
    This processor extracts structured information from Java files, including:
    - Class and interface definitions
    - Method signatures
    - Import statements
    - Dependencies
    - Type information
    """
    def __init__(self, debug: bool = False):
        super().__init__()
        self.debug = debug
        if self.debug:
            logger.setLevel(logging.DEBUG)
```

### 2. MIME Type Support
- [ ] Define all supported MIME types in `__init__`
- [ ] Include both primary and alternative MIME types
- [ ] Register MIME types in `file_type_detector.py`
- [ ] Implement `get_supported_types()` method

Example:
```python
def __init__(self):
    self.supported_types = {
        'text/x-java',
        'text/java',
        'application/x-java'
    }

def get_supported_types(self):
    """Return list of supported MIME types."""
    return self.supported_types
```

### 3. Result Object
- [ ] Create a result class
- [ ] Define all necessary attributes

Example:
```python
class JavaProcessingResult:
    """Result object for Java processing."""
    def __init__(self):
        self.errors: List[str] = []
        self.file_info: Dict[str, Any] = {}
        self.classes: List[Dict] = []
        self.methods: List[Dict] = []
        self.imports: Set[str] = set()
        self.dependencies: Dict[str, str] = {}
        self.types: Dict[str, str] = {}
        self.structure: List[Dict] = []
```

### 4. Core Processing Methods
- [ ] Implement `process_file` method
- [ ] Create helper methods for different node types

Example:
```python
def process_file(self, file_path: str) -> JavaProcessingResult:
    """Process a Java file and extract structured information."""
    result = JavaProcessingResult()
    path = Path(file_path)
    
    # Set file info
    result.file_info = {
        'name': path.name,
        'path': str(path.absolute()),
        'size': path.stat().st_size,
        'last_modified': path.stat().st_mtime
    }
    
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
            
        # Process content
        self._process_content(content, result)
        
    except Exception as e:
        error_msg = f"Error processing file: {str(e)}"
        result.errors.append(error_msg)
        logger.error(error_msg)
    
    return result

def _process_content(self, content: str, result: JavaProcessingResult):
    """Process Java file content."""
    # Extract imports
    imports = self._extract_imports(content)
    result.imports.update(imports)
    
    # Extract classes
    classes = self._extract_classes(content)
    result.classes.extend(classes)
    
    # Extract methods
    methods = self._extract_methods(content)
    result.methods.extend(methods)
```

### 5. Language-Specific Extractors
- [ ] Implement regex patterns for common patterns
- [ ] Create extraction methods

Example:
```python
def _setup_patterns(self):
    """Initialize regex patterns."""
    self.import_pattern = re.compile(
        r'import\s+(?:static\s+)?([^\s;]+)(?:\s*;\s*)?'
    )
    self.class_pattern = re.compile(
        r'(?:public|private|protected)?\s*class\s+(\w+)(?:\s+extends\s+(\w+))?(?:\s+implements\s+([^{]+))?'
    )
    self.method_pattern = re.compile(
        r'(?:public|private|protected)?\s*(?:static\s+)?(?:<[^>]+>\s+)?(\w+)\s+(\w+)\s*\([^)]*\)'
    )

def _extract_imports(self, content: str) -> Set[str]:
    """Extract import statements."""
    imports = set()
    for match in self.import_pattern.finditer(content):
        imports.add(match.group(1))
    return imports
```

### 6. Data Structure Handling
- [ ] Implement proper type inference
- [ ] Handle nested structures
- [ ] Maintain path information

Example:
```python
def _analyze_types(self, node: Any, path: str = '') -> Dict[str, str]:
    """Analyze and record type information."""
    types = {}
    if isinstance(node, dict):
        types[path] = 'object'
        for key, value in node.items():
            new_path = f"{path}.{key}" if path else key
            types.update(self._analyze_types(value, new_path))
    elif isinstance(node, list):
        types[path] = 'array'
        for i, item in enumerate(node):
            new_path = f"{path}[{i}]"
            types.update(self._analyze_types(item, new_path))
    else:
        if path:
            types[path] = type(node).__name__
    return types
```

### 7. CSV Output Support
- [ ] Ensure consistent MIME type usage
- [ ] Implement data flattening
- [ ] Handle special characters

Example:
```python
def to_csv(self, data: Any, sep: str = '.') -> List[Dict]:
    """Convert processed data to CSV format."""
    if isinstance(data, list):
        rows = []
        for item in data:
            row = {}
            self._flatten_data(item, row, '', sep)
            if row:
                rows.append(row)
        return rows
    else:
        row = {}
        self._flatten_data(data, row, '', sep)
        return [row] if row else []

def _flatten_data(self, data: Any, current_row: Dict, prefix: str, sep: str = '.'):
    """Flatten nested data structures for CSV output."""
    if isinstance(data, dict):
        for key, value in data.items():
            new_prefix = f"{prefix}{sep}{key}" if prefix else key
            if isinstance(value, (dict, list)):
                self._flatten_data(value, current_row, new_prefix, sep)
            else:
                current_row[new_prefix] = str(value) if value is not None else ''
```

### 8. Error Handling
- [ ] Implement comprehensive error catching
- [ ] Add detailed error messages

Example:
```python
try:
    # Process file content
    pass
except UnicodeDecodeError as e:
    error_msg = f"File encoding error: {str(e)}"
    result.errors.append(error_msg)
    logger.error(error_msg)
except Exception as e:
    error_msg = f"Unexpected error: {str(e)}"
    result.errors.append(error_msg)
    logger.error(error_msg)
```

### 9. Testing
- [ ] Create test files
- [ ] Implement unit tests

Example:
```python
def test_java_processing(self):
    """Test Java file processing."""
    # Create test file
    with tempfile.TemporaryDirectory() as tmp_dir:
        test_file = Path(tmp_dir) / "test.java"
        with open(test_file, 'w') as f:
            f.write('''
                import java.util.List;
                import java.util.Map;
                
                public class TestClass {
                    private String name;
                    
                    public String getName() {
                        return name;
                    }
                }
            ''')
        
        # Process file
        processor = JavaProcessor()
        result = processor.process_file(str(test_file))
        
        # Validate results
        self.assertEqual(len(result.errors), 0)
        self.assertEqual(len(result.imports), 2)
        self.assertEqual(len(result.classes), 1)
        self.assertEqual(len(result.methods), 1)
```

## Integration Tips

1. **File Type Detection**:
```python
# In file_type_detector.py
MIME_TYPE_MAPPING = {
    '.java': 'text/x-java',
    '.py': 'text/x-python',
    '.yaml': 'text/x-yaml',
    # Add new mappings here
}
```

2. **Processor Registration**:
```python
# In file_processor.py
def _get_processor(self, mime_type: str):
    if mime_type in {'text/x-java', 'text/java'}:
        return JavaProcessor()
    elif mime_type in {'text/x-python', 'application/x-python'}:
        return PythonProcessor()
    # Add new processors here
```

## Best Practices

1. **Consistent MIME Types**
   - Use standard MIME types
   - Support multiple type variations
   - Document supported types

2. **Error Handling**
   - Catch specific exceptions
   - Provide detailed error messages
   - Log errors appropriately
   - Continue processing when possible

3. **Type Information**
   - Use type hints
   - Document parameter types
   - Validate input types

4. **Code Organization**
   - Keep methods focused
   - Use clear naming
   - Document complex logic
   - Follow existing patterns

5. **Testing**
   - Test edge cases
   - Validate all outputs
   - Test error conditions
   - Use realistic test data

## Performance Considerations

1. **Memory Usage**
   - Process large files in chunks
   - Clear temporary data structures
   - Use generators where appropriate

2. **Processing Speed**
   - Optimize regex patterns
   - Cache compiled patterns
   - Use efficient data structures

3. **Logging**
   - Use appropriate log levels
   - Enable debug logging when needed
   - Log performance metrics

## References

- [MIME Types Reference](https://www.iana.org/assignments/media-types/media-types.xhtml)
- [Python Regex Documentation](https://docs.python.org/3/library/re.html)
- [Python Type Hints](https://docs.python.org/3/library/typing.html)

# LibLearner

A Python library for extracting and analyzing code from various source files. LibLearner can extract functions, methods, classes, and other code elements from Python and JavaScript files, saving them in a structured format for further analysis.

## Prerequisites

- Python 3.7 or higher
- Node.js 14 or higher (for JavaScript processing)
- npm (Node.js package manager)

## Installation

1. Install Python package:
```bash
pip install liblearner
```

2. Install Node.js dependencies (required for JavaScript processing):
```bash
npm install
```

## Usage

### As a Command Line Tool

```bash
# Process a single file
extract_functions path/to/your/file.py -o output_dir
extract_functions path/to/your/file.js -o output_dir

# Process a directory
extract_functions path/to/your/directory -o output_dir

# Only extract global functions (Python only)
extract_functions path/to/your/file.py -o output_dir --globals-only

# Ignore specific directories
extract_functions path/to/your/directory -o output_dir --ignore-dirs tests docs
```

### As a Library

```python
from liblearner import extract_functions, process_file, process_directory

# Extract Python functions from source code
python_code = '''
def hello(name):
    return f"Hello, {name}!"
'''
functions = extract_functions(python_code, "example.py")

# Process a JavaScript file
from liblearner.processors.javascript_processor import JavaScriptProcessor
js_processor = JavaScriptProcessor()
js_result = js_processor.process_file("path/to/file.js")

# Process any file (auto-detects type)
functions = process_file("path/to/file")

# Process a directory
folder_functions = process_directory("path/to/directory")

# Write results to CSV
from liblearner import write_results_to_csv
write_results_to_csv(functions, "output.csv")
```

## Supported File Types

### Python Files (.py)
- Functions
- Methods
- Classes
- Lambda functions
- Nested functions
- Function docstrings

### JavaScript Files (.js)
- Functions
- Methods
- Classes
- Arrow functions
- Nested functions
- Constants
- Leading comments

### Jupyter Notebooks (.ipynb)
- Cell types (code, markdown, raw)
- Code execution order
- Cell outputs
- Cell metadata

## Output Format

### Python Output
The extracted Python functions are saved with the following information:
- Filename: Source file path
- Parent: Parent class name or "Global"
- Order: Order of appearance in the file
- Function/Method Name: Name of the function or method
- Parameters: List of parameter names
- Docstring: Function docstring if available
- Code: Complete function source code

### JavaScript Output
The extracted JavaScript elements include:
- Type: Element type (Function, Class, Constant)
- Name: Element name
- Code: Complete element source code
- Nesting Level: Depth in the code structure
- Parent Name: Name of the containing element
- Parameters: Function parameters (if applicable)
- Comments: Leading comments
- Order: Order of appearance

### Jupyter Output
The extracted notebook information includes:
- Cell Type: Code, markdown, or raw
- Source: Cell content
- Execution Count: For code cells
- Outputs: For code cells
- Metadata: Cell-specific metadata

## Development

### Running Tests

The test suite is located in the `tests` directory and uses Python's built-in unittest framework. To run the tests:

```bash
# Run all tests with verbose output
python -m unittest discover -s tests -v

# Run Python processor tests
python -m unittest tests/test_python_processor.py

# Run JavaScript processor tests
python -m unittest tests/test_javascript_processor.py

# Run Jupyter processor tests
python -m unittest tests/test_jupyter_processor.py
```

The test suite covers:
- File type detection
- Processor registration and handling
- Directory processing with ignore patterns
- Python code processing:
  - Simple functions
  - Class methods
  - Multiple functions
  - Nested functions
  - Invalid code
  - Empty files
- JavaScript code processing:
  - Functions and methods
  - Classes
  - Nested functions
  - Constants
  - Invalid code
- Jupyter notebook processing:
  - Code cells
  - Markdown cells
  - Raw cells
  - Cell metadata

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

This project is licensed under the MIT License - see the LICENSE file for details.

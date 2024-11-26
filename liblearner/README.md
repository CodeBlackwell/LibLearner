# LibLearner

A Python library for extracting and analyzing Python functions from source code. LibLearner can extract functions, methods, and lambdas from Python files and save them in a structured CSV format for further analysis.

## Installation

```bash
pip install liblearner
```

## Usage

### As a Command Line Tool

```bash
# Process a single file
extract_functions path/to/your/file.py -o output_dir

# Process a directory
extract_functions path/to/your/directory -o output_dir

# Only extract global functions
extract_functions path/to/your/file.py -o output_dir --globals-only

# Ignore specific directories
extract_functions path/to/your/directory -o output_dir --ignore-dirs tests docs
```

### As a Library

```python
from liblearner import extract_functions, process_file, process_directory

# Extract functions from a string of source code
source_code = '''
def hello(name):
    return f"Hello, {name}!"
'''
functions = extract_functions(source_code, "example.py")

# Process a single file
functions = process_file("path/to/file.py")

# Process a directory
folder_functions = process_directory("path/to/directory")

# Write results to CSV
from liblearner import write_results_to_csv
write_results_to_csv(functions, "output.csv")
```

## Output Format

The extracted functions are saved in CSV format with the following columns:
- Filename: Source file path
- Parent: Parent class name or "Global"
- Order: Order of appearance in the file
- Function/Method Name: Name of the function or method
- Parameters: List of parameter names
- Docstring: Function docstring if available
- Code: Complete function source code

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

This project is licensed under the MIT License - see the LICENSE file for details.

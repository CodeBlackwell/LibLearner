# LibLearner

A collection of tools and libraries for code analysis and learning.

## Projects

### Function Extractor (`liblearner`)

A Python library and CLI tool for extracting and analyzing code from various source files. The tool can extract functions, methods, classes, and other code elements from Python, JavaScript, Jupyter notebooks, and Markdown files, saving them in a structured format for further analysis.

### File Extension Scout (`scout_extensions`)

A streamlined command-line tool for analyzing file extensions in a directory tree. Features include:
- Recursive directory traversal
- Frequency-based sorting
- Configurable directory exclusions
- Empty extension filtering
- Cross-platform compatibility

## Processors

### Currently Supported File Types

- **Python** (.py): Functions, classes, methods, and docstrings
- **JavaScript** (.js): Functions, classes, methods, and JSDoc comments
- **Jupyter** (.ipynb): Code cells, markdown cells, and outputs
- **Markdown** (.md): Headers, code blocks, lists, links, tables, and metadata

#### Quick Start

```bash
# Install Python package
cd liblearner
pip install -e .

# Install Node.js dependencies (required for JavaScript processing)
npm install

# Use the CLI tools
extract_functions path/to/your/code -o output_dir  # Extract code elements
scout_extensions path/to/directory --sort          # List file extensions by frequency
scout_extensions path/to/directory --no-empty      # Skip files without extensions
scout_extensions path/to/directory --ignore-dirs node_modules,dist  # Exclude directories
```

For more details, see the [liblearner README](liblearner/README.md).

## Repository Structure

```
LibLearner/
├── liblearner/           # Code extraction library
│   ├── liblearner/      # Core library code
│   │   ├── processors/  # Language-specific processors
│   │   ├── extractors/  # Language-specific extractors
│   │   └── scout/       # File analysis tools
│   ├── bin/             # CLI tools
│   ├── tests/           # Test suite
│   ├── setup.py         # Package configuration
│   ├── package.json     # Node.js dependencies
│   └── README.md        # Library documentation
├── LICENSE              # Project license
└── README.md           # This file
```

## Development

### Prerequisites

- Python 3.7 or higher
- Node.js 14 or higher (for JavaScript processing)
- npm (Node.js package manager)

### Installation

1. Install Python dependencies:
```bash
cd liblearner
pip install -e .
```

2. Install Node.js dependencies:
```bash
npm install
```

### Running Tests

The test suite is located in the `liblearner/tests` directory. To run the tests:

```bash
cd liblearner
python -m unittest discover -s tests -v
```

Alternative test commands:

```bash
# Run specific processor tests
python -m unittest tests/test_python_processor.py
python -m unittest tests/test_javascript_processor.py
python -m unittest tests/test_jupyter_processor.py
python -m unittest tests/test_markdown_processor.py

# Run scout tools tests
python -m unittest tests/test_scout_extensions.py

# Run a specific test class
python -m unittest tests.test_python_processor.TestPythonProcessor

# Run a specific test method
python -m unittest tests.test_python_processor.TestPythonProcessor.test_supported_types
```

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

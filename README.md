# LibLearner

A collection of tools and libraries for code analysis and learning.

## Projects

### Function Extractor (`liblearner`)

A Python library and CLI tool for extracting and analyzing Python functions from source code. The tool can extract functions, methods, and lambdas from Python files and save them in a structured CSV format for further analysis.

#### Quick Start

```bash
# Install the package
cd liblearner
pip install -e .

# Use the CLI tool
extract_functions path/to/your/code -o output_dir
```

For more details, see the [liblearner README](liblearner/README.md).

## Repository Structure

```
LibLearner/
├── liblearner/           # Python function extraction library
│   ├── liblearner/      # Core library code
│   ├── bin/             # CLI tools
│   ├── tests/           # Test suite
│   ├── setup.py         # Package configuration
│   └── README.md        # Library documentation
├── LICENSE              # Project license
└── README.md           # This file
```

## Development

### Running Tests

The test suite is located in the `liblearner/tests` directory. To run the tests:

```bash
cd liblearner
python -m unittest discover -s tests -v
```

Alternative test commands:

```bash
# Run a specific test file
python -m unittest tests/test_python_processor.py

# Run a specific test class
python -m unittest tests.test_python_processor.TestPythonProcessor

# Run a specific test method
python -m unittest tests.test_python_processor.TestPythonProcessor.test_supported_types
```

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

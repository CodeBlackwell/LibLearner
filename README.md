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
│   ├── setup.py         # Package configuration
│   └── README.md        # Library documentation
├── LICENSE              # Project license
└── README.md           # This file
```

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

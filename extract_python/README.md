# Python Code Analysis Library

A comprehensive Python library for analyzing and extracting information from Python codebases, with a focus on code structure analysis and metrics collection using DataFrame-based tree structures.

## Features

- **Code Analysis**: Analyze Python code to extract various metrics and structural information
- **Function Extraction**: Extract and analyze function definitions from Python files
- **Data Structure Analysis**: Identify and analyze data structures in Python code
- **DataFrame Tree Processing**: Organize and analyze code metrics using tree-structured DataFrames
- **Documentation Generation**: Generate documentation from analyzed code structures
- **Flexible Output**: Support for both DataFrame and CSV output formats
- **Configurable Analysis**: Customizable analysis settings through configuration classes

## Installation

Clone the repository and include it in your Python path:

```bash
git clone <repository-url>
cd extract_python
pip install -r requirements.txt
```

## Requirements

- Python 3.7+
- pandas
- pathlib
- typing-extensions (for Python < 3.8)

## Usage

### Basic Usage

```python
from extract_python import CodeAnalyzer, AnalyzerConfig, OutputConfig

# Create configuration
config = AnalyzerConfig(
    excluded_directories=['venv', 'node_modules']
)

# Configure output settings
output_config = OutputConfig(
    output_format='csv',
    output_directory='analysis_results'
)

# Initialize and run analyzer
analyzer = CodeAnalyzer(
    input_path="path/to/code",
    config=config,
    output_config=output_config
)

# Run analysis
results = analyzer.analyze()
```

### Custom Configuration

```python
from extract_python import AnalyzerConfig

# Create custom configuration
config = AnalyzerConfig(
    excluded_directories=[
        'venv',
        'node_modules',
        '.git',
        '__pycache__'
    ],
    csv_output_dir='custom/output/path'
)
```

### Output Configuration

```python
from extract_python import OutputConfig
from pathlib import Path

output_config = OutputConfig(
    output_format='csv',  # or 'dataframe'
    csv_filename_template='{name}_analysis.csv',
    output_directory=Path('analysis_results')
)
```

## Architecture

### Core Components

- `code_analyzer.py`: Main analysis orchestration
- `dataframe_tree.py`: Tree structure implementation using DataFrames
- `config.py`: Configuration management
- `exceptions.py`: Custom exception handling

### Configuration

The library uses two main configuration classes:

1. `AnalyzerConfig`:
   - Manages analysis settings
   - Controls directory exclusions
   - Configures output paths

2. `OutputConfig`:
   - Controls output format (DataFrame/CSV)
   - Manages output file naming
   - Handles output directory settings

### Error Handling

Custom exceptions for better error management:

- `CodeAnalysisError`: Base exception class
- `InvalidPathError`: Path-related errors
- `DataFrameGenerationError`: DataFrame processing errors
- `OutputError`: Output generation errors
- `ConfigurationError`: Configuration-related errors

## Development

### Running Tests

```bash
python -m pytest tests/
```

### Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests for new functionality
5. Submit a pull request

### Code Style

This project follows PEP 8 guidelines. Ensure your code is formatted accordingly:

```bash
black .
flake8 .
```

## License

[Add appropriate license information]

## Support

For issues and feature requests, please use the GitHub issue tracker.

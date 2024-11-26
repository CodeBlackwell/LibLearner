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

## 🔍 Processors

LibLearner includes several specialized processors for different file types:

### Markdown Processor
- Comprehensive Markdown file analysis
- Headers and hierarchy extraction
- Code blocks with language detection
- Lists, links, and references
- Tables and formatting
- YAML frontmatter parsing
- Table of Contents generation

### MDX Processor
- JSX component extraction and analysis
- Import/export module tracking
- Layout and theme detection
- Frontmatter parsing
- Component props analysis
- Markdown feature support
- Interactive component detection
- Next.js and React integration

### YAML Processor
- Rich YAML document analysis
- Environment variable detection
- Service configuration parsing
- API configuration extraction
- URL identification
- Type and schema inference
- Dependency tracking
- Multi-document support
- Docker and Kubernetes config analysis

### Python Processor
- Functions, classes, methods, and docstrings
- Type hinting and annotation support
- Decorator detection and parsing
- Lambda functions and closures
- Context manager analysis
- Import and export tracking

### JavaScript Processor
- Functions, classes, methods, and JSDoc comments
- ES6+ syntax support
- Module import and export analysis
- Async/await and promise handling
- Class and inheritance analysis
- Decorator detection and parsing

### Jupyter Processor
- Code cells, markdown cells, and outputs
- Notebook structure and hierarchy analysis
- Cell metadata and tags
- Output analysis and visualization
- Interactive shell and kernel support

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

## 🛣️ Processor Roadmap

### Completed Processors
- ✅ **Markdown Processor**: Full Markdown syntax support with frontmatter
- ✅ **YAML Processor**: Configuration analysis with environment and service detection
- ✅ **Python Processor**: Python code analysis with type hints and docstrings
- ✅ **JavaScript Processor**: Modern JavaScript/ES6+ analysis
- ✅ **Jupyter Processor**: Notebook cell and output analysis
- ✅ **MDX Processor**: JSX in Markdown with component and module analysis

### In Development
- 🚧 **RST Processor**: Next priority
  - reStructuredText parsing
  - Sphinx directives
  - Documentation roles
  - Cross-reference system
  - Table of contents
  - Directive extensions
  - Theme compatibility
  - Documentation generation

### Planned Processors
- 📋 **JSONL Processor**
  - Line-by-line JSON parsing
  - Schema inference
  - Data validation
  - Streaming support
  - Type detection
  - Data statistics
  - Error recovery
  - Bulk processing

- 📋 **Properties/CONF Processor**
  - Configuration key-value parsing
  - Environment variable support
  - Include directive handling
  - Hierarchical config support
  - Variable interpolation
  - Conditional sections
  - Multi-environment configs
  - Import resolution

### Future Considerations
- 💡 **TOML Processor**: Modern config file format
  - Table support
  - Array of tables
  - Inline tables
  - Key-value pairs
  - Data types
  - DateTime handling

- 💡 **TypeScript Processor**: Static typing and interfaces
  - Type definitions
  - Interface analysis
  - Generic support
  - Decorator analysis
  - Module resolution
  - JSX/TSX support

- 💡 **GraphQL Processor**: Schema and query analysis
  - Schema validation
  - Query parsing
  - Type system
  - Directives
  - Fragments
  - Mutations/Subscriptions

- 💡 **XML/HTML Processor**: Markup and DOM analysis
  - Element hierarchy
  - Attribute extraction
  - Namespace support
  - XPath queries
  - XSLT templates
  - DTD validation

- 💡 **CSV/TSV Processor**: Tabular data analysis
  - Header detection
  - Type inference
  - Delimiter handling
  - Quoted fields
  - Escape sequences
  - Data validation

### Integration Goals
- 🎯 Cross-processor reference tracking
  - File dependencies
  - Symbol resolution
  - Import graphs
  - Type relationships

- 🎯 Unified type system
  - Common type representation
  - Type conversion
  - Schema validation
  - Type inference

- 🎯 Dependency graph generation
  - Module dependencies
  - Type dependencies
  - File relationships
  - Circular detection

- 🎯 Documentation cross-linking
  - Symbol linking
  - API references
  - Code examples
  - Version tracking

- 🎯 Schema validation framework
  - JSON Schema
  - XML Schema
  - Custom validators
  - Error reporting

### Performance Goals
- 🚀 Parallel processing
- 🚀 Incremental analysis
- 🚀 Caching system
- 🚀 Memory optimization
- 🚀 Large file handling

### Security Goals
- 🔒 Safe parsing
- 🔒 Input validation
- 🔒 Resource limits
- 🔒 Sandbox execution
- 🔒 Credential detection

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

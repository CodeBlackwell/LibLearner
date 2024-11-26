# LibLearner

A Python library for extracting and analyzing code from various source files. LibLearner can extract functions, methods, classes, and other code elements from Python, JavaScript, Jupyter notebooks, and Markdown files, saving them in a structured format for further analysis.

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

### Command Line Tools

#### Code Extraction Tool

```bash
# Process a single file
process_files path/to/your/file.py -o output_dir
process_files path/to/your/file.js -o output_dir
process_files path/to/your/file.md -o output_dir

# Process a directory
process_files path/to/your/directory -o output_dir

# Only extract global functions (Python only)
process_files path/to/your/file.py -o output_dir --globals-only

# Ignore specific directories
process_files path/to/your/directory -o output_dir --ignore-dirs tests docs
```

#### File Extension Scout

```bash
# List file extensions with their frequency
scout_extensions /path/to/directory

# Sort extensions by frequency
scout_extensions /path/to/directory --sort

# Skip files without extensions
scout_extensions /path/to/directory --no-empty

# Ignore specific directories
scout_extensions /path/to/directory --ignore-dirs build dist node_modules

# Combine options
scout_extensions /path/to/directory --sort --no-empty --ignore-dirs build dist
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

# Process a Markdown file
from liblearner.processors.markdown_processor import MarkdownProcessor
md_processor = MarkdownProcessor()
md_result = md_processor.process_file("path/to/file.md")

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

### Markdown Files (.md)
- Headers and their hierarchy
- Code blocks with language information
- Inline code snippets
- Lists (ordered and unordered)
- Links and references
- Blockquotes
- Tables
- Emphasized and strong text
- YAML frontmatter metadata
- Table of contents
- File metadata

### YAML Files (.yml, .yaml)
- Document structure
- Environment variables
- Service definitions
- API configurations
- Database settings
- Cache configurations
- URL extraction and validation
- Dependency version tracking
- Credential placeholder detection
- Safe YAML loading

### MDX Files (.mdx)
- JSX components
- Module analysis
- Markdown features
- Metadata

## 📦 Processors

### YAML Processor

The YAML processor provides comprehensive analysis of YAML files, particularly useful for configuration files, service definitions, and infrastructure specifications.

#### Features
- **Document Analysis**
  - Multi-document support
  - Nested structure parsing
  - Type inference
  - Schema detection

- **Configuration Detection**
  - Environment variables (`${VAR}` and `$VAR` syntax)
  - Service definitions (Docker, Kubernetes)
  - API configurations
  - Database settings
  - Cache configurations

- **Security & Dependencies**
  - URL extraction and validation
  - Dependency version tracking
  - Credential placeholder detection
  - Safe YAML loading

#### Usage Example
```python
from liblearner.processors import YAMLProcessor

# Initialize processor
processor = YAMLProcessor()

# Process a YAML file
result = processor.process_file('docker-compose.yml')

# Access extracted information
env_vars = result['env_vars']  # List of environment variables
services = result['services']  # Service configurations
urls = result['urls']  # List of URLs
types = result['types']  # Type information
schemas = result['schemas']  # Schema information
```

#### Output Format
```python
{
    'documents': [...],  # List of YAML documents
    'structure': {...},  # Document structure
    'env_vars': [...],   # Environment variables
    'urls': [...],       # URLs found
    'services': {...},   # Service configurations
    'api_configs': {...},# API configurations
    'dependencies': {...},# Dependencies
    'types': {...},      # Type information
    'schemas': {...},    # Schema information
    'errors': [...],     # Any parsing errors
    'file_info': {...}   # File metadata
}
```

### Markdown Processor

The Markdown processor extracts various elements from Markdown files, including headers, code blocks, lists, links, and more.

#### Features
- **Header Analysis**
  - Header hierarchy
  - Header text and level

- **Code Blocks**
  - Code language detection
  - Code block content

- **Lists and Links**
  - Ordered and unordered lists
  - List items
  - Links and references

- **Tables and Blockquotes**
  - Table rows and columns
  - Blockquotes

- **Text Formatting**
  - Emphasized and strong text
  - Inline code snippets

- **Metadata**
  - YAML frontmatter metadata
  - Table of contents
  - File metadata

#### Usage Example
```python
from liblearner.processors import MarkdownProcessor

# Initialize processor
processor = MarkdownProcessor()

# Process a Markdown file
result = processor.process_file('README.md')

# Access extracted information
headers = result['headers']  # List of headers
code_blocks = result['code_blocks']  # List of code blocks
lists = result['lists']  # List of lists
links = result['links']  # List of links
tables = result['tables']  # List of tables
```

#### Output Format
```python
{
    'headers': [...],  # List of headers
    'code_blocks': [...],  # List of code blocks
    'lists': [...],  # List of lists
    'links': [...],  # List of links
    'tables': [...],  # List of tables
    'blockquotes': [...],  # List of blockquotes
    'emphasized_text': [...],  # List of emphasized text
    'strong_text': [...],  # List of strong text
    'metadata': {...},  # YAML frontmatter metadata
    'toc': [...],  # Table of contents
    'file_info': {...}  # File metadata
}
```

### MDX Processor

The MDX processor provides comprehensive analysis of MDX files, combining Markdown processing capabilities with JSX component extraction and module analysis.

#### Features
- **JSX Components**
  - Component detection and extraction
  - Props analysis
  - Layout components
  - Component hierarchy

- **Module Analysis**
  - Import statements
  - Default and named exports
  - Component exports
  - Module dependencies

- **Markdown Features**
  - Headers and content
  - Code blocks with language detection
  - Lists and links
  - Text formatting

- **Metadata**
  - YAML frontmatter
  - Date handling
  - Layout configuration
  - Theme settings

#### Usage Example
```python
from liblearner.processors import MDXProcessor

# Initialize processor
processor = MDXProcessor()

# Process an MDX file
result = processor.process_file('blog-post.mdx')

# Access extracted information
components = result['components']  # List of JSX components
exports = result['exports']       # List of exports
imports = result['imports']       # List of imports
frontmatter = result['frontmatter']  # Frontmatter data
layout = result['layout']        # Layout configuration
```

#### Example MDX File
```mdx
---
title: My Blog Post
layout: BlogPost
date: 2023-12-25
---

import { Button } from '@components/Button'
import { Card } from '@components/Card'

export const metadata = {
  title: 'Dynamic Title',
  description: 'Page description'
}

<Button variant="primary">Click Me</Button>

<Card>
  ## Card Title
  Some content inside a card component
</Card>

# Main Content

Regular markdown content with **bold** and *italic* text.

export default ({ children }) => <BlogLayout>{children}</BlogLayout>
```

#### Output Format
```python
{
    'components': ['Button', 'Card', 'BlogLayout'],  # JSX components
    'exports': ['metadata', 'default'],              # Exported items
    'imports': ['@components/Button', '@components/Card'], # Imported modules
    'frontmatter': {                                # Frontmatter data
        'title': 'My Blog Post',
        'layout': 'BlogPost',
        'date': '2023-12-25'
    },
    'layout': 'BlogPost',                          # Layout configuration
    'content': '...',                              # Full MDX content
    'file_info': {                                 # File metadata
        'name': 'blog-post.mdx',
        'path': '/path/to/blog-post.mdx',
        'size': 1234,
        'modified': 1703520000
    },
    'errors': []                                   # Any parsing errors
}
```

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

### Markdown Output
The extracted Markdown information includes:
- Headers: List of (level, text) tuples
- Code Blocks: List of (language, code) tuples
- Inline Code: List of code snippets
- Lists: List of list items
- Links: List of (text, url) tuples
- Blockquotes: List of quoted text
- Tables: List of table rows
- Emphasized Text: List of italic text
- Strong Text: List of bold text
- Metadata: Dictionary of YAML frontmatter
- ToC: List of headers with levels and slugs
- File Info: Name, path, size, last modified

## Development

### Running Tests

The test suite is located in the `tests` directory and uses Python's built-in unittest framework. To run the tests:

```bash
# Run all tests with verbose output
python -m unittest discover -s tests -v

# Run specific processor tests
python -m unittest tests/test_python_processor.py
python -m unittest tests/test_javascript_processor.py
python -m unittest tests/test_jupyter_processor.py
python -m unittest tests/test_markdown_processor.py

# Run scout tools tests
python -m unittest tests/test_scout_extensions.py
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
- Markdown processing:
  - Headers and hierarchy
  - Code blocks and languages
  - Lists and links
  - Tables and blockquotes
  - Text formatting
  - Metadata extraction
- File extension analysis:
  - Directory traversal
  - Extension counting
  - Directory exclusion
  - Empty extension handling

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

This project is licensed under the MIT License - see the LICENSE file for details.

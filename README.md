# 🎓 LibLearner

> Train your own T5 model on any codebase with powerful code extraction and processing tools.

<div align="center">

[![Python Version](https://img.shields.io/badge/python-3.7%2B-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Code Style: Black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)

</div>

## 🎯 Purpose

LibLearner is a comprehensive toolkit designed to help you create custom T5 models trained on specific codebases. It extracts, processes, and prepares code from various sources, making it easy to train specialized code understanding and generation models.

## ✨ Key Features

- 🔍 **Universal Code Extraction**: Process any codebase or GitHub repository
- 📊 **Multi-Format Support**: Handle Python, JavaScript, Jupyter notebooks, and more
- 🤖 **T5 Training Ready**: Structured output perfect for fine-tuning T5 models
- 🔄 **Batch Processing**: Process entire repositories or directories at once
- 📈 **Rich Analysis**: Extract functions, classes, docstrings, and more
- 🌐 **GitHub Integration**: Direct processing of GitHub repositories

## 🚀 Quick Start

```bash
# Install LibLearner
pip install -e .

# Process a GitHub repository
process_files https://github.com/user/repo -o ./training_data

# Process local files
process_files ./my_codebase -o ./training_data

# Extract with detailed logging
process_files -v ./src --ignore-dirs tests,docs
```

## 🛠️ Core Tools

### 1. File Processor (`process_files`)

Our main utility for code extraction and analysis:

```bash
process_files [-h] [-o OUTPUT] [--ignore-dirs [DIRS...]] [-v] [--temp-dir DIR] input_paths...
```

**Features:**
- 🔄 Batch processing of files and directories
- 🌐 Direct GitHub repository processing
- 📊 CSV output for structured data
- ⚙️ Configurable processing options
- 📝 Comprehensive error reporting

### 2. Function Extractor (`extract_functions`)

Specialized tool for function-level extraction:

```bash
extract_functions path/to/code -o output_dir
```

### 3. Extension Scout (`scout_extensions`)

Analyze file types in your codebase:

```bash
scout_extensions path/to/directory --sort
```

## 📝 Supported File Types

| Type | Extension | Features |
|------|-----------|----------|
| Python | `.py` | Functions, classes, type hints, docstrings |
| JavaScript | `.js` | Functions, classes, JSDoc, ES6+ syntax |
| Jupyter | `.ipynb` | Code cells, markdown, outputs |
| Markdown | `.md` | Headers, code blocks, documentation |
| YAML | `.yml/.yaml` | Configurations, schemas |
| JSON | `.json` | Data structures, configs |
| Shell | `.sh` | Scripts, commands |

## 🔧 Processors

LibLearner includes specialized processors for each file type:

### Current Processors
- ✅ **Python Processor**: Full language feature support
- ✅ **JavaScript Processor**: Modern JS/ES6+ analysis
- ✅ **Jupyter Processor**: Notebook analysis
- ✅ **Markdown Processor**: Documentation parsing
- ✅ **YAML Processor**: Configuration analysis
- ✅ **MDX Processor**: JSX in Markdown support

### Coming Soon
- 🚧 **RST Processor**: Documentation processing
- 📋 **JSONL Processor**: Streaming data handling
- 📋 **TypeScript Processor**: Static typing support

## 🎯 T5 Training Pipeline

1. **Extract Code**
   ```bash
   process_files your/codebase -o training_data
   ```

2. **Prepare Dataset**
   ```bash
   prepare_t5_dataset training_data -o t5_ready
   ```

3. **Train Model**
   ```bash
   train_t5_model t5_ready -o trained_model
   ```

## 📚 Documentation

For detailed documentation, visit our [documentation site](docs/).

## 🤝 Contributing

We welcome contributions! See our [Contributing Guide](CONTRIBUTING.md) for details.

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

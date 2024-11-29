import os
import pytest
import pandas as pd
import json
from pathlib import Path
from liblearner.processors.markdown_processor import MarkdownProcessor
from liblearner.processing_result import MarkdownProcessingResult

TEST_FILES_DIR = Path(__file__).parent.parent / "test_files"

@pytest.fixture
def markdown_processor():
    return MarkdownProcessor(debug=True)  # Enable debug mode for better error messages

@pytest.fixture
def example_md_path():
    return TEST_FILES_DIR / "example.md"

@pytest.fixture
def example_mdx_path():
    return TEST_FILES_DIR / "example.mdx"

@pytest.fixture
def create_temp_md(tmp_path):
    def _create_temp_md(content: str) -> Path:
        md_file = tmp_path / "test.md"
        md_file.write_text(content)
        return md_file
    return _create_temp_md

def test_markdown_processor_initialization(markdown_processor):
    """Test the initialization of the markdown processor."""
    assert markdown_processor is not None
    assert isinstance(markdown_processor, MarkdownProcessor)
    assert hasattr(markdown_processor, 'results_df')
    assert isinstance(markdown_processor.results_df, pd.DataFrame)
    assert markdown_processor.results_df.empty
    
    # Check pattern initialization
    assert hasattr(markdown_processor, 'patterns')
    required_patterns = ['header', 'code_block', 'jsx_component', 'list_item', 
                        'ordered_list', 'link', 'blockquote', 'table']
    for pattern in required_patterns:
        assert pattern in markdown_processor.patterns

def test_supported_mime_types(markdown_processor):
    """Test the supported MIME types."""
    mime_types = markdown_processor.get_supported_types()
    assert isinstance(mime_types, list)
    assert len(mime_types) == 3
    assert "text/markdown" in mime_types
    assert "text/x-markdown" in mime_types
    assert "text/mdx" in mime_types

def test_process_markdown_file(markdown_processor, example_md_path):
    """Test processing a complete markdown file."""
    result = markdown_processor.process_file(str(example_md_path))
    
    assert isinstance(result, MarkdownProcessingResult)
    df = result.to_dataframe()
    assert isinstance(df, pd.DataFrame)
    assert not df.empty
    
    # Check metadata
    assert result.metadata["title"] == "Example Markdown"
    assert result.metadata["author"] == "LibLearner Team"
    assert len(result.metadata["tags"]) == 2
    assert "documentation" in result.metadata["tags"]
    assert "test" in result.metadata["tags"]
    
    # Check DataFrame structure
    required_columns = ["filepath", "parent_path", "order", "name", 
                       "content", "props", "processor_type"]
    for col in required_columns:
        assert col in df.columns
        assert not df[col].isna().any(), f"Found NaN values in column {col}"
    
    # Verify order is sequential
    orders = df["order"].tolist()
    assert orders == sorted(orders), "Order is not sequential"
    assert len(set(orders)) == len(orders), "Duplicate order values found"

def test_markdown_headers(markdown_processor, create_temp_md):
    """Test processing of markdown headers with different levels."""
    content = """# Header 1
## Header 2
### Header 3
#### Header 4
##### Header 5
###### Header 6"""
    md_file = create_temp_md(content)
    
    result = markdown_processor.process_file(str(md_file))
    df = result.to_dataframe()
    
    headers = df[df["processor_type"] == "header"]
    assert len(headers) == 6, "Not all header levels were processed"
    
    # Check header levels
    levels = [json.loads(props)["level"] for props in headers["props"]]
    assert levels == [1, 2, 3, 4, 5, 6], "Header levels are incorrect"
    
    # Check header content
    contents = headers["content"].tolist()
    expected_contents = [f"Header {i}" for i in range(1, 7)]
    assert contents == expected_contents, "Header contents are incorrect"
    
    # Check order is preserved
    assert headers["order"].tolist() == sorted(headers["order"].tolist())

def test_markdown_code_blocks(markdown_processor, create_temp_md):
    """Test processing of code blocks with different languages and inline code."""
    content = '''```python
def hello():
    print("Hello")
```
`inline code`
```javascript
console.log("test");
```
```
no language specified
```'''
    md_file = create_temp_md(content)
    
    result = markdown_processor.process_file(str(md_file))
    df = result.to_dataframe()
    
    code_blocks = df[df["processor_type"] == "code_block"]
    assert len(code_blocks) == 3, "Not all code blocks were processed"
    
    # Check language detection
    languages = [json.loads(props)["language"] for props in code_blocks["props"]]
    assert "python" in languages, "Python code block not detected"
    assert "javascript" in languages, "JavaScript code block not detected"
    assert "text" in languages, "Unlanguaged code block should default to 'text'"
    
    # Check code content
    python_block = code_blocks[code_blocks["props"].str.contains("python")].iloc[0]
    assert "def hello" in python_block["content"]
    assert "print" in python_block["content"]

def test_markdown_lists(markdown_processor, create_temp_md):
    """Test processing of ordered and unordered lists with nested items."""
    content = """- Item 1
  - Nested 1.1
  - Nested 1.2
- Item 2
1. First
2. Second
   1. Nested 2.1
   2. Nested 2.2
3. Third"""
    md_file = create_temp_md(content)
    
    result = markdown_processor.process_file(str(md_file))
    df = result.to_dataframe()
    
    list_items = df[df["processor_type"] == "list_item"]
    assert len(list_items) == 9, "Not all list items were processed"
    
    # Check list types
    unordered = list_items[list_items["props"].apply(lambda x: not json.loads(x)["ordered"])]
    ordered = list_items[list_items["props"].apply(lambda x: json.loads(x)["ordered"])]
    
    assert len(unordered) == 4, "Incorrect number of unordered list items"
    assert len(ordered) == 5, "Incorrect number of ordered list items"
    
    # Check content preservation
    assert "Item 1" in list_items["content"].values
    assert "Nested 1.1" in list_items["content"].values
    assert "First" in list_items["content"].values
    assert "Nested 2.1" in list_items["content"].values

def test_markdown_links(markdown_processor, create_temp_md):
    """Test processing of different types of links."""
    content = """[Basic Link](https://example.com)
[Link with Title](https://test.com "Test Title")
[Reference Link][ref]
<https://direct.com>

[ref]: https://reference.com"""
    md_file = create_temp_md(content)
    
    result = markdown_processor.process_file(str(md_file))
    df = result.to_dataframe()
    
    links = df[df["processor_type"] == "link"]
    assert len(links) >= 4, "Not all links were processed"
    
    # Check URLs
    urls = links["content"].tolist()
    assert "https://example.com" in urls
    assert "https://test.com" in urls
    assert "https://reference.com" in urls
    assert "https://direct.com" in urls
    
    # Check link texts
    texts = [json.loads(props)["text"] for props in links["props"]]
    assert "Basic Link" in texts
    assert "Link with Title" in texts

def test_mdx_components(markdown_processor, example_mdx_path):
    """Test processing of MDX-specific components and imports."""
    result = markdown_processor.process_file(str(example_mdx_path))
    df = result.to_dataframe()
    
    # Check imports
    imports = df[df["processor_type"] == "import"]
    assert not imports.empty, "No imports detected"
    assert any("Button" in str(content) for content in imports["content"])
    assert any("Card" in str(content) for content in imports["content"])
    
    # Check JSX components
    jsx_components = df[df["processor_type"] == "jsx_component"]
    assert not jsx_components.empty, "No JSX components detected"
    
    # Check specific components
    buttons = jsx_components[jsx_components["name"] == "Button"]
    assert not buttons.empty, "Button component not detected"
    
    cards = jsx_components[jsx_components["name"] == "Card"]
    assert not cards.empty, "Card component not detected"
    
    # Check component content
    button_content = buttons.iloc[0]["content"]
    assert "Click Me" in button_content
    assert "variant=" in button_content.lower()

def test_error_handling(markdown_processor, create_temp_md):
    """Test various error conditions and edge cases."""
    # Test with non-existent file
    with pytest.raises(FileNotFoundError):
        markdown_processor.process_file("nonexistent.md")
    
    # Test with invalid frontmatter
    invalid_content = """---
invalid: [
unclosed: bracket
---
# Test"""
    md_file = create_temp_md(invalid_content)
    result = markdown_processor.process_file(str(md_file))
    assert len(result.errors) > 0
    
    # Test with empty file
    empty_file = create_temp_md("")
    result = markdown_processor.process_file(str(empty_file))
    assert isinstance(result, MarkdownProcessingResult)
    assert result.to_dataframe().empty
    
    # Test with only frontmatter
    frontmatter_only = create_temp_md("""---
title: Test
---""")
    result = markdown_processor.process_file(str(frontmatter_only))
    assert isinstance(result, MarkdownProcessingResult)
    assert result.metadata.get("title") == "Test"
    
    # Test with malformed markdown
    malformed = create_temp_md("""# Unclosed link [text
> Unclosed blockquote
```python
unclosed code block""")
    result = markdown_processor.process_file(str(malformed))
    assert isinstance(result, MarkdownProcessingResult)
    assert len(result.errors) > 0

def test_multiple_files_processing(markdown_processor, tmp_path):
    """Test processing multiple files and result accumulation."""
    def _create_temp_md_with_name(content: str, name: str) -> Path:
        md_file = tmp_path / name
        md_file.write_text(content)
        return md_file
        
    # Process first file
    content1 = """# File 1
## Header 2
```python
code1
```"""
    file1 = _create_temp_md_with_name(content1, "file1.md")
    result1 = markdown_processor.process_file(str(file1))
    
    # Process second file
    content2 = """# File 2
## Header 2
```python
code2
```"""
    file2 = _create_temp_md_with_name(content2, "file2.md")
    result2 = markdown_processor.process_file(str(file2))
    
    # Check results accumulation
    assert not markdown_processor.results_df.empty
    assert len(markdown_processor.results_df) == 6  # 2 headers + 1 code block from each file
    
    # Check file paths
    file_paths = markdown_processor.results_df["filepath"].unique()
    assert len(file_paths) == 2
    
    # Check content from both files
    headers = markdown_processor.results_df[markdown_processor.results_df["processor_type"] == "header"]
    assert "File 1" in headers["content"].values
    assert "File 2" in headers["content"].values

def test_complex_document(markdown_processor, create_temp_md):
    """Test processing a complex document with mixed elements."""
    content = """---
title: Complex Document
author: Test
---

# Main Title

## Section 1

Here's a paragraph with *emphasis* and **strong** text.

```python
def test():
    return "Hello"
```

> Blockquote with a [link](https://example.com)

1. First item
   - Nested unordered
   - Another nested
2. Second item

| Header 1 | Header 2 |
|----------|----------|
| Cell 1   | Cell 2   |

<CustomComponent prop="test">
  Some *markdown* inside JSX
</CustomComponent>"""
    
    md_file = create_temp_md(content)
    result = markdown_processor.process_file(str(md_file))
    df = result.to_dataframe()
    
    # Check all element types are present
    element_types = df["processor_type"].unique()
    required_types = {"header", "code_block", "list_item", "link", 
                     "blockquote", "table_row"}
    for req_type in required_types:
        assert req_type in element_types
    
    # Check metadata
    assert result.metadata["title"] == "Complex Document"
    assert result.metadata["author"] == "Test"
    
    # Check element relationships
    assert df["parent_path"].notna().all()
    assert df["order"].is_monotonic_increasing
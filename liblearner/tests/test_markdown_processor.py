"""Tests for the Markdown processor."""

import os
import tempfile
import unittest
from liblearner.processors.markdown_processor import MarkdownProcessor
import csv

class TestMarkdownProcessor(unittest.TestCase):
    def setUp(self):
        self.processor = MarkdownProcessor()
        self.test_content = '''---
title: Test Document
author: Test Author
---

# Main Header

## Section 1

This is a paragraph with *italic* and **bold** text.
It also has `inline code` and a [link](https://example.com).

### Subsection

1. First item
2. Second item
   - Nested item
   - Another nested item

> This is a blockquote
> with multiple lines

```python
def hello():
    print("Hello, world!")
```

| Header 1 | Header 2 |
|----------|----------|
| Cell 1   | Cell 2   |
'''

    def test_process_file(self):
        # Create a temporary file with test content
        with tempfile.NamedTemporaryFile(mode='w', suffix='.md', delete=False) as f:
            f.write(self.test_content)
            temp_path = f.name

        try:
            result = self.processor.process_file(temp_path)

            # Test headers
            self.assertEqual(len(result['headers']), 3)
            self.assertEqual(result['headers'][0], (1, 'Main Header'))
            self.assertEqual(result['headers'][1], (2, 'Section 1'))
            self.assertEqual(result['headers'][2], (3, 'Subsection'))

            # Test code blocks
            self.assertEqual(len(result['code_blocks']), 1)
            self.assertEqual(result['code_blocks'][0][0], 'python')
            self.assertTrue('print("Hello, world!")' in result['code_blocks'][0][1])

            # Test inline code
            self.assertEqual(result['inline_code'], ['inline code'])

            # Test lists
            self.assertTrue('First item' in result['lists'])
            self.assertTrue('Second item' in result['lists'])
            self.assertTrue('Nested item' in result['lists'])

            # Test links
            self.assertEqual(result['links'], [('link', 'https://example.com')])

            # Test blockquotes
            self.assertTrue(any('This is a blockquote' in quote for quote in result['blockquotes']))

            # Test tables
            self.assertTrue(any('Header 1' in row for row in result['tables']))
            self.assertTrue(any('Cell 1' in row for row in result['tables']))

            # Test emphasis and strong text
            self.assertEqual(result['emphasized_text'], ['italic'])
            self.assertEqual(result['strong_text'], ['bold'])

            # Test metadata
            self.assertEqual(result['metadata']['title'], 'Test Document')
            self.assertEqual(result['metadata']['author'], 'Test Author')

            # Test ToC
            self.assertEqual(len(result['toc']), 3)
            self.assertEqual(result['toc'][0]['text'], 'Main Header')
            self.assertEqual(result['toc'][0]['level'], 1)

        finally:
            # Clean up temporary file
            os.unlink(temp_path)

    def test_csv_output(self):
        """Test that CSV output format is correct."""
        # Create a temporary file with test content
        with tempfile.NamedTemporaryFile(mode='w', suffix='.md', delete=False) as f:
            f.write('''# Main Heading

## Section 1

### Code Examples

```python
def example():
    return True
```

```javascript
function test() {
    return true;
}
```

This is a paragraph with some text.

1. First item
2. Second item
   - Nested item
   - Another nested item

[Example Link](https://example.com)
''')
            temp_path = f.name

        try:
            result = self.processor.process_file(temp_path)
            csv_path = os.path.join(tempfile.gettempdir(), "output.csv")
            with open(csv_path, 'w', newline='') as csvfile:
                writer = csv.writer(csvfile)
                writer.writerow(['Filename', 'Type', 'Content', 'Level', 'Language', 'Metadata'])
                
                # Write headers first
                for level, text in result.get('headers', []):
                    writer.writerow([
                        'test.md',
                        'header',
                        text,
                        str(level),
                        '',
                        ''
                    ])
                
                # Then write code blocks
                for language, code in result.get('code_blocks', []):
                    writer.writerow([
                        'test.md',
                        'code_block',
                        code,
                        '',
                        language,
                        ''
                    ])
                
                # Then write paragraphs
                for para in result.get('paragraphs', []):
                    writer.writerow([
                        'test.md',
                        'paragraph',
                        para,
                        '',
                        '',
                        ''
                    ])
                
                # Finally write lists
                for item in result.get('lists', []):
                    writer.writerow([
                        'test.md',
                        'list_item',
                        item,
                        '',
                        '',
                        ''
                    ])

            # Read and verify the CSV content
            with open(csv_path, newline='') as csvfile:
                reader = csv.reader(csvfile)
                header = next(reader)
                self.assertEqual(header, ['Filename', 'Type', 'Content', 'Level', 'Language', 'Metadata'])
                
                # Verify headers first
                row = next(reader)
                self.assertEqual(row[1], 'header')
                self.assertEqual(row[2], 'Main Heading')
                self.assertEqual(row[3], '1')
                
                row = next(reader)
                self.assertEqual(row[1], 'header')
                self.assertEqual(row[2], 'Section 1')
                self.assertEqual(row[3], '2')
                
                row = next(reader)
                self.assertEqual(row[1], 'header')
                self.assertEqual(row[2], 'Code Examples')
                self.assertEqual(row[3], '3')
                
                # Then verify code blocks
                row = next(reader)
                self.assertEqual(row[1], 'code_block')
                self.assertEqual(row[2].rstrip(), 'def example():\n    return True')
                self.assertEqual(row[4], 'python')
                
                row = next(reader)
                self.assertEqual(row[1], 'code_block')
                self.assertEqual(row[2].rstrip(), 'function test() {\n    return true;\n}')
                self.assertEqual(row[4], 'javascript')
                
                # Then verify paragraphs
                row = next(reader)
                self.assertEqual(row[1], 'paragraph')
                self.assertTrue('This is a paragraph' in row[2])
                
                # Finally verify list items
                row = next(reader)
                self.assertEqual(row[1], 'list_item')
                self.assertEqual(row[2], 'First item')
                
                row = next(reader)
                self.assertEqual(row[1], 'list_item')
                self.assertEqual(row[2], 'Second item')

        finally:
            # Clean up temporary files
            os.unlink(temp_path)
            os.unlink(csv_path)

    def test_supported_extensions(self):
        extensions = self.processor.get_supported_extensions()
        self.assertEqual(set(extensions), {'md', 'markdown'})

if __name__ == '__main__':
    unittest.main()

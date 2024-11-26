"""Tests for the Markdown processor."""

import os
import tempfile
import unittest
from liblearner.processors.markdown_processor import MarkdownProcessor

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

    def test_supported_extensions(self):
        extensions = self.processor.get_supported_extensions()
        self.assertEqual(set(extensions), {'md', 'markdown'})

if __name__ == '__main__':
    unittest.main()

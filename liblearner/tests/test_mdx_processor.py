"""Tests for the MDX processor."""

import os
import tempfile
import unittest
from pathlib import Path
from liblearner.processors.mdx_processor import MDXProcessor

class TestMDXProcessor(unittest.TestCase):
    def setUp(self):
        self.processor = MDXProcessor()
        self.test_content = '''---
title: Test MDX File
layout: BlogPost
date: 2023-01-01
---

import { Button } from '@components/Button'
import { Card } from '@components/Card'
import DefaultLayout from '@layouts/DefaultLayout'

export const metadata = {
    title: 'My Blog Post',
    description: 'A test blog post'
}

<Button variant="primary" onClick={() => console.log('clicked')}>
  Click me!
</Button>

<Card title="Test Card">
  This is a test card component
</Card>

# Introduction

This is a test MDX file with some **bold** text and *italic* text.

## Code Example

```python
def hello_world():
    print("Hello, World!")
```

export default ({ children }) => <DefaultLayout>{children}</DefaultLayout>
'''

    def test_process_file(self):
        # Create a temporary file with test content
        with tempfile.NamedTemporaryFile(mode='w', suffix='.mdx', delete=False) as f:
            f.write(self.test_content)
            temp_path = f.name

        try:
            result = self.processor.process_file(temp_path)

            # Test frontmatter
            self.assertEqual(result['frontmatter']['title'], 'Test MDX File')
            self.assertEqual(result['frontmatter']['layout'], 'BlogPost')
            self.assertEqual(result['frontmatter']['date'], '2023-01-01')

            # Test layout
            self.assertEqual(result['layout'], 'BlogPost')

            # Test components
            expected_components = ['Button', 'Card', 'DefaultLayout']
            self.assertEqual(result['components'], expected_components)

            # Test exports
            self.assertTrue('metadata' in result['exports'])
            self.assertTrue('default' in result['exports'])

            # Test imports
            expected_imports = [
                '@components/Button',
                '@components/Card',
                '@layouts/DefaultLayout'
            ]
            self.assertEqual(result['imports'], expected_imports)

            # Test file info
            self.assertTrue('name' in result['file_info'])
            self.assertTrue('path' in result['file_info'])
            self.assertTrue('size' in result['file_info'])
            self.assertTrue('modified' in result['file_info'])

            # Test error handling
            self.assertEqual(len(result['errors']), 0)

        finally:
            # Clean up temporary file
            os.unlink(temp_path)

    def test_invalid_file(self):
        result = self.processor.process_file('nonexistent.mdx')
        self.assertTrue('error' in result)
        self.assertEqual(len(result['components']), 0)
        self.assertEqual(len(result['exports']), 0)
        self.assertEqual(len(result['imports']), 0)
        self.assertEqual(result['frontmatter'], {})
        self.assertIsNone(result['layout'])

    def test_invalid_frontmatter(self):
        invalid_content = '''---
invalid: yaml:
  - not properly indented
---

# Content
'''
        with tempfile.NamedTemporaryFile(mode='w', suffix='.mdx', delete=False) as f:
            f.write(invalid_content)
            temp_path = f.name

        try:
            result = self.processor.process_file(temp_path)
            self.assertTrue(len(result['errors']) > 0)
            self.assertEqual(result['frontmatter'], {})
        finally:
            os.unlink(temp_path)

    def test_supported_extensions(self):
        extensions = self.processor.get_supported_extensions()
        self.assertEqual(extensions, ['mdx'])

    def test_extract_props(self):
        component_str = '<Button variant="primary" size={2} disabled={true} />'
        props = self.processor._extract_props(component_str)
        
        self.assertEqual(props['variant'], 'primary')
        self.assertEqual(props['size'], '2')
        self.assertEqual(props['disabled'], 'true')

if __name__ == '__main__':
    unittest.main()

"""Tests for the MDX processor."""

import os
import tempfile
import unittest
from pathlib import Path
from liblearner.processors.mdx_processor import MDXProcessor
import csv

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

    def test_csv_output(self):
        """Test that CSV output format is correct."""
        mdx_content = '''
---
title: Test Post
description: A test MDX post
---

import Button from '@components/Button';
import Card from '@components/Card';

export const metadata = {
    title: "Dynamic Title",
    date: "2023-12-25"
};

# Main Content

<Button variant="primary">Click Me</Button>

<Card>
  ## Card Title
  Some card content here
</Card>

This is a test paragraph.

```javascript
console.log('Hello MDX!');
```
'''
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.mdx', delete=False) as f:
            f.write(mdx_content)
            temp_path = f.name

        try:
            result = self.processor.process_file(temp_path)
            
            csv_path = os.path.join(tempfile.gettempdir(), "output.csv")
            with open(csv_path, 'w', newline='') as csvfile:
                writer = csv.writer(csvfile)
                writer.writerow(['Filename', 'Type', 'Name', 'Content', 'Props', 'Metadata'])
                
                # Write components
                for comp in result['components']:
                    writer.writerow([
                        'blog-post.mdx',
                        'component',
                        comp['name'],
                        comp.get('content', ''),
                        comp.get('props', ''),
                        ''
                    ])
                
                # Write imports
                for imp in result['imports']:
                    source = imp[imp.find('from')+4:].strip().strip("'").strip('"') if 'from' in imp else ''
                    name = imp[imp.find('import')+6:imp.find('from')].strip() if 'from' in imp else imp[imp.find('import')+6:].strip()
                    writer.writerow([
                        'blog-post.mdx',
                        'import',
                        name,
                        source,
                        '',
                        ''
                    ])
                
                # Write exports
                for exp in result['exports']:
                    if 'export default' in exp:
                        name = 'default'
                        value = exp.replace('export default', '').strip()
                    else:
                        name = exp[exp.find('export')+6:].split('=')[0].strip()
                        value = exp[exp.find('=')+1:].strip() if '=' in exp else ''
                    writer.writerow([
                        'blog-post.mdx',
                        'export',
                        name,
                        value,
                        '',
                        ''
                    ])

            # Read and verify the CSV content
            with open(csv_path, newline='') as csvfile:
                reader = csv.reader(csvfile)
                header = next(reader)
                self.assertEqual(header, ['Filename', 'Type', 'Name', 'Content', 'Props', 'Metadata'])
                
                # Verify imports first
                row = next(reader)
                self.assertEqual(row[1], 'import')
                self.assertEqual(row[2], 'Button')
                self.assertEqual(row[3], '@components/Button')
                
                row = next(reader)
                self.assertEqual(row[1], 'import')
                self.assertEqual(row[2], 'Card')
                self.assertEqual(row[3], '@components/Card')
                
                # Then verify exports
                row = next(reader)
                self.assertEqual(row[1], 'export')
                self.assertEqual(row[2], 'metadata')
                self.assertIn('Dynamic Title', row[3])
                
                # Finally verify components
                row = next(reader)
                self.assertEqual(row[1], 'component')
                self.assertEqual(row[2], 'Button')
                self.assertIn('Click Me', row[3])
                self.assertIn('variant="primary"', row[4])
                
                row = next(reader)
                self.assertEqual(row[1], 'component')
                self.assertEqual(row[2], 'Card')
                self.assertIn('Card Title', row[3])
                
        finally:
            # Clean up temporary files
            os.unlink(temp_path)
            os.unlink(csv_path)

if __name__ == '__main__':
    unittest.main()

import unittest
import os
import tempfile
import shutil
from pathlib import Path

from liblearner.scout import scout_extensions as scout

class TestScoutExtensions(unittest.TestCase):
    def setUp(self):
        # Create a temporary directory for test files
        self.test_dir = tempfile.mkdtemp()
        
        # Create test files with different extensions
        self.create_test_files()
        
    def tearDown(self):
        # Clean up temporary directory
        shutil.rmtree(self.test_dir)
        
    def create_test_files(self):
        """Create test files with various extensions"""
        # Create test files
        files = {
            'test1.py': 'print("Hello")',
            'test2.py': 'def test(): pass',
            'test3.js': 'function test() {}',
            'test4.ts': 'const x: number = 42;',
            'test5.go': 'package main',
            'noext': 'no extension',
            'test6.ts': 'interface Test {}',
            '.hidden': 'hidden file'
        }
        
        # Create subdirectories
        os.makedirs(os.path.join(self.test_dir, 'subdir'))
        os.makedirs(os.path.join(self.test_dir, 'node_modules'))
        
        # Create files
        for filename, content in files.items():
            filepath = os.path.join(self.test_dir, filename)
            with open(filepath, 'w') as f:
                f.write(content)
                
        # Create files in subdirectory
        with open(os.path.join(self.test_dir, 'subdir', 'test7.py'), 'w') as f:
            f.write('# Test file')
            
        # Create file in ignored directory
        with open(os.path.join(self.test_dir, 'node_modules', 'test8.js'), 'w') as f:
            f.write('// Ignored file')

    def test_analyze_extensions(self):
        """Test extension analysis functionality"""
        extensions = scout.analyze_extensions(self.test_dir)
        
        # Check extension counts
        self.assertEqual(extensions['py'], 3)  # Including subdirectory file
        self.assertEqual(extensions['js'], 1)  # node_modules file should be ignored
        self.assertEqual(extensions['ts'], 2)
        self.assertEqual(extensions['go'], 1)
        
        # Check that files without extensions are not counted
        self.assertNotIn('', extensions)
        
    def test_directory_exclusion(self):
        """Test directory exclusion functionality"""
        # Test with default ignore list
        extensions = scout.analyze_extensions(self.test_dir)
        self.assertEqual(extensions['js'], 1)  # node_modules file should be ignored
        
        # Test with custom ignore list
        extensions = scout.analyze_extensions(self.test_dir, ignore_dirs=['subdir'])
        self.assertEqual(extensions['py'], 2)  # subdir file should be ignored
        
    def test_empty_directory(self):
        """Test handling of empty directory"""
        empty_dir = tempfile.mkdtemp()
        try:
            extensions = scout.analyze_extensions(empty_dir)
            self.assertEqual(len(extensions), 0)
        finally:
            shutil.rmtree(empty_dir)
            
    def test_nonexistent_directory(self):
        """Test handling of nonexistent directory"""
        with self.assertRaises(FileNotFoundError):
            scout.analyze_extensions('/nonexistent/directory')
            
    def test_format_extension_report(self):
        """Test report formatting"""
        extensions = {'py': 3, 'js': 1, 'ts': 2}
        
        # Test unsorted report
        report = scout.format_extension_report(extensions, sort=False)
        self.assertIn('.py          3 files', report)
        self.assertIn('.js          1 files', report)
        self.assertIn('.ts          2 files', report)
        
        # Test sorted report
        report = scout.format_extension_report(extensions, sort=True)
        lines = report.split('\n')
        self.assertEqual(lines[0], '.py          3 files')  # Most frequent first
        self.assertEqual(lines[1], '.ts          2 files')
        self.assertEqual(lines[2], '.js          1 files')

if __name__ == '__main__':
    unittest.main()

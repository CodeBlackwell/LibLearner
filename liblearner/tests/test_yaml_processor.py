"""Tests for the YAML processor."""

import os
import tempfile
import unittest
from liblearner.processors.yaml_processor import YAMLProcessor

class TestYAMLProcessor(unittest.TestCase):
    def setUp(self):
        self.processor = YAMLProcessor()
        self.test_content = '''---
# Service configuration
services:
  web:
    image: nginx:latest
    environment:
      - PORT=${PORT}
      - API_KEY=$API_KEY
    ports:
      - "8080:80"
    depends_on:
      - db

  db:
    image: postgres:13
    environment:
      POSTGRES_PASSWORD: ${DB_PASSWORD}
      POSTGRES_USER: $DB_USER

# API configuration
api:
  base_url: https://api.example.com
  endpoints:
    - name: users
      path: /users
      method: GET
    - name: posts
      path: /posts
      method: POST

# Dependencies
dependencies:
  python: ">=3.7"
  packages:
    - name: requests
      version: "2.26.0"
    - name: pyyaml
      version: "5.4.1"

# Nested configuration
config:
  database:
    host: localhost
    port: 5432
    credentials:
      username: ${DB_USER}
      password: ${DB_PASSWORD}
  cache:
    type: redis
    url: https://redis.example.com
    timeout: 30
'''

    def test_process_file(self):
        # Create a temporary file with test content
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yml', delete=False) as f:
            f.write(self.test_content)
            temp_path = f.name

        try:
            result = self.processor.process_file(temp_path)

            # Test document structure
            self.assertEqual(len(result['documents']), 1)
            self.assertTrue(isinstance(result['documents'][0], dict))

            # Test environment variables
            expected_env_vars = {'PORT', 'API_KEY', 'DB_PASSWORD', 'DB_USER'}
            self.assertEqual(set(result['env_vars']), expected_env_vars)

            # Test URLs
            expected_urls = {
                'https://api.example.com',
                'https://redis.example.com'
            }
            self.assertEqual(set(result['urls']), expected_urls)

            # Test service configurations
            self.assertTrue('services' in result['services'])
            services = result['services']['services']
            self.assertTrue('web' in services)
            self.assertTrue('db' in services)

            # Test API configurations
            self.assertTrue('api' in result['api_configs'])
            api_config = result['api_configs']['api']
            self.assertEqual(api_config['base_url'], 'https://api.example.com')

            # Test dependencies
            self.assertTrue('dependencies' in result['dependencies'])
            deps = result['dependencies']['dependencies']
            self.assertEqual(deps['python'], '>=3.7')

            # Test type analysis
            types = result['types']
            self.assertEqual(types['services'], 'mapping')
            self.assertEqual(types['services.web.ports'], 'sequence')
            self.assertEqual(types['api.base_url'], 'str')

            # Test schema inference
            schemas = result['schemas']
            self.assertTrue('services' in schemas)
            self.assertEqual(schemas['services']['type'], 'object')

            # Test file info
            self.assertTrue('file_info' in result)
            self.assertEqual(result['file_info']['name'], os.path.basename(temp_path))

        finally:
            # Clean up temporary file
            os.unlink(temp_path)

    def test_invalid_yaml(self):
        invalid_content = '''
        invalid:
          - yaml:
            content
            not properly indented
        '''
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yml', delete=False) as f:
            f.write(invalid_content)
            temp_path = f.name

        try:
            result = self.processor.process_file(temp_path)
            self.assertTrue(len(result['errors']) > 0)
            self.assertEqual(len(result['documents']), 0)
        finally:
            os.unlink(temp_path)

    def test_empty_file(self):
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yml', delete=False) as f:
            temp_path = f.name

        try:
            result = self.processor.process_file(temp_path)
            self.assertEqual(len(result['documents']), 0)
            self.assertEqual(len(result['structure']), 0)
            self.assertEqual(len(result['env_vars']), 0)
            self.assertEqual(len(result['urls']), 0)
        finally:
            os.unlink(temp_path)

    def test_multiple_documents(self):
        content = '''---
document: 1
---
document: 2
---
document: 3
'''
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yml', delete=False) as f:
            f.write(content)
            temp_path = f.name

        try:
            result = self.processor.process_file(temp_path)
            self.assertEqual(len(result['documents']), 3)
            self.assertEqual(len(result['structure']), 3)
        finally:
            os.unlink(temp_path)

    def test_supported_extensions(self):
        extensions = self.processor.get_supported_extensions()
        self.assertEqual(set(extensions), {'yaml', 'yml'})

if __name__ == '__main__':
    unittest.main()

import unittest
from pathlib import Path
from liblearner.processors.yaml_processor import YAMLProcessor, YAMLProcessingResult

class TestYAMLProcessor(unittest.TestCase):
    def setUp(self):
        self.processor = YAMLProcessor(debug=True)
        self.test_files_dir = Path(__file__).parent / "test_files"
        self.sample_yaml = self.test_files_dir / "sample.yaml"
        self.invalid_yaml = self.test_files_dir / "invalid.yaml"

    def test_process_valid_file(self):
        """Test processing a valid YAML file"""
        result = self.processor.process_file(str(self.sample_yaml))
        
        # Check basic result properties
        self.assertIsInstance(result, YAMLProcessingResult)
        self.assertEqual(len(result.errors), 0)
        self.assertEqual(len(result.documents), 1)
        
        # Check file info
        self.assertIn('name', result.file_info)
        self.assertEqual(result.file_info['name'], 'sample.yaml')
        
        # Check structure
        self.assertTrue(len(result.structure) > 0)
        self.assertEqual(result.structure[0]['type'], 'mapping')
        
        # Check environment variables
        expected_env_vars = {'PORT', 'DATABASE_HOST', 'API_KEY'}
        self.assertEqual(set(result.env_vars), expected_env_vars)
        
        # Check URLs
        self.assertIn('https://api.example.com', result.urls)
        
        # Check types
        self.assertIn('data_types.string_value', result.types)
        self.assertEqual(result.types['data_types.string_value'], 'str')
        self.assertEqual(result.types['data_types.int_value'], 'int')
        self.assertEqual(result.types['data_types.float_value'], 'float')
        self.assertEqual(result.types['data_types.bool_value'], 'bool')
        self.assertEqual(result.types['data_types.null_value'], 'null')
        
        # Check services
        self.assertIn('web', result.services)
        
        # Check dependencies
        self.assertEqual(result.dependencies.get('python'), '>=3.8')
        self.assertEqual(result.dependencies.get('yaml'), '^5.1')
        
        # Check API configs
        self.assertIn('base_url', result.api_configs)
        self.assertIn('endpoints', result.api_configs)

    def test_process_invalid_file(self):
        """Test processing an invalid YAML file"""
        result = self.processor.process_file(str(self.invalid_yaml))
        
        # Should have parsing error
        self.assertTrue(len(result.errors) > 0)
        self.assertIn('YAML parsing error', result.errors[0])
        
        # Basic file info should still be available
        self.assertIn('name', result.file_info)
        self.assertEqual(result.file_info['name'], 'invalid.yaml')

    def test_nonexistent_file(self):
        """Test processing a file that doesn't exist"""
        result = self.processor.process_file('nonexistent.yaml')
        self.assertTrue(len(result.errors) > 0)
        self.assertIn('Error reading file', result.errors[0])

    def test_empty_file(self):
        """Test processing an empty file"""
        empty_file = self.test_files_dir / "empty.yaml"
        empty_file.touch()
        
        result = self.processor.process_file(str(empty_file))
        self.assertEqual(len(result.errors), 0)
        self.assertEqual(len(result.documents), 0)
        
        empty_file.unlink()  # Clean up

    def test_analyze_structure(self):
        """Test structure analysis of YAML content"""
        test_data = {
            'string': 'value',
            'list': [1, 2, 3],
            'dict': {'key': 'value'}
        }
        
        structure = self.processor._analyze_structure(test_data)
        self.assertEqual(structure['type'], 'mapping')
        self.assertIn('keys', structure)
        self.assertEqual(structure['keys']['string']['type'], 'str')
        self.assertEqual(structure['keys']['list']['type'], 'sequence')
        self.assertEqual(structure['keys']['dict']['type'], 'mapping')

    def test_extract_env_vars(self):
        """Test environment variable extraction"""
        test_data = {
            'simple': '$SIMPLE_VAR',
            'braces': '${BRACED_VAR}',
            'nested': {'env': '${NESTED_VAR}'},
            'list': ['$LIST_VAR', '${OTHER_VAR}']
        }
        
        env_vars = self.processor._extract_env_vars(test_data)
        expected_vars = {'SIMPLE_VAR', 'BRACED_VAR', 'NESTED_VAR', 'LIST_VAR', 'OTHER_VAR'}
        self.assertEqual(set(env_vars), expected_vars)

    def test_extract_urls(self):
        """Test URL extraction"""
        test_data = {
            'url1': 'https://example.com',
            'url2': 'http://test.com/api',
            'nested': {'url': 'https://nested.com/path'},
            'list': ['http://list.com', 'https://another.com/path?q=1']
        }
        
        urls = self.processor._extract_urls(test_data)
        expected_urls = {
            'https://example.com',
            'http://test.com/api',
            'https://nested.com/path',
            'http://list.com',
            'https://another.com/path?q=1'
        }
        self.assertEqual(set(urls), expected_urls)

    def test_analyze_types(self):
        """Test type analysis"""
        test_data = {
            'string': 'value',
            'integer': 42,
            'float': 3.14,
            'boolean': True,
            'null': None,
            'list': [1, 2, 3],
            'dict': {'key': 'value'}
        }
        
        types = self.processor._analyze_types(test_data)
        self.assertEqual(types['string'], 'str')
        self.assertEqual(types['integer'], 'int')
        self.assertEqual(types['float'], 'float')
        self.assertEqual(types['boolean'], 'bool')
        self.assertEqual(types['null'], 'null')
        self.assertEqual(types['list'], 'sequence')
        self.assertEqual(types['dict'], 'mapping')

    def test_infer_schemas(self):
        """Test schema inference"""
        test_data = {
            'config': {
                'name': 'test',
                'values': [1, 2, 3],
                'nested': {
                    'key': 'value'
                }
            }
        }
        
        schemas = self.processor._infer_schemas(test_data)
        config_schema = schemas['config']
        
        self.assertEqual(config_schema['type'], 'object')
        self.assertIn('properties', config_schema)
        self.assertEqual(config_schema['properties']['name']['type'], 'str')
        self.assertEqual(config_schema['properties']['values']['type'], 'array')
        self.assertEqual(config_schema['properties']['nested']['type'], 'object')

    def test_to_csv_nested_dict(self):
        """Test converting nested dictionary to CSV format"""
        test_data = {
            'person': {
                'name': 'John',
                'age': 30,
                'address': {
                    'street': '123 Main St',
                    'city': 'Example City'
                }
            }
        }
        
        rows = self.processor.to_csv(test_data)
        self.assertEqual(len(rows), 1)  # One row for the dictionary
        row = rows[0]
        
        # Check flattened keys
        self.assertEqual(row['person.name'], 'John')
        self.assertEqual(row['person.age'], '30')
        self.assertEqual(row['person.address.street'], '123 Main St')
        self.assertEqual(row['person.address.city'], 'Example City')

    def test_to_csv_list(self):
        """Test converting list to CSV format"""
        test_data = [
            {'name': 'John', 'age': 30},
            {'name': 'Jane', 'age': 25}
        ]
        
        rows = self.processor.to_csv(test_data)
        self.assertEqual(len(rows), 2)  # Two rows for two list items
        
        # Check first row
        self.assertEqual(rows[0]['name'], 'John')
        self.assertEqual(rows[0]['age'], '30')
        
        # Check second row
        self.assertEqual(rows[1]['name'], 'Jane')
        self.assertEqual(rows[1]['age'], '25')

    def test_to_csv_nested_list(self):
        """Test converting nested list to CSV format"""
        test_data = {
            'users': [
                {'name': 'John', 'scores': [85, 90, 95]},
                {'name': 'Jane', 'scores': [88, 92, 98]}
            ]
        }
        
        rows = self.processor.to_csv(test_data)
        self.assertEqual(len(rows), 1)  # One row for the dictionary
        row = rows[0]
        
        # Check flattened list items
        self.assertEqual(row['users[0].name'], 'John')
        self.assertEqual(row['users[0].scores[0]'], '85')
        self.assertEqual(row['users[0].scores[1]'], '90')
        self.assertEqual(row['users[0].scores[2]'], '95')
        self.assertEqual(row['users[1].name'], 'Jane')
        self.assertEqual(row['users[1].scores[0]'], '88')
        self.assertEqual(row['users[1].scores[1]'], '92')
        self.assertEqual(row['users[1].scores[2]'], '98')

    def test_to_csv_custom_separator(self):
        """Test CSV conversion with custom separator"""
        test_data = {
            'person': {
                'name': 'John',
                'age': 30
            }
        }
        
        rows = self.processor.to_csv(test_data, sep='_')
        self.assertEqual(len(rows), 1)
        row = rows[0]
        
        # Check keys with custom separator
        self.assertEqual(row['person_name'], 'John')
        self.assertEqual(row['person_age'], '30')

    def test_to_csv_with_none_values(self):
        """Test CSV conversion with None values"""
        test_data = {
            'person': {
                'name': 'John',
                'email': None,
                'phone': ''
            }
        }
        
        rows = self.processor.to_csv(test_data)
        self.assertEqual(len(rows), 1)
        row = rows[0]
        
        # Check handling of None and empty values
        self.assertEqual(row['person.name'], 'John')
        self.assertEqual(row['person.email'], '')  # None should be converted to empty string
        self.assertEqual(row['person.phone'], '')

if __name__ == '__main__':
    unittest.main()

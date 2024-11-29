import json
import subprocess
import os
import logging
import re
import pandas as pd
from typing import List, Dict, Any, Set
from pathlib import Path
from datetime import datetime
from ..file_processor import FileProcessor
from ..processing_result import JavaScriptProcessingResult

# Set up logging
logger = logging.getLogger(__name__)

class JavaScriptProcessor(FileProcessor):
    def __init__(self, debug: bool = False):
        super().__init__()
        self.debug = debug
        if self.debug:
            logger.setLevel(logging.DEBUG)
        
        # Initialize tracking variables
        self.results_df = pd.DataFrame()
        self._order_counter = 0
        self._current_path = []
        
        # Define supported MIME types
        self.supported_types = {
            'application/javascript',
            'text/javascript',
            'application/x-javascript'
        }
    
    def get_supported_types(self) -> List[str]:
        """Return list of supported MIME types."""
        return list(self.supported_types)
    
    def _validate_content(self, content: str) -> List[str]:
        """Validate JavaScript content for malformed elements."""
        errors = []
        
        # Check for unclosed braces/brackets
        brace_count = content.count('{') - content.count('}')
        bracket_count = content.count('[') - content.count(']')
        paren_count = content.count('(') - content.count(')')
        
        if brace_count != 0:
            errors.append(f"Found {abs(brace_count)} unclosed braces")
        if bracket_count != 0:
            errors.append(f"Found {abs(bracket_count)} unclosed brackets")
        if paren_count != 0:
            errors.append(f"Found {abs(paren_count)} unclosed parentheses")
            
        # Check for missing semicolons at line ends (basic check)
        lines = content.split('\n')
        for i, line in enumerate(lines):
            line = line.strip()
            if line and not line.endswith(';') and not line.endswith('{') and not line.endswith('}') \
               and not line.endswith('[') and not line.endswith(']') and not line.endswith(',') \
               and not line.startswith('//') and not line.startswith('/*'):
                errors.append(f"Line {i+1} may be missing a semicolon: {line}")
        
        return errors
    
    def _handle_error(self, error: Exception, context: str) -> Dict:
        """Create standardized error entry."""
        return {
            'error_type': type(error).__name__,
            'message': str(error),
            'context': context,
            'timestamp': datetime.now().isoformat()
        }
    
    def process_file(self, file_path: str) -> JavaScriptProcessingResult:
        """Process a JavaScript file and extract structured information."""
        self._order_counter = 0
        result = JavaScriptProcessingResult()
        results_data = []
        
        path = Path(file_path)
        
        # Check file existence first
        if not os.path.exists(file_path):
            logger.error(f"Error processing {file_path}: File not found")
            raise FileNotFoundError(f"File not found: {file_path}")
        
        try:
            # Read file content
            content = path.read_text()
            
            # Validate content
            validation_errors = self._validate_content(content)
            if validation_errors:
                for error in validation_errors:
                    result.errors.append(error)
                    logger.warning(f"Validation error in {file_path}: {error}")
            
            # Store file info
            result.file_info = {
                'name': path.name,
                'path': str(path.absolute()),
                'size': path.stat().st_size,
                'last_modified': path.stat().st_mtime,
                'type': 'javascript'
            }
            
            # Get the path to the JavaScript extractor script
            extractor_path = os.path.join(os.path.dirname(__file__), '../javascript_extractor.js')
            
            # Run the JavaScript extractor as a subprocess
            output = subprocess.check_output(
                ['node', extractor_path, '--path', file_path],
                universal_newlines=True
            )
            
            # Parse the JSON output
            elements = json.loads(output)
            
            # Process elements and create records
            for element in elements:
                self._order_counter += 1
                
                # Extract environment variables and URLs
                env_vars = self._extract_env_vars(element['code'])
                urls = self._extract_urls(element['code'])
                
                # Create element record
                element_info = {
                    'filepath': str(path.absolute()),
                    'parent_path': element.get('parentName', ''),
                    'order': self._order_counter,
                    'name': element['name'],
                    'content': element['code'],
                    'props': json.dumps({
                        'parameters': element.get('parameters', []),
                        'comments': element.get('comments', []),
                        'nestingLevel': element['nestingLevel'],
                        'env_vars': list(env_vars),
                        'urls': list(urls)
                    }),
                    'processor_type': element['type'].lower()
                }
                results_data.append(element_info)
            
            # Create DataFrame
            df = pd.DataFrame(results_data) if results_data else pd.DataFrame(columns=[
                'filepath', 'parent_path', 'order', 'name', 'content', 'props', 'processor_type'
            ])
            
            # Set the DataFrame in the result object
            result.df = df
            
            # Concatenate with existing results
            if not self.results_df.empty:
                self.results_df = pd.concat([self.results_df, df], ignore_index=True)
            else:
                self.results_df = df
                
        except subprocess.CalledProcessError as e:
            error = self._handle_error(e, "JavaScript extraction failed")
            result.errors.append(str(error))
            logger.error(f"Error processing {file_path}: {error}")
        except json.JSONDecodeError as e:
            error = self._handle_error(e, "Failed to parse extractor output")
            result.errors.append(str(error))
            logger.error(f"Error processing {file_path}: {error}")
        except Exception as e:
            error = self._handle_error(e, "Unexpected error during processing")
            result.errors.append(str(error))
            logger.error(f"Error processing {file_path}: {error}")
            
        return result
    
    def _extract_env_vars(self, code: str) -> Set[str]:
        """Extract environment variables from JavaScript code."""
        env_vars = set()
        
        # Match process.env.VAR_NAME or process.env['VAR_NAME']
        env_patterns = [
            r'process\.env\.([A-Z][A-Z0-9_]*)',
            r'process\.env\[[\'"](.*?)[\'"]\]'
        ]
        
        for pattern in env_patterns:
            matches = re.finditer(pattern, code)
            for match in matches:
                env_vars.add(match.group(1))
                
        return env_vars
    
    def _extract_urls(self, code: str) -> Set[str]:
        """Extract URLs from JavaScript code."""
        urls = set()
        
        # Match URLs in strings
        url_patterns = [
            r'https?://[^\s<>"\']+|www\.[^\s<>"\']+',
            r'[\'"`]\/[^\s<>\'"`]+[\'"`]'  # Match relative URLs
        ]
        
        for pattern in url_patterns:
            matches = re.finditer(pattern, code)
            for match in matches:
                url = match.group(0).strip("'`\"")
                urls.add(url)
                
        return urls
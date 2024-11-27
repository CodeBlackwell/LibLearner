"""JavaScript processor for LibLearner.
Handles extraction of information from JavaScript files.
"""

import json
import subprocess
import os
import pandas as pd
from typing import List, Dict, Any, Union
from ..file_processor import FileProcessor

class JavaScriptProcessor(FileProcessor):
    """Processor for JavaScript files."""
    result_data = []
    
    def __init__(self):
        """Initialize the JavaScript processor."""
        super().__init__()
    
    def get_supported_types(self) -> List[str]:
        """Return list of supported MIME types."""
        return [
            'application/javascript',
            'text/javascript',
            'application/x-javascript'
        ]
    
    def process_file(self, file_path: str) -> Dict[str, Any]:
        """
        Process a JavaScript file and extract code elements.
        
        Args:
            file_path: Path to the JavaScript file
            
        Returns:
            Dictionary containing:
                - type: "javascript"
                - path: file path
                - elements: list of code elements (functions, classes, etc.)
                - error: error message if processing failed
        """
        try:
            # Get the path to our JavaScript extractor
            extractor_path = os.path.join(os.path.dirname(__file__), '..', 'javascript_extractor.js')
            
            # Run the JavaScript extractor as a subprocess
            result = subprocess.run(
                ['node', extractor_path, '--path', file_path],
                capture_output=True,
                text=True,
                check=True
            )
            
            # Parse the JSON output
            elements = json.loads(result.stdout)
            
            # Create results data for DataFrame
            results_data = self.result_data
            for element in elements:
                element_type = element.get('type', 'unknown')
                name = element.get('name', '')
                
                if element_type == 'FunctionDeclaration':
                    content = element.get('code', '')
                    props = {
                        'parameters': element.get('parameters', []),
                        'async': element.get('async', False),
                        'generator': element.get('generator', False)
                    }
                elif element_type == 'ClassDeclaration':
                    content = element.get('code', '')
                    props = {
                        'superClass': element.get('superClass', None),
                        'methods': [m.get('name') for m in element.get('methods', [])]
                    }
                else:
                    content = element.get('code', '')
                    props = {}
                
                results_data.append({
                    'type': element_type.lower(),
                    'name': name,
                    'content': content,
                    'props': str(props)
                })
            
            # Update the results DataFrame
            self.results_df = pd.DataFrame(results_data)
            
            return {
                "type": "javascript",
                "path": file_path,
                "elements": elements
            }
            
        except subprocess.CalledProcessError as e:
            self.results_df = pd.DataFrame(columns=['type', 'name', 'content', 'props'])
            return {
                "type": "javascript",
                "path": file_path,
                "elements": [],
                "error": f"JavaScript extraction failed: {e.stderr}"
            }
        except json.JSONDecodeError as e:
            self.results_df = pd.DataFrame(columns=['type', 'name', 'content', 'props'])
            return {
                "type": "javascript",
                "path": file_path,
                "elements": [],
                "error": f"Failed to parse extractor output: {str(e)}"
            }
        except Exception as e:
            self.results_df = pd.DataFrame(columns=['type', 'name', 'content', 'props'])
            return {
                "type": "javascript",
                "path": file_path,
                "elements": [],
                "error": str(e)
            }

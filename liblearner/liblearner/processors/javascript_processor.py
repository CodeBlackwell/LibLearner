import json
import subprocess
import os
import pandas as pd
from typing import List, Dict, Any
from ..file_processor import FileProcessor

class JavaScriptProcessingResult:
    def __init__(self):
        self.errors: List[str] = []
        self.elements: List[Dict] = []
        self.file_info: Dict[str, Any] = {}
        self.env_vars: Set[str] = set()
        self.urls: Set[str] = set()

class JavaScriptProcessor(FileProcessor):
    def __init__(self, debug: bool = False):
        super().__init__()
        self.debug = debug
    
    def get_supported_types(self) -> List[str]:
        return [
            'application/javascript',
            'text/javascript',
            'application/x-javascript'
        ]
    
    def process_file(self, file_path: str) -> JavaScriptProcessingResult:
        result = JavaScriptProcessingResult()
        
        try:
            result.file_info = {
                'name': os.path.basename(file_path),
                'path': file_path,
                'size': os.path.getsize(file_path),
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
            result.elements = json.loads(output)
            
            # Extract environment variables and URLs from elements
            for element in result.elements:
                result.env_vars.update(self._extract_env_vars(element['code']))
                result.urls.update(self._extract_urls(element['code']))
            
            # Create DataFrame from result elements
            self.results_df = pd.DataFrame([{
                'type': e['type'].lower(),
                'name': e['name'], 
                'content': e['code'],
                'props': json.dumps({
                    'parameters': e.get('parameters', []),
                    'comments': e.get('comments', []),
                    'nestingLevel': e['nestingLevel'],
                    'parentName': e.get('parentName')
                })
            } for e in result.elements])
            
        except subprocess.CalledProcessError as e:
            result.errors.append(f"JavaScript extraction failed: {e.stderr}")
            if self.debug:
                raise e
        except json.JSONDecodeError as e:
            result.errors.append(f"Failed to parse extractor output: {str(e)}")
            if self.debug:
                raise e
        except Exception as e:
            result.errors.append(str(e))
            if self.debug:
                raise e
        
        return result
    
    def _extract_env_vars(self, code: str) -> set[str]:
        # TODO: Implement environment variable extraction logic
        return set()
    
    def _extract_urls(self, code: str) -> set[str]:
        # TODO: Implement URL extraction logic
        return set()
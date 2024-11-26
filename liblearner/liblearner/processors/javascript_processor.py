"""JavaScript processor for LibLearner.
Handles extraction of information from JavaScript files.
"""

import json
import subprocess
import os
from typing import List, Dict, Any, Union
from ..file_processor import FileProcessor

class JavaScriptProcessor(FileProcessor):
    """Processor for JavaScript files."""
    
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
            
            return {
                "type": "javascript",
                "path": file_path,
                "elements": elements
            }
            
        except subprocess.CalledProcessError as e:
            return {
                "type": "javascript",
                "path": file_path,
                "elements": [],
                "error": f"JavaScript extraction failed: {e.stderr}"
            }
        except json.JSONDecodeError as e:
            return {
                "type": "javascript",
                "path": file_path,
                "elements": [],
                "error": f"Failed to parse extractor output: {str(e)}"
            }
        except Exception as e:
            return {
                "type": "javascript",
                "path": file_path,
                "elements": [],
                "error": str(e)
            }

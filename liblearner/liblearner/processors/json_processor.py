"""JSON processor for LibLearner.
Handles extraction of information from JSON files.
"""

import json
import pandas as pd
from typing import List, Dict, Any, Union
from ..file_processor import FileProcessor
from pathlib import Path

class JSONProcessor(FileProcessor):
    """Processor for JSON files."""
    
    def __init__(self):
        """Initialize the JSON processor."""
        super().__init__()
    
    def get_supported_types(self) -> List[str]:
        """Return list of supported MIME types."""
        return [
            'application/json'
        ]
    
    def to_csv(self, data: Dict, parent_key: str = '', sep: str = '.') -> List[Dict]:
        """
        Convert nested JSON data to a flattened format suitable for CSV.
        
        Args:
            data: JSON data to convert
            parent_key: Key of parent object (for nested objects)
            sep: Separator to use between nested keys
            
        Returns:
            List of dictionaries with flattened data
        """
        items = []
        
        def flatten(obj: Any, parent_key: str = '', sep: str = '.') -> Dict:
            """Recursively flatten nested objects."""
            flat_dict = {}
            
            if isinstance(obj, dict):
                for key, value in obj.items():
                    new_key = f"{parent_key}{sep}{key}" if parent_key else key
                    if isinstance(value, (dict, list)):
                        flat_dict.update(flatten(value, new_key, sep))
                    else:
                        flat_dict[new_key] = value
            elif isinstance(obj, list):
                for i, value in enumerate(obj):
                    new_key = f"{parent_key}{sep}{i}" if parent_key else str(i)
                    if isinstance(value, (dict, list)):
                        flat_dict.update(flatten(value, new_key, sep))
                    else:
                        flat_dict[new_key] = value
            else:
                flat_dict[parent_key] = obj
                
            return flat_dict
        
        # Handle both list and dict inputs
        if isinstance(data, list):
            for item in data:
                items.append(flatten(item))
        else:
            items.append(flatten(data))
            
        return items
    
    def process_file(self, file_path: str) -> Dict[str, Any]:
        """
        Process a JSON file and extract structured information.
        
        Args:
            file_path: Path to the JSON file
            
        Returns:
            Dictionary containing:
                - type: "json"
                - path: file path
                - data: parsed JSON data
                - error: error message if processing failed
        """
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # Convert data to rows for DataFrame
            rows = self.to_csv(data)
            
            # Create DataFrame with file info
            df = pd.DataFrame(rows)
            df['filepath'] = str(Path(file_path).absolute())
            df['type'] = 'application/json'
            
            # Update results DataFrame
            self.results_df = df
            
            return {
                'type': 'json',
                'path': file_path,
                'data': data
            }
            
        except Exception as e:
            return {
                'type': 'json',
                'path': file_path,
                'error': str(e)
            }

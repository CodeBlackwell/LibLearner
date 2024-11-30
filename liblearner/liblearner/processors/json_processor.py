"""JSON processor for LibLearner.
Handles extraction of information from JSON files.
"""

import json
import logging
import pandas as pd
from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional
from pathlib import Path
from ..file_processor import FileProcessor, ProcessingResult

logger = logging.getLogger(__name__)

@dataclass
class JSONProcessingResult(ProcessingResult):
    """Result class for JSON processing."""
    elements: List[Dict] = field(default_factory=list)
    errors: List[str] = field(default_factory=list)
    file_info: Dict = field(default_factory=dict)
    raw_data: Optional[Any] = None

    def is_valid(self) -> bool:
        """Check if the processing result is valid."""
        return len(self.errors) == 0 and self.raw_data is not None

class JSONProcessor(FileProcessor):
    """Processor for JSON files."""
    
    def __init__(self, debug: bool = False):
        """Initialize the JSON processor."""
        super().__init__()
        self.debug = debug
        if self.debug:
            logger.setLevel(logging.DEBUG)
        self.results_df = pd.DataFrame()
        self._order_counter = 0
    
    def get_supported_types(self) -> List[str]:
        """Return list of supported MIME types."""
        return [
            'application/json',
            'text/json'
        ]
    
    def _validate_content(self, content: str) -> List[str]:
        """Validate JSON content before processing."""
        errors = []
        try:
            json.loads(content)
        except json.JSONDecodeError as e:
            errors.append(f"Invalid JSON format: {str(e)}")
        return errors
    
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
    
    def process_file(self, file_path: str) -> JSONProcessingResult:
        """
        Process a JSON file and extract structured information.
        
        Args:
            file_path: Path to the JSON file
            
        Returns:
            JSONProcessingResult containing processing results and any errors
        """
        # Reset counters for new file
        self._order_counter = 0
        
        path = Path(file_path)
        result = JSONProcessingResult()
        
        # Add file metadata
        result.file_info = {
            'name': path.name,
            'path': str(path.absolute()),
            'size': path.stat().st_size,
            'last_modified': path.stat().st_mtime
        }
        
        try:
            # Read and validate content
            content = path.read_text(encoding='utf-8')
            validation_errors = self._validate_content(content)
            if validation_errors:
                for error in validation_errors:
                    result.errors.append(error)
                    logger.warning(f"Validation error in {file_path}: {error}")
                return result
            
            # Parse JSON
            data = json.loads(content)
            result.raw_data = data
            
            # Convert data to rows for DataFrame
            results_data = []
            rows = self.to_csv(data)
            
            for row in rows:
                self._order_counter += 1
                processed_row = {
                    'filepath': str(path.absolute()),
                    'parent_path': str(path.parent),
                    'order': self._order_counter,
                    'name': path.name,
                    'content': json.dumps(row),
                    'props': row,
                    'processor_type': 'json'
                }
                results_data.append(processed_row)
                result.elements.append(row)
            
            # Create DataFrame with standard columns
            if results_data:
                df = pd.DataFrame(results_data)
                column_order = ['filepath', 'parent_path', 'order', 'name', 'content', 'props', 'processor_type']
                df = df[column_order]
                
                # Concatenate with existing results
                if not self.results_df.empty:
                    self.results_df = pd.concat([self.results_df, df], ignore_index=True)
                else:
                    self.results_df = df
            
        except Exception as e:
            error_msg = f"Error processing {file_path}: {str(e)}"
            result.errors.append(error_msg)
            logger.error(error_msg)
        
        return result

"""Jupyter notebook processor for LibLearner.
Handles extraction of information from Jupyter notebook files.
"""

import nbformat
import pandas as pd
from typing import List, Dict, Any, Union
from ..file_processor import FileProcessor

class JupyterProcessor(FileProcessor):
    """Processor for Jupyter notebook files."""
    result_data = []
    
    def __init__(self):
        """Initialize the Jupyter processor."""
        super().__init__()
    
    def get_supported_types(self) -> List[str]:
        """Return list of supported MIME types."""
        return [
            'application/x-ipynb+json'
        ]
    
    def process_file(self, file_path: str) -> Dict[str, Any]:
        """
        Process a Jupyter notebook file and extract cell information.
        
        Args:
            file_path: Path to the notebook file
            
        Returns:
            Dictionary containing:
                - type: "jupyter"
                - path: file path
                - cells: list of cell information
                - error: error message if processing failed
        """
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                nb = nbformat.read(f, as_version=4)
            
            cells = []
            results_data = []
            
            for idx, cell in enumerate(nb.cells):
                cell_info = {
                    "cell_type": cell.cell_type,
                    "source": "".join(cell.source) if isinstance(cell.source, list) else cell.source
                }
                
                # Add execution count for code cells
                if cell.cell_type == "code":
                    cell_info["execution_count"] = cell.execution_count
                    cell_info["outputs"] = cell.outputs
                
                # Add metadata if present
                if hasattr(cell, 'metadata') and cell.metadata:
                    cell_info["metadata"] = cell.metadata
                
                cells.append(cell_info)
                
                # Add to results DataFrame
                results_data.append({
                    'type': cell.cell_type,
                    'name': f'cell_{idx}',
                    'content': cell_info['source'],
                    'props': str({
                        'execution_count': cell_info.get('execution_count'),
                        'metadata': cell_info.get('metadata', {}),
                        'has_output': bool(cell_info.get('outputs', []))
                    })
                })
            
            # Update the results DataFrame
            self.results_df = pd.DataFrame(results_data)
            
            return {
                "type": "jupyter",
                "path": file_path,
                "cells": cells
            }
            
        except FileNotFoundError as e:
            self.results_df = pd.DataFrame(columns=['type', 'name', 'content', 'props'])
            return {
                "type": "jupyter",
                "path": file_path,
                "cells": [],
                "error": f"File not found: {str(e)}"
            }
        except Exception as e:
            self.results_df = pd.DataFrame(columns=['type', 'name', 'content', 'props'])
            return {
                "type": "jupyter",
                "path": file_path,
                "cells": [],
                "error": str(e)
            }
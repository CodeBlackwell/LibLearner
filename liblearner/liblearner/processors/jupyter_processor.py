"""Jupyter notebook processor for LibLearner.
Handles extraction of information from Jupyter notebook files.
"""

import nbformat
from typing import List, Dict, Any, Union
from ..file_processor import FileProcessor

class JupyterProcessor(FileProcessor):
    """Processor for Jupyter notebook files."""
    
    def get_supported_types(self) -> List[str]:
        """Return list of supported MIME types."""
        return [
            'application/x-ipynb+json',
            'application/json'
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
            for cell in nb.cells:
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
            
            return {
                "type": "jupyter",
                "path": file_path,
                "cells": cells
            }
            
        except FileNotFoundError as e:
            return {
                "type": "jupyter",
                "path": file_path,
                "cells": [],
                "error": f"File not found: {str(e)}"
            }
        except Exception as e:
            return {
                "type": "jupyter",
                "path": file_path,
                "cells": [],
                "error": str(e)
            }
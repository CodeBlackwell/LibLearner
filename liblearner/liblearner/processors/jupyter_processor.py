"""
Jupyter Notebook Processor for LibLearner.

This processor extracts structured information from Jupyter notebooks (.ipynb files), including:
- Cell contents and types
- Cell metadata
- Notebook metadata
- Code execution order
- Cell outputs
"""

import json
import logging
from pathlib import Path
from typing import List, Dict, Any

import pandas as pd

from ..file_processor import FileProcessor
from ..processing_result import JupyterProcessingResult

logger = logging.getLogger(__name__)

class JupyterProcessor(FileProcessor):
    """Processor for Jupyter notebook files."""
    
    def __init__(self, debug: bool = False):
        """Initialize the Jupyter notebook processor."""
        super().__init__()
        self.debug = debug
        if self.debug:
            logger.setLevel(logging.DEBUG)
            
        # Initialize results DataFrame
        self.results_df = pd.DataFrame()
            
        # Define supported MIME types
        self.supported_types = {
            'application/x-ipynb+json',
            'application/x-jupyter',
            'text/x-ipynb+json'
        }
        
        # Initialize tracking variables
        self._order_counter = 0
        self._current_path = []
        
    def get_supported_types(self) -> List[str]:
        """Return list of supported MIME types."""
        return list(self.supported_types)
        
    def process_file(self, file_path: str) -> JupyterProcessingResult:
        """Process a Jupyter notebook and extract structured information."""
        # Reset counters for new file
        self._order_counter = 0
        self._current_path = []
        
        path = Path(file_path)
        result = JupyterProcessingResult()
        results_data = []

        # Validate file exists
        if not path.exists():
            error_msg = f"File not found: {file_path}"
            result.errors.append(error_msg)
            logger.error(error_msg)
            return result

        try:
            # Add file metadata
            result.file_info = {
                'name': path.name,
                'path': str(path.absolute()),
                'size': path.stat().st_size,
                'last_modified': path.stat().st_mtime
            }
        except Exception as e:
            error_msg = f"Error getting file info: {str(e)}"
            result.errors.append(error_msg)
            logger.error(error_msg)
            return result

        try:
            # Read and parse notebook
            with path.open('r', encoding='utf-8') as f:
                notebook = json.load(f)
                
            # Extract notebook metadata
            result.metadata = notebook.get('metadata', {})
            
            # Process cells
            self._process_cells(notebook.get('cells', []), result, results_data, file_path)
            
        except json.JSONDecodeError as e:
            error_msg = f"Invalid JSON in notebook: {str(e)}"
            result.errors.append(error_msg)
            logger.error(error_msg)
            return result
        except Exception as e:
            error_msg = f"Error processing notebook: {str(e)}"
            result.errors.append(error_msg)
            logger.error(error_msg)
            return result

        # Create DataFrame from results
        if results_data:
            try:
                df = pd.DataFrame(results_data)
                df = df.rename(columns={'type': 'processor_type'})
                column_order = ['filepath', 'parent_path', 'order', 'name', 
                              'content', 'props', 'processor_type']
                df = df[column_order]
                
                # Concatenate with existing results
                if not self.results_df.empty:
                    self.results_df = pd.concat([self.results_df, df], ignore_index=True)
                else:
                    self.results_df = df
            except Exception as e:
                error_msg = f"Error creating DataFrame: {str(e)}"
                result.errors.append(error_msg)
                logger.error(error_msg)

        return result
        
    def _process_cells(self, cells: List[Dict[str, Any]], result: JupyterProcessingResult,
                      results_data: List[Dict], file_path: str) -> None:
        """Process notebook cells."""
        for idx, cell in enumerate(cells):
            self._order_counter += 1
            
            # Extract cell information
            cell_type = cell.get('cell_type', 'unknown')
            cell_source = ''.join(cell.get('source', []))
            cell_metadata = cell.get('metadata', {})
            execution_count = cell.get('execution_count')
            outputs = cell.get('outputs', [])
            
            # Create cell name based on type and index
            cell_name = f"cell_{idx}_{cell_type}"
            if execution_count is not None:
                cell_name = f"{cell_name}_[{execution_count}]"
            
            # Create cell properties
            props = {
                'cell_type': cell_type,
                'metadata': cell_metadata,
                'execution_count': execution_count,
                'output_types': [out.get('output_type') for out in outputs],
                'has_outputs': bool(outputs)
            }
            
            # Create cell info
            cell_info = {
                'name': cell_name,
                'type': 'cell',
                'content': cell_source,
                'props': str(props),
                'filepath': file_path,
                'parent_path': '',  # Cells are top-level elements
                'order': self._order_counter
            }
            
            # Add to results
            result.cells.append(cell_info)
            results_data.append(cell_info)
            
            # If it's a code cell, also process its outputs
            if cell_type == 'code' and outputs:
                self._process_outputs(outputs, cell_name, result, results_data, file_path)
                
    def _process_outputs(self, outputs: List[Dict[str, Any]], parent_cell: str,
                        result: JupyterProcessingResult, results_data: List[Dict],
                        file_path: str) -> None:
        """Process cell outputs."""
        for idx, output in enumerate(outputs):
            self._order_counter += 1
            
            output_type = output.get('output_type', 'unknown')
            output_name = f"{parent_cell}_output_{idx}_{output_type}"
            
            # Extract output content based on type
            content = ''
            if output_type == 'stream':
                content = ''.join(output.get('text', []))
            elif output_type == 'execute_result':
                content = str(output.get('data', {}))
            elif output_type == 'display_data':
                content = str(output.get('data', {}))
            elif output_type == 'error':
                content = '\n'.join(output.get('traceback', []))
                
            # Create output properties
            props = {
                'output_type': output_type,
                'metadata': output.get('metadata', {}),
                'execution_count': output.get('execution_count')
            }
            
            # Create output info
            output_info = {
                'name': output_name,
                'type': 'output',
                'content': content,
                'props': str(props),
                'filepath': file_path,
                'parent_path': parent_cell,  # Outputs are nested under cells
                'order': self._order_counter
            }
            
            # Add to results
            result.cells.append(output_info)  # Store outputs in cells list
            results_data.append(output_info)

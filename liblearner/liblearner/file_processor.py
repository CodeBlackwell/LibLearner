"""
File type detection and processing module for LibLearner.
Handles detection of file types and routing to appropriate processors.
"""

import os
import mimetypes
import magic  # python-magic library for robust file type detection
from typing import Optional, Dict, Type, List, Union
from abc import ABC, abstractmethod
import sys
from pathlib import Path
from collections import defaultdict
import pandas as pd

# Default directories to ignore
DEFAULT_IGNORE_DIRS = {"venv", ".git", "ds_venv", "dw_env", "__pycache__", ".venv", "*.egg-info"}

class FileProcessor(ABC):
    """Base class for file processors."""
    
    def __init__(self):
        """Initialize the processor with an empty dataframe."""
        self.results_df = pd.DataFrame()
    
    @abstractmethod
    def get_supported_types(self) -> List[str]:
        """
        Returns the MIME types this processor can handle.
        
        Returns:
            List of supported MIME types
        """
        pass
    
    @abstractmethod
    def process_file(self, file_path: str) -> Union[dict, str]:
        """
        Process a file and extract information.
        
        Args:
            file_path: Path to the file to process
            
        Returns:
            Either:
            - Dictionary containing extracted information for function-based processors
            - String path to the CSV file for cell-based processors
            - None if processing failed
        """
        pass

    def get_results_dataframe(self) -> pd.DataFrame:
        """
        Get the results dataframe for this processor.
        
        Returns:
            pandas DataFrame containing the processing results
        """
        return self.results_df

class FileTypeDetector:
    """Handles file type detection using multiple methods."""
    
    def __init__(self):
        """Initialize the detector with magic library."""
        self._magic = magic.Magic(mime=True)
        
        # Define strict mappings for file extensions
        self._extension_mime_types = {
            '.py': 'text/x-python',
            '.pyi': 'text/x-python',
            '.ipynb': 'application/x-ipynb+json',
            '.txt': 'text/plain',
            '.md': 'text/markdown',
            '.json': 'application/json',
            '.yaml': 'text/x-yaml',
            '.yml': 'text/x-yaml',
            '.js': 'application/javascript'
        }
    
    def detect_type(self, file_path: str) -> str:
        """
        Detect the MIME type of a file using multiple methods.
        
        Args:
            file_path: Path to the file
            
        Returns:
            MIME type string
        """
        # Get file extension
        extension = Path(file_path).suffix.lower()
        
        # First check our strict extension mappings
        if extension in self._extension_mime_types:
            return self._extension_mime_types[extension]
            
        # Try magic library
        try:
            mime_type = self._magic.from_file(file_path)
            if mime_type:
                return mime_type
        except Exception as e:
            print(f"Warning: Magic library failed for {file_path}: {str(e)}")
        
        # Fallback to mimetypes library
        mime_type, _ = mimetypes.guess_type(file_path)
        return mime_type if mime_type else 'application/octet-stream'

class ProcessorRegistry:
    """Registry for file processors."""
    
    def __init__(self):
        """Initialize registry and file type detector."""
        self._processors = {}
        self._detector = FileTypeDetector()
        self._verbose = False
        self._results = defaultdict(lambda: defaultdict(pd.DataFrame))
    
    def set_verbose(self, verbose: bool) -> None:
        """Set verbose mode for debug output."""
        self._verbose = verbose
    
    def _debug(self, message: str) -> None:
        """Print debug message if verbose mode is enabled."""
        if self._verbose:
            print(f"DEBUG: {message}")
    
    def register_processor(self, processor: Union[Type[FileProcessor], FileProcessor]) -> None:
        """Register a processor for its supported MIME types.
        
        Args:
            processor: Either a FileProcessor class or instance
        """
        if isinstance(processor, type):
            processor_instance = processor()
        else:
            processor_instance = processor
            
        for mime_type in processor_instance.get_supported_types():
            self._debug(f"Registering processor for MIME type: {mime_type}")
            self._processors[mime_type] = processor_instance
    
    def get_processor(self, file_path: str) -> Optional[FileProcessor]:
        """Get appropriate processor for a file."""
        mime_type = self._detector.detect_type(file_path)
        
        # For text/plain files, check extension first
        if mime_type == 'text/plain':
            ext = Path(file_path).suffix.lower()
            if ext == '.py':
                mime_type = 'text/x-python'
            else:
                self._debug(f"Skipping non-Python text file: {file_path}")
                return None
        
        processor = self._processors.get(mime_type)
        self._debug(f"Looking for processor for {mime_type}, found: {processor is not None}")
        return processor
    
    def process_file(self, file_path: str) -> Optional[Union[dict, str]]:
        """Process a single file using appropriate processor."""
        processor = self.get_processor(file_path)
        if processor:
            try:
                result = processor.process_file(file_path)
                if result:
                    # Store the dataframe in the results dictionary
                    file_type = self._detector.detect_type(file_path)
                    filename = os.path.basename(file_path)
                    self._results[file_type][filename] = processor.get_results_dataframe()
                self._debug(f"Successfully processed {file_path}")
                return result
            except Exception as e:
                self._debug(f"Error processing {file_path}: {str(e)}")
                return None
        return None

    def get_results(self) -> Dict[str, Dict[str, pd.DataFrame]]:
        """
        Get all processing results organized by file type and filename.
        
        Returns:
            Dictionary mapping file types to dictionaries of filename -> DataFrame
        """
        return dict(self._results)

    def write_results_to_csv(self, output_dir: str, combined: bool = True) -> None:
        """
        Write processing results to CSV files.
        
        Args:
            output_dir: Directory to write CSV files to
            combined: If True, create a single combined CSV for all file types.
                     If False, create separate CSVs for each file type.
        """
        os.makedirs(output_dir, exist_ok=True)
        
        if combined:
            # Combine all dataframes into one
            all_dfs = []
            for file_type, file_dict in self._results.items():
                for filename, df in file_dict.items():
                    df = df.copy()
                    df['file_type'] = file_type
                    df['filename'] = filename
                    all_dfs.append(df)
            
            if all_dfs:
                combined_df = pd.concat(all_dfs, ignore_index=True)
                # Reorder columns to put file_type and filename first
                cols = ['file_type', 'filename', 'type', 'name', 'content', 'props']
                combined_df = combined_df[cols]
                output_path = os.path.join(output_dir, 'all_results.csv')
                combined_df.to_csv(output_path, index=False)
                self._debug(f"Written combined results to {output_path}")
        else:
            # Write separate CSV for each file type
            for file_type, file_dict in self._results.items():
                file_dfs = []
                for filename, df in file_dict.items():
                    df = df.copy()
                    df['filename'] = filename
                    file_dfs.append(df)
                
                if file_dfs:
                    file_type_df = pd.concat(file_dfs, ignore_index=True)
                    # Reorder columns to put filename first
                    cols = ['filename', 'type', 'name', 'content', 'props']
                    file_type_df = file_type_df[cols]
                    
                    # Create a safe filename from the MIME type
                    safe_name = file_type.replace('/', '_').replace('+', '_')
                    output_path = os.path.join(output_dir, f'{safe_name}_results.csv')
                    file_type_df.to_csv(output_path, index=False)
                    self._debug(f"Written {file_type} results to {output_path}")

    def process_directory(self, directory_path: str, ignore_dirs: Optional[List[str]] = None) -> Dict[str, List[Union[dict, str]]]:
        """
        Process all files in a directory recursively.
        
        Args:
            directory_path: Path to the directory to process
            ignore_dirs: List of directory names to ignore (in addition to DEFAULT_IGNORE_DIRS)
        
        Returns:
            Dictionary mapping relative paths to lists of processing results
        """
        results = defaultdict(list)
        
        # Split ignore patterns into exact matches and glob patterns
        exact_ignores = set()
        glob_patterns = set()
        
        # Process default ignore dirs
        for pattern in DEFAULT_IGNORE_DIRS:
            if '*' in pattern:
                glob_patterns.add(pattern)
            else:
                exact_ignores.add(pattern)
        
        # Add user-provided ignore dirs
        if ignore_dirs:
            for pattern in ignore_dirs:
                if '*' in pattern:
                    glob_patterns.add(pattern)
                else:
                    exact_ignores.add(pattern)

        for root, dirs, files in os.walk(directory_path):
            # Remove directories that match exact names or glob patterns
            dirs[:] = [d for d in dirs 
                      if d not in exact_ignores 
                      and not any(part in exact_ignores for part in Path(d).parts)
                      and not any(Path(d).match(pattern) for pattern in glob_patterns)]
            
            # Get relative path from input directory
            rel_path = os.path.relpath(root, directory_path)
            rel_path = '.' if rel_path == '.' else rel_path
            
            # Skip if current directory matches any glob pattern
            if any(Path(root).match(pattern) for pattern in glob_patterns):
                continue
            
            for file in files:
                file_path = os.path.join(root, file)
                result = self.process_file(file_path)
                if result:
                    results[rel_path].append(result)
        
        return dict(results)

# Global registry instance
registry = ProcessorRegistry()

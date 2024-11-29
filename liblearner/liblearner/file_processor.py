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
from .processing_result import ProcessingResult

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
    def process_file(self, file_path: str) -> ProcessingResult:
        """
        Process a file and extract information.
        
        Args:
            file_path: Path to the file to process
            
        Returns:
            ProcessingResult containing extracted information
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
            '.pyw': 'text/x-python-executable',
            '.ipynb': 'application/x-ipynb+json',
            '.txt': 'text/plain',
            '.md': 'text/markdown',
            '.mdx': 'text/mdx',
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
        if not os.path.exists(file_path) or os.path.isdir(file_path):
            return ''

        # First try extension mapping for known types
        ext = os.path.splitext(file_path)[1].lower()
        if ext in self._extension_mime_types:
            return self._extension_mime_types[ext]

        # For empty files, use extension mapping or default to text/plain
        if os.path.getsize(file_path) == 0:
            if ext == '.py':
                return 'text/x-python'
            if ext == '.pyw':
                return 'text/x-python-executable'
            if ext == '.md':
                return 'text/markdown'
            if ext == '.mdx':
                return 'text/mdx'
            if ext == '.js':
                return 'text/javascript'
            if ext in ['.yaml', '.yml']:
                return 'text/x-yaml'
            if ext == '.ipynb':
                return 'application/x-ipynb+json'
            return 'text/plain'

        # Try python-magic for more accurate detection
        try:
            return self._magic.from_file(file_path)
        except Exception as e:
            # If magic fails, fall back to mimetypes
            mime_type, _ = mimetypes.guess_type(file_path)
            return mime_type or 'application/octet-stream'

class ProcessorRegistry:
    """Registry for file processors."""
    
    def __init__(self):
        """Initialize registry and file type detector."""
        self._processors = {}  # MIME type -> processor mapping
        self._unique_processors = set()  # Set of unique processor instances
        self._detector = FileTypeDetector()
        self._verbose = False
        self._results = defaultdict(lambda: defaultdict(pd.DataFrame))
        self._processed_files = set()  # Track processed files by absolute path
    
    def set_verbose(self, verbose: bool) -> None:
        """Set verbose mode for debug output."""
        self._verbose = verbose
    
    def _debug(self, message: str) -> None:
        """Print debug message if verbose mode is enabled."""
        if self._verbose:
            print(f"DEBUG: {message}", file=sys.stderr)
    
    def register_processor(self, processor: Union[Type[FileProcessor], FileProcessor]) -> None:
        """Register a processor for its supported MIME types.
        
        Args:
            processor: Either a FileProcessor class or instance
        """
        if isinstance(processor, type):
            processor = processor()
        
        # Add to unique processors set
        self._unique_processors.add(processor)
        
        for mime_type in processor.get_supported_types():
            self._debug(f"Registering processor for MIME type: {mime_type}")
            self._processors[mime_type] = processor

    def get_unique_processors(self) -> List[FileProcessor]:
        """Get list of unique processor instances."""
        return list(self._unique_processors)
    
    def get_processor(self, file_path: str) -> Optional[FileProcessor]:
        """Get appropriate processor for a file."""
        try:
            mime_type = self._detector.detect_type(file_path)
            
            # For text/plain files, check extension first. Many files return text/plain
            # each extension that potentially does requires a different processor and condition.
            if mime_type == 'text/plain':
                ext = Path(file_path).suffix.lower()
                if ext == '.py':
                    mime_type = 'text/x-python'
                elif ext in ['.yaml', '.yml']:
                    mime_type = 'text/x-yaml'
                elif ext == '.json':
                    # Check if it's a Jupyter notebook by looking for nbformat
                    try:
                        with open(file_path, 'r') as f:
                            import json
                            content = json.load(f)
                            if 'nbformat' in content:
                                mime_type = 'application/x-ipynb+json'
                            else:
                                mime_type = 'application/json'
                    except:
                        mime_type = 'application/json'
                elif ext in ['.md', '.markdown']:
                    mime_type = 'text/markdown'
                elif ext == '.rst':
                    mime_type = 'text/x-rst'
                elif ext == '.ini':
                    mime_type = 'text/x-ini'
                elif ext == '.toml':
                    mime_type = 'text/x-toml'
                elif ext == '.js':
                    mime_type = 'application/javascript'
                elif ext == '.ipynb':
                    mime_type = 'application/x-ipynb+json'
                else:
                    self._debug(f"Skipping unsupported text file: {file_path}")
                    return None
            elif mime_type == 'application/json':
                # Check if it's a Jupyter notebook by looking for nbformat
                try:
                    with open(file_path, 'r') as f:
                        import json
                        content = json.load(f)
                        if 'nbformat' in content:
                            mime_type = 'application/x-ipynb+json'
                except:
                    pass
            
            processor = self._processors.get(mime_type)
            self._debug(f"Looking for processor for {mime_type}, found: {processor is not None}")
            return processor
        
        except Exception as e:
            if self._verbose:
                raise RuntimeError(f"Error determining processor for file {file_path}: {str(e)}")
            return None
    
    def process_file(self, file_path: str) -> Optional[ProcessingResult]:
        """Process a single file using appropriate processor."""
        abs_path = str(Path(file_path).resolve())
        
        # Check if file has already been processed
        if abs_path in self._processed_files:
            self._debug(f"Skipping already processed file: {file_path}")
            return None
            
        try:
            processor = self.get_processor(file_path)
        except Exception as e:
            self._debug(f"Error getting processor for {file_path}: {str(e)}")
            return None
        
        if processor:
            try:
                result = processor.process_file(file_path)
                if result and result.is_valid():
                    # Store the dataframe in the results dictionary
                    file_type = self._detector.detect_type(file_path)
                    filename = os.path.basename(file_path)
                    self._results[file_type][filename] = processor.get_results_dataframe()
                    # Mark file as processed
                    self._processed_files.add(abs_path)
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
            # Combine all DataFrames
            all_dfs = []
            for file_type, files_dict in self._results.items():
                for filename, df in files_dict.items():
                    if not df.empty:
                        df = df.copy()
                        df['file_type'] = file_type
                        df['filename'] = filename
                        all_dfs.append(df)
            
            if all_dfs:
                combined_df = pd.concat(all_dfs, ignore_index=True)
                output_path = os.path.join(output_dir, 'combined_results.csv')
                combined_df.to_csv(output_path, index=False)
                self._debug(f"Written combined results to {output_path}")
        else:
            # Write separate CSV for each file type
            for file_type, files_dict in self._results.items():
                file_type_dfs = []
                for filename, df in files_dict.items():
                    if not df.empty:
                        df = df.copy()
                        df['filename'] = filename
                        file_type_dfs.append(df)
                
                if file_type_dfs:
                    file_type_df = pd.concat(file_type_dfs, ignore_index=True)
                    safe_name = file_type.replace('/', '_').replace('+', '_')
                    output_path = os.path.join(output_dir, f'{safe_name}_results.csv')
                    file_type_df.to_csv(output_path, index=False)
                    self._debug(f"Written {file_type} results to {output_path}")

    def process_directory(self, directory_path: str, ignore_dirs: Optional[List[str]] = None) -> Dict[str, List[ProcessingResult]]:
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
                if result and result.is_valid():
                    results[rel_path].append(result)
        
        return dict(results)

# Global registry instance
registry = ProcessorRegistry()

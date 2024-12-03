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
import logging
from pathlib import Path
from collections import defaultdict
import pandas as pd
from tqdm import tqdm
from .processing_result import ProcessingResult

# Default directories to ignore
DEFAULT_IGNORE_DIRS = {"venv", ".git", "ds_venv", "dw_env", "__pycache__", ".venv", "*.egg-info", ".github", "node_modules", "*tests*"}

# Set up root logger
logger = logging.getLogger('liblearner')
logger.setLevel(logging.WARNING)

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
            '.js': 'application/javascript',
            '.sh': 'application/x-shellscript',
            '.bash': 'application/x-shellscript'
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
            elif ext in ['.sh', '.bash']:
                return 'application/x-shellscript'
            elif ext == '.py':
                return 'text/x-python'
            elif ext == '.js':
                return 'application/javascript'
            elif ext == '.json':
                return 'application/json'
            elif ext in ['.yaml', '.yml']:
                return 'text/x-yaml'
            elif ext == '.md':
                return 'text/markdown'
            else:
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
        self._results_dir = None  # Directory to store intermediate results
        self._processed_files = set()  # Track processed files by absolute path
        self._log_file = None
        self._chunk_size = 20  # Default chunk size
        self._current_chunk = defaultdict(list)  # Current chunk of results
        self._chunk_counter = 0
        self._progress_bar = None
        self._total_files = 0
        self._processed_count = 0

    def set_verbose(self, verbose: bool, log_file: Optional[str] = None) -> None:
        """Set verbose mode for debug output and optionally redirect to file.
        
        Args:
            verbose: Whether to enable verbose output
            log_file: Optional file path to write verbose output to
        """
        self._verbose = verbose
        self._log_file = log_file
        
        # Configure logging
        logger = logging.getLogger('liblearner')
        logger.setLevel(logging.DEBUG if verbose else logging.WARNING)
        
        # Remove existing handlers
        for handler in logger.handlers[:]:
            logger.removeHandler(handler)
        
        # Set up new handler based on configuration
        if verbose:
            if log_file:
                handler = logging.FileHandler(log_file, mode='w')
                formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
            else:
                handler = logging.StreamHandler(sys.stderr)
                formatter = logging.Formatter('%(levelname)s: %(message)s')
            
            handler.setFormatter(formatter)
            logger.addHandler(handler)
        
        # Update debug mode for all registered processors
        for processor in self._unique_processors:
            if hasattr(processor, 'debug'):
                processor.debug = verbose
    
    def set_output_dir(self, output_dir: str) -> None:
        """Set the output directory for intermediate results."""
        self._results_dir = output_dir
        # Create temp directory for chunks
        self._chunk_dir = os.path.join(output_dir, '.chunks')
        os.makedirs(self._chunk_dir, exist_ok=True)
    
    def set_chunk_size(self, size: int) -> None:
        """Set the size of chunks for processing.
        
        Args:
            size: Number of files to process before writing a chunk to disk
        """
        if size < 1:
            raise ValueError("Chunk size must be at least 1")
        self._chunk_size = size
        self._debug(f"Chunk size set to {size} files")
    
    def _debug(self, message: str) -> None:
        """Log debug message if verbose mode is enabled."""
        if self._verbose:
            logger.debug(message)
    
    def _write_chunk(self) -> None:
        """Write current chunk to disk and clear memory."""
        if not self._current_chunk:
            return
        
        chunk_file = os.path.join(self._chunk_dir, f'chunk_{self._chunk_counter}.pkl')
        
        # Write chunk to disk using pickle
        import pickle
        with open(chunk_file, 'wb') as f:
            pickle.dump(dict(self._current_chunk), f)
        
        # Clear current chunk from memory
        self._current_chunk.clear()
        self._chunk_counter += 1
        
        self._debug(f"Wrote chunk {self._chunk_counter} to disk")
    
    def register_processor(self, processor: Union[Type[FileProcessor], FileProcessor]) -> None:
        """Register a processor for its supported MIME types.
        
        Args:
            processor: Either a FileProcessor class or instance
        """
        if isinstance(processor, type):
            processor = processor()
        
        # Set debug mode based on registry's verbose setting
        if hasattr(processor, 'debug'):
            processor.debug = self._verbose
        
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
            self._debug(f"Detected MIME type for {file_path}: {mime_type}")
            
            # For text/plain files, check extension first. Many files return text/plain
            # each extension that potentially does requires a different processor and condition.
            if mime_type == 'text/plain':
                ext = Path(file_path).suffix.lower()
                self._debug(f"File has extension: {ext}")
                if ext == '.py':
                    mime_type = 'text/x-python'
                    self._debug(f"Treating {file_path} as Python file")
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
                elif ext in ['.sh', '.bash']:
                    mime_type = 'application/x-shellscript'
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
    
    def process_file(self, file_path: str) -> Optional[Dict]:
        """Process a single file using appropriate processor."""
        if not os.path.exists(file_path):
            self._debug(f"File not found: {file_path}")
            return None
        
        abs_path = os.path.abspath(file_path)
        if abs_path in self._processed_files:
            self._debug(f"Skipping already processed file: {file_path}")
            return None
        
        processor = self.get_processor(file_path)
        
        if processor:
            try:
                result = processor.process_file(file_path)
                if result and result.is_valid():
                    # Add result to current chunk
                    file_type = self._detector.detect_type(file_path)
                    self._current_chunk[file_type].append({
                        'filename': os.path.basename(file_path),
                        'data': processor.get_results_dataframe()
                    })
                    
                    # Write chunk if it reaches the size limit
                    if len(self._current_chunk) >= self._chunk_size:
                        self._write_chunk()
                    
                    # Mark file as processed
                    self._processed_files.add(abs_path)
                    
                self._debug(f"Successfully processed {file_path}")
                return result
            except Exception as e:
                self._debug(f"Error processing {file_path}: {str(e)}")
                return None
        return None

    def _count_files(self, directory_path: str, ignore_dirs: Optional[List[str]] = None) -> int:
        """Count total number of files to process."""
        total = 0
        exact_ignores = set(DEFAULT_IGNORE_DIRS)
        if ignore_dirs:
            exact_ignores.update(ignore_dirs)

        for root, dirs, files in os.walk(directory_path):
            # Remove ignored directories
            dirs[:] = [d for d in dirs if d not in exact_ignores]
            total += len(files)
        return total

    def process_directory(self, directory_path: str, ignore_dirs: Optional[List[str]] = None) -> Dict[str, List[ProcessingResult]]:
        """Process all files in a directory recursively."""
        self._total_files = self._count_files(directory_path, ignore_dirs)
        self._processed_count = 0
        
        # Initialize progress bar
        self._progress_bar = tqdm(
            total=self._total_files,
            desc="Processing files",
            unit="file",
            position=0,
            leave=True
        )
        
        try:
            results = defaultdict(list)
            unprocessed_files = []
            
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
            
            # Walk through directory
            for root, dirs, files in os.walk(directory_path):
                # Remove ignored directories
                dirs[:] = [d for d in dirs if d not in exact_ignores]
                
                # Process each file
                for file in files:
                    file_path = os.path.join(root, file)
                    try:
                        result = self.process_file(file_path)
                        if result:
                            rel_path = os.path.relpath(root, directory_path)
                            results[rel_path].append(result)
                        else:
                            unprocessed_files.append(file_path)
                    except Exception as e:
                        self._debug(f"Error processing {file_path}: {str(e)}")
                        unprocessed_files.append(file_path)
                    
                    # Update progress
                    self._processed_count += 1
                    if self._progress_bar:
                        self._progress_bar.update(1)
                        self._progress_bar.set_postfix({
                            'chunks': self._chunk_counter,
                            'current_chunk': len(self._current_chunk)
                        })
            
            return dict(results)
        finally:
            # Close progress bar
            if self._progress_bar:
                self._progress_bar.close()
                self._progress_bar = None

    def write_results_to_csv(self, output_dir: str, combined: bool = True) -> None:
        """Write all results to CSV files, combining chunks."""
        os.makedirs(output_dir, exist_ok=True)
        
        # Write final chunk if any
        if self._current_chunk:
            self._write_chunk()
        
        # Process chunks and write results
        all_dfs = defaultdict(list)
        import pickle
        
        # Create progress bar for chunk processing
        chunk_progress = tqdm(
            total=self._chunk_counter,
            desc="Processing chunks",
            unit="chunk",
            position=0,
            leave=True
        )
        
        try:
            # Process each chunk file
            for i in range(self._chunk_counter):
                chunk_file = os.path.join(self._chunk_dir, f'chunk_{i}.pkl')
                try:
                    with open(chunk_file, 'rb') as f:
                        chunk_data = pickle.load(f)
                    
                    # Process each file type in the chunk
                    for file_type, results in chunk_data.items():
                        for result in results:
                            df = result['data']
                            if not df.empty:
                                df = df.copy()
                                df['filename'] = result['filename']
                                if combined:
                                    df['file_type'] = file_type
                                all_dfs[file_type].append(df)
                    
                    # Remove processed chunk file
                    os.remove(chunk_file)
                    chunk_progress.update(1)
                except Exception as e:
                    self._debug(f"Error processing chunk {i}: {str(e)}")
            
            # Write final results with a new progress bar
            if combined:
                combined_dfs = []
                for file_type, dfs in all_dfs.items():
                    if dfs:
                        combined_dfs.extend(dfs)
                
                if combined_dfs:
                    with tqdm(desc="Writing combined results", total=1, leave=True) as pbar:
                        combined_df = pd.concat(combined_dfs, ignore_index=True)
                        output_path = os.path.join(output_dir, 'combined_results.csv')
                        combined_df.to_csv(output_path, index=False)
                        pbar.update(1)
                        self._debug(f"Written combined results to {output_path}")
            else:
                with tqdm(desc="Writing type-specific results", total=len(all_dfs), leave=True) as pbar:
                    for file_type, dfs in all_dfs.items():
                        if dfs:
                            file_type_df = pd.concat(dfs, ignore_index=True)
                            safe_name = file_type.replace('/', '_').replace('+', '_')
                            output_path = os.path.join(output_dir, f'{safe_name}_results.csv')
                            file_type_df.to_csv(output_path, index=False)
                            pbar.update(1)
                            self._debug(f"Written {file_type} results to {output_path}")
        finally:
            chunk_progress.close()
            
            # Clean up chunk directory
            try:
                import shutil
                shutil.rmtree(self._chunk_dir)
            except Exception as e:
                self._debug(f"Error cleaning up chunk directory: {str(e)}")

# Global registry instance
registry = ProcessorRegistry()

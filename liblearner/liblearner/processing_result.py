"""
Common result types for LibLearner processors.
"""

from typing import Dict, List, Any
from dataclasses import dataclass, field

@dataclass
class ProcessingResult:
    """Base class for all processing results."""
    errors: List[str] = field(default_factory=list)
    file_info: Dict[str, Any] = field(default_factory=dict)

    def is_valid(self) -> bool:
        """Check if the processing result is valid (has no errors)."""
        return len(self.errors) == 0

@dataclass
class PythonProcessingResult(ProcessingResult):
    """Result object for Python processing."""
    functions: List[Dict] = field(default_factory=list)
    classes: List[Dict] = field(default_factory=list)

@dataclass
class JupyterProcessingResult(ProcessingResult):
    """Result object for Jupyter notebook processing."""
    cells: List[Dict] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)

@dataclass
class YAMLProcessingResult(ProcessingResult):
    """Result object for YAML processing."""
    data: Dict[str, Any] = field(default_factory=dict)

@dataclass
class JSONProcessingResult(ProcessingResult):
    """Result object for JSON processing."""
    data: Dict[str, Any] = field(default_factory=dict)

@dataclass
class MarkdownProcessingResult(ProcessingResult):
    """Result object for Markdown processing."""
    sections: List[Dict] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)

@dataclass
class JavaScriptProcessingResult(ProcessingResult):
    """Result object for JavaScript processing."""
    functions: List[Dict] = field(default_factory=list)
    classes: List[Dict] = field(default_factory=list)
    exports: List[Dict] = field(default_factory=list)

@dataclass
class ShellProcessingResult(ProcessingResult):
    """Result object for shell script processing.
    
    Stores structured information extracted from shell scripts including:
    - Functions
    - Variables
    - Aliases
    - Source/Include statements
    - Comments and documentation
    """
    functions: List[Dict] = field(default_factory=list)
    variables: List[Dict] = field(default_factory=list)
    aliases: List[Dict] = field(default_factory=list)
    sources: List[Dict] = field(default_factory=list)
    errors: List[str] = field(default_factory=list)
    file_info: Dict = field(default_factory=dict)
    
    def is_valid(self) -> bool:
        """Check if the processing result is valid."""
        return True  # Shell scripts can be valid even without functions/variables

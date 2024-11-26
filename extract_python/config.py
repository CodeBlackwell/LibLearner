"""Configuration management for the code analysis library."""

from dataclasses import dataclass
from typing import List, Optional
from pathlib import Path


@dataclass
class AnalyzerConfig:
    """Configuration settings for code analysis."""

    excluded_directories: List[str] = None
    csv_output_dir: Optional[Path] = None

    def __post_init__(self):
        """Initialize default values if none provided."""
        if self.excluded_directories is None:
            self.excluded_directories = ["node_modules", ".git", "venv", "__pycache__"]

    @classmethod
    def from_dict(cls, config_dict: dict) -> "AnalyzerConfig":
        """Create config from dictionary."""
        return cls(**config_dict)


@dataclass
class OutputConfig:
    """Configuration for output handling."""

    output_format: str = "dataframe"  # 'dataframe' or 'csv'
    csv_filename_template: str = "{name}.csv"
    output_directory: Optional[Path] = None

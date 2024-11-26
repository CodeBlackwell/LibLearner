"""Code analyzer module for analyzing Python source code."""

from pathlib import Path
import logging
from typing import Dict, Optional, Union

import pandas as pd

from .dataframe_tree import DataframeTree
from .config import AnalyzerConfig, OutputConfig
from .exceptions import InvalidPathError, OutputError

logger = logging.getLogger(__name__)


class CodeAnalyzer:
    """
    Analyzes code and generates a dataframe tree representation.

    Args:
        input_path: Path to the code directory or file to analyze
        config: Configuration settings for the analyzer
        output_config: Configuration for output handling

    Raises:
        InvalidPathError: If the input path is invalid
        ConfigurationError: If the configuration is invalid

    Usage Example:
    --------------
    >>> config = AnalyzerConfig(excluded_directories=['venv'])
    >>> output_config = OutputConfig(output_format='csv')
    >>> analyzer = CodeAnalyzer("path/to/code", config, output_config)
    >>> result = analyzer.analyze()
    """

    def __init__(
        self,
        input_path: Union[str, Path],
        config: Optional[AnalyzerConfig] = None,
        output_config: Optional[OutputConfig] = None,
    ):
        self.input_path = Path(input_path)
        self.config = config or AnalyzerConfig()
        self.output_config = output_config or OutputConfig()

        if not self.input_path.exists():
            raise InvalidPathError(f"Path does not exist: {self.input_path}")

        logger.debug(f"Initialized CodeAnalyzer with path: {self.input_path}")

    def analyze(self) -> Dict[str, pd.DataFrame]:
        """
        Analyzes the code and returns a dataframe tree.

        Returns:
            Dict mapping file paths to their corresponding DataFrames

        Raises:
            OutputError: If there's an error generating output files
        """
        logger.info(f"Starting analysis of {self.input_path}")

        try:
            dataframe_tree = DataframeTree(
                self.input_path, excluded_dirs=self.config.excluded_directories
            ).generate_dataframe_tree()

            if self.output_config.output_format == "csv":
                self._save_to_csv(dataframe_tree)

            logger.info("Analysis completed successfully")
            return dataframe_tree

        except Exception as e:
            logger.error(f"Error during analysis: {str(e)}")
            raise

    def _save_to_csv(self, dataframe_tree: Dict[str, pd.DataFrame]) -> None:
        """Save DataFrames to CSV files."""
        output_dir = self.output_config.output_directory or Path.cwd()
        output_dir.mkdir(parents=True, exist_ok=True)

        try:
            for rel_path, df in dataframe_tree.items():
                output_name = self.output_config.csv_filename_template.format(
                    name=Path(rel_path).stem
                )
                output_path = output_dir / output_name
                df.to_csv(output_path, index=False)
                logger.debug(f"Saved CSV: {output_path}")
        except Exception as e:
            raise OutputError(f"Error saving CSV files: {str(e)}")

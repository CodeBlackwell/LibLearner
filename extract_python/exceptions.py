"""Custom exceptions for the code analysis library."""


class CodeAnalysisError(Exception):
    """Base exception for all code analysis errors."""

    pass


class InvalidPathError(CodeAnalysisError):
    """Raised when an invalid path is provided."""

    pass


class DataFrameGenerationError(CodeAnalysisError):
    """Raised when there's an error generating the DataFrame."""

    pass


class OutputError(CodeAnalysisError):
    """Raised when there's an error with output generation."""

    pass


class ConfigurationError(CodeAnalysisError):
    """Raised when there's an error in configuration."""

    pass

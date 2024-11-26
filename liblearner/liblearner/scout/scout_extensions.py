#!/usr/bin/env python3

import os
import argparse
from collections import Counter
from pathlib import Path
from typing import Dict, List, Set

def analyze_extensions(directory: str, ignore_dirs: List[str] = None) -> Dict[str, int]:
    """
    Analyze file extensions in a directory tree.
    
    Args:
        directory: Path to the directory to analyze
        ignore_dirs: List of directory names to ignore
        
    Returns:
        Dictionary mapping extensions to their counts
    """
    if not os.path.isdir(directory):
        raise FileNotFoundError(f"Directory '{directory}' does not exist")
        
    if ignore_dirs is None:
        ignore_dirs = ['node_modules', 'build', 'dist', '.git']
        
    extensions = Counter()
    
    for root, dirs, files in os.walk(directory):
        # Remove ignored directories
        dirs[:] = [d for d in dirs if d not in ignore_dirs]
        
        for file in files:
            # Get the file extension (lowercase for consistency)
            ext = os.path.splitext(file)[1].lower().lstrip('.')
            if ext:  # Only count files with extensions
                extensions[ext] += 1
                
    return dict(extensions)

def format_extension_report(extensions: Dict[str, int], sort: bool = False) -> str:
    """
    Format the extension analysis into a readable report.
    
    Args:
        extensions: Dictionary mapping extensions to their counts
        sort: Whether to sort extensions by count
        
    Returns:
        Formatted report string
    """
    if not extensions:
        return "No files with extensions found."
        
    # Convert to list of tuples for sorting
    items = list(extensions.items())
    if sort:
        items.sort(key=lambda x: (-x[1], x[0]))  # Sort by count (desc) then name (asc)
        
    # Format the report
    lines = []
    for ext, count in items:
        lines.append(f".{ext:<9} {count:>3} files")
        
    return "\n".join(lines)

def main():
    parser = argparse.ArgumentParser(
        description="Analyze file extensions in a directory tree"
    )
    parser.add_argument(
        "directory",
        help="Directory to analyze"
    )
    parser.add_argument(
        "--sort",
        action="store_true",
        help="Sort extensions by frequency"
    )
    parser.add_argument(
        "--no-empty",
        action="store_true",
        help="Skip files without extensions"
    )
    parser.add_argument(
        "--ignore-dirs",
        nargs="+",
        default=None,
        help="List of directories to ignore"
    )
    
    args = parser.parse_args()
    
    try:
        # Analyze extensions
        extensions = analyze_extensions(args.directory, args.ignore_dirs)
        
        # Generate and print report
        report = format_extension_report(extensions, args.sort)
        print(report)
        
        return 0
        
    except Exception as e:
        print(f"Error: {str(e)}")
        return 1

if __name__ == '__main__':
    exit(main())

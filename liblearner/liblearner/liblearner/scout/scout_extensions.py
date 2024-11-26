#!/usr/bin/env python3

import os
import sys
import argparse
import tempfile
import shutil
import subprocess
from pathlib import Path
from typing import Set, Optional, Dict, List
from collections import Counter

def clone_repo(url: str, target_dir: str) -> bool:
    """
    Clone a git repository to a target directory.
    
    Args:
        url: Git repository URL
        target_dir: Directory to clone into
        
    Returns:
        bool: True if successful, False otherwise
    """
    try:
        subprocess.run(['git', 'clone', url, target_dir], 
                      check=True, 
                      capture_output=True, 
                      text=True)
        return True
    except subprocess.CalledProcessError as e:
        print(f"Error cloning repository: {e.stderr}", file=sys.stderr)
        return False

def get_available_processors() -> Set[str]:
    """
    Get the list of file extensions that LibLearner can currently process.
    
    Returns:
        Set of supported file extensions
    """
    return {'py', 'js', 'ipynb'}  # Current supported types

def analyze_extensions(directory: str, ignore_dirs: Optional[list] = None) -> Dict[str, int]:
    """
    Analyze file extensions in a directory and count their occurrences.
    
    Args:
        directory: Path to the directory to scan
        ignore_dirs: List of directory names to ignore
        
    Returns:
        Dictionary mapping extensions to their count
    """
    if ignore_dirs is None:
        ignore_dirs = ['.git', '__pycache__', 'node_modules', '.venv', 'venv']
        
    if not os.path.exists(directory):
        raise FileNotFoundError(f"Directory '{directory}' does not exist")
        
    extension_counts = Counter()
    
    for root, dirs, files in os.walk(directory):
        # Remove ignored directories
        dirs[:] = [d for d in dirs if d not in ignore_dirs]
        
        for file in files:
            ext = os.path.splitext(file)[1].lstrip('.')
            if ext:  # Only count non-empty extensions
                extension_counts[ext] += 1
    
    return dict(extension_counts)

def report_missing_processors(extensions: Dict[str, int], supported_extensions: Set[str]) -> List[Dict]:
    """
    Generate a report of file types that need processors.
    
    Args:
        extensions: Dictionary of extensions and their counts
        supported_extensions: Set of currently supported extensions
        
    Returns:
        List of dictionaries containing extension info and counts
    """
    missing_processors = []
    for ext, count in extensions.items():
        if ext not in supported_extensions and count >= 5:  # Only report if 5 or more files
            missing_processors.append({
                'extension': ext,
                'count': count,
                'priority': 'High' if count >= 20 else 'Medium' if count >= 10 else 'Low'
            })
    
    return sorted(missing_processors, key=lambda x: x['count'], reverse=True)

def main():
    parser = argparse.ArgumentParser(
        description='Scout file extensions and analyze processor coverage.'
    )
    parser.add_argument(
        'target',
        type=str,
        help='Directory to scan or git repository URL'
    )
    parser.add_argument(
        '--ignore-dirs',
        type=str,
        nargs='+',
        help='Directories to ignore (default: .git __pycache__ node_modules .venv venv)'
    )
    parser.add_argument(
        '--sort',
        action='store_true',
        help='Sort extensions alphabetically'
    )
    parser.add_argument(
        '--no-empty',
        action='store_true',
        help='Skip files without extensions'
    )
    parser.add_argument(
        '--min-count',
        type=int,
        default=5,
        help='Minimum number of files to consider an extension relevant (default: 5)'
    )
    
    args = parser.parse_args()
    
    # Check if target is a git URL
    is_git_url = args.target.startswith(('http://', 'https://', 'git://')) and args.target.endswith('.git')
    
    target_dir = args.target
    temp_dir = None
    
    try:
        if is_git_url:
            print(f"Cloning repository {args.target}...")
            temp_dir = tempfile.mkdtemp()
            if not clone_repo(args.target, temp_dir):
                sys.exit(1)
            target_dir = temp_dir
        else:
            target_dir = os.path.abspath(args.target)
            if not os.path.isdir(target_dir):
                print(f"Error: Directory '{target_dir}' does not exist", file=sys.stderr)
                sys.exit(1)
        
        # Get extension counts
        extensions = analyze_extensions(target_dir, args.ignore_dirs)
        
        # Get available processors
        supported_extensions = get_available_processors()
        
        # Print extension summary
        print("\nFile Extension Summary:")
        print("----------------------")
        ext_list = sorted(extensions.items()) if args.sort else sorted(extensions.items(), key=lambda x: x[1], reverse=True)
        for ext, count in ext_list:
            if not args.no_empty or ext:
                status = "✓" if ext in supported_extensions else "✗"
                print(f"{status} .{ext:<10} {count:>5} files")
        
        # Report missing processors
        missing = report_missing_processors(extensions, supported_extensions)
        if missing:
            print("\nMissing Processors (Priority Report):")
            print("----------------------------------")
            for proc in missing:
                print(f"[{proc['priority']:^6}] .{proc['extension']:<10} {proc['count']:>5} files")
        else:
            print("\nAll significant file types have processors available!")
            
    except Exception as e:
        print(f"Error: {str(e)}", file=sys.stderr)
        sys.exit(1)
    finally:
        if temp_dir and os.path.exists(temp_dir):
            shutil.rmtree(temp_dir)

if __name__ == '__main__':
    main()

#!/usr/bin/env python3

import ast
import csv
import os
from collections import defaultdict
import astunparse

class FunctionExtractor(ast.NodeVisitor):
    def __init__(self, filename, globals_only=False):
        self.functions = []
        self.current_class = None
        self.current_function = []
        self.order = 0
        self.lambda_count = 0
        self.filename = filename
        self.globals_only = globals_only

    def visit_FunctionDef(self, node):
        self._process_entity(node, entity_type='function')

    def visit_ClassDef(self, node):
        self.current_class = node.name
        self.generic_visit(node)
        self.current_class = None

    def visit_Lambda(self, node):
        self._process_entity(node, entity_type='lambda')

    def _process_entity(self, node, entity_type):
        self.order += 1
        parent_class = self.current_class or "Global"
        parent_function = self.current_function[-1] if self.current_function else None
        entity_name = node.name if entity_type == 'function' else f"lambda_{self.lambda_count}"
        
        # Build full name with class prefix if in a class
        if parent_class != "Global":
            full_entity_name = f"{parent_class}.{entity_name}"
        else:
            full_entity_name = f"{parent_function}.{entity_name}" if parent_function else entity_name
        
        parameters = [arg.arg for arg in node.args.args]
        docstring = ast.get_docstring(node) or "N/A" if entity_type == 'function' else "N/A"
        entity_code = astunparse.unparse(node)
        self.functions.append((self.filename, parent_class, self.order, full_entity_name, parameters, docstring, entity_code))

        if not self.globals_only or (self.globals_only and not parent_function):
            self.current_function.append(entity_name)
            self.generic_visit(node)
            self.current_function.pop()

def extract_functions(source_code, filename, globals_only=False):
    """
    Extract functions from Python source code.
    
    Args:
        source_code (str): The Python source code to analyze
        filename (str): The name of the file being analyzed
        globals_only (bool): If True, only extract global functions
        
    Returns:
        list: List of tuples containing function information
    """
    tree = ast.parse(source_code)
    extractor = FunctionExtractor(filename, globals_only)
    extractor.source_code = source_code
    extractor.visit(tree)
    return extractor.functions

def process_file(file_path, error_callback=None, globals_only=False):
    """
    Process a single Python file and extract its functions.
    
    Args:
        file_path (str): Path to the Python file
        error_callback (callable): Optional callback for error handling
        globals_only (bool): If True, only extract global functions
        
    Returns:
        list: List of extracted functions
        
    Raises:
        SyntaxError: If the Python code is invalid
        Exception: For other errors during processing
    """
    try:
        with open(file_path, 'r') as f:
            source_code = f.read()
        tree = ast.parse(source_code)  # Let syntax errors propagate
        extractor = FunctionExtractor(file_path, globals_only)
        extractor.source_code = source_code
        extractor.visit(tree)
        return extractor.functions
    except Exception as e:
        if error_callback:
            error_callback(file_path, str(e))
        raise  # Re-raise the exception to be handled by the processor

def process_directory(input_directory, ignore_dirs=None, error_callback=None, progress_callback=None, globals_only=False):
    """
    Process a directory recursively and extract functions from all Python files.
    
    Args:
        input_directory (str): Directory to process
        ignore_dirs (list): List of directory names to ignore
        error_callback (callable): Optional callback for error handling
        progress_callback (callable): Optional callback for progress updates
        globals_only (bool): If True, only extract global functions
        
    Returns:
        dict: Dictionary mapping folders to their extracted functions
    """
    if ignore_dirs is None:
        ignore_dirs = ["venv", ".git", 'ds_venv', 'dw_env']
        
    folder_to_functions = defaultdict(list)
    total_files = sum(1 for root, dirs, files in os.walk(input_directory)
                     if not any(d in root for d in ignore_dirs)
                     for file in files if file.endswith(".py"))
    processed_files = 0
    
    for root, dirs, files in os.walk(input_directory):
        dirs[:] = [d for d in dirs if d not in ignore_dirs]
        for file in files:
            if file.endswith(".py"):
                file_path = os.path.join(root, file)
                relative_folder = os.path.relpath(root, input_directory)
                functions = process_file(file_path, error_callback, globals_only)
                folder_to_functions[relative_folder].extend(functions)
                processed_files += 1
                if progress_callback:
                    progress_callback(processed_files, total_files, file_path)
                    
    return dict(folder_to_functions)

def write_results_to_csv(functions, output_path):
    """
    Write extracted functions to a CSV file.
    
    Args:
        functions (list): List of function information tuples
        output_path (str): Path to the output CSV file
    """
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, 'w', newline='') as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow(['Filename', 'Parent', 'Order', 'Function/Method Name', 'Parameters', 'Docstring', 'Code'])
        for row in functions:
            writer.writerow(row)

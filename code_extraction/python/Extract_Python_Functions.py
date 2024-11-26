#!/usr/bin/env python3

import ast
import csv
import argparse
import os
import astunparse
from collections import defaultdict

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
        parameters = [arg.arg for arg in node.args.args]
        docstring = ast.get_docstring(node) or "N/A" if entity_type == 'function' else "N/A"
        full_entity_name = f"{parent_function}.{entity_name}" if parent_function else entity_name
        entity_code = astunparse.unparse(node)
        self.functions.append((self.filename, parent_class, self.order, full_entity_name, parameters, docstring, entity_code))

        if not self.globals_only or (self.globals_only and not parent_function):
            self.current_function.append(entity_name)
            self.generic_visit(node)
            self.current_function.pop()

def extract_functions(source_code, filename, globals_only=False):
    tree = ast.parse(source_code)
    extractor = FunctionExtractor(filename, globals_only)
    extractor.source_code = source_code
    extractor.visit(tree)
    return extractor.functions

def parse_arguments():
    parser = argparse.ArgumentParser()
    parser.add_argument("input_filepath", nargs='?', default=os.getcwd())
    parser.add_argument("output_csv_filepath", nargs='?', default=os.getcwd().split("/")[-1])
    parser.add_argument("--ignore_dirs", nargs='*', default=["venv", ".git", 'ds_venv', 'dw_env'])
    parser.add_argument("--globals-only", action='store_true')
    return parser.parse_args()

def process_file(file_path, error_log_path, globals_only=False):
    try:
        with open(file_path, 'r') as f:
            source_code = f.read()
        return extract_functions(source_code, file_path, globals_only)
    except Exception as e:
        log_error(error_log_path, file_path, str(e))
        return []

def log_error(error_log_path, file_path, error_message):
    with open(error_log_path, 'a', newline='') as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow([file_path, error_message])

def write_to_csv(functions, output_directory, folder_name):
    if folder_name == '.':
        folder_name = os.path.basename(os.path.abspath(output_directory))
    output_csv_filepath = os.path.join(output_directory, f"{folder_name}.csv")
    os.makedirs(os.path.dirname(output_csv_filepath), exist_ok=True)
    with open(output_csv_filepath, 'w', newline='') as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow(['Filename', 'Parent', 'Order', 'Function/Method Name', 'Parameters', 'Docstring', 'Code'])
        for row in functions:
            writer.writerow(row)

def process_directory(input_directory, output_directory, total_files, ignore_dirs, error_log_path, globals_only=False):
    folder_to_functions = defaultdict(list)
    processed_files = 0
    for root, dirs, files in os.walk(input_directory):
        dirs[:] = [d for d in dirs if d not in ignore_dirs]
        for file in files:
            if file.endswith(".py"):
                file_path = os.path.join(root, file)
                relative_folder = os.path.relpath(root, input_directory)
                functions = process_file(file_path, error_log_path, globals_only)
                folder_to_functions[relative_folder].extend(functions)
                processed_files += 1
                progress = (processed_files / total_files) * 100
                print(f"Progress: {progress:.2f}% - Processed {file_path}")
    for folder, functions in folder_to_functions.items():
        write_to_csv(functions, output_directory, folder)

def main():
    args = parse_arguments()
    if args.output_csv_filepath is None:
        input_name = os.path.basename(args.input_filepath)
        args.output_csv_filepath = os.path.join(os.getcwd(), f"{input_name}_output")
    abs_output_path = os.path.abspath(args.output_csv_filepath) 
    print(f"Output will be saved to: {abs_output_path}")  
    total_files = 0
    if os.path.isdir(args.input_filepath):
        for root, dirs, files in os.walk(args.input_filepath):
            dirs[:] = [d for d in dirs if d not in args.ignore_dirs]
            total_files += sum(1 for file in files if file.endswith(".py"))
    os.makedirs(args.output_csv_filepath, exist_ok=True)
    error_log_path = os.path.join(args.output_csv_filepath, "errors.csv")
    with open(error_log_path, 'w', newline='') as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow(['File Path', 'Error Message'])
    if os.path.isdir(args.input_filepath):
        process_directory(args.input_filepath, args.output_csv_filepath, total_files, args.ignore_dirs, error_log_path, args.globals_only)
    else:
        functions = process_file(args.input_filepath, error_log_path)
        write_to_csv(functions, args.output_csv_filepath, os.path.basename(args.input_filepath))

if __name__ == "__main__":
    main()

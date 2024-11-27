#!/usr/bin/env python3

from liblearner.python_extractor import process_file
import os
import json

def main():
    # Get the absolute path to test_script.py
    test_file = os.path.join(os.path.dirname(__file__), 'test_files', 'test_script.py')
    
    print(f"Processing file: {test_file}")
    print("-" * 50)
    
    try:
        # Process the file and get the extracted functions
        functions = process_file(test_file)
        
        # Print each extracted function in a readable format
        for func in functions:
            print("\nExtracted Function:")
            print(f"File: {func[0]}")
            print(f"Class: {func[1]}")
            print(f"Order: {func[2]}")
            print(f"Name: {func[3]}")
            print(f"Parameters: {func[4]}")
            print(f"Docstring: {func[5]}")
            print(f"Code:\n{func[6]}")
            print("-" * 50)
            
    except Exception as e:
        print(f"Error processing file: {e}")

if __name__ == "__main__":
    main()

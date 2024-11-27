#!/usr/bin/env python3

from liblearner.processors.python_processor import PythonProcessor
import os
import pandas as pd

def main():
    # Create processor
    processor = PythonProcessor()
    
    # Get test file path
    test_file = os.path.join(os.path.dirname(__file__), 'test_files', 'test_script.py')
    print(f"Processing file: {test_file}")
    
    # Process the file
    result = processor.process_file(test_file)
    
    # Create output directory
    output_dir = os.path.join(os.path.dirname(__file__), 'output')
    os.makedirs(output_dir, exist_ok=True)
    
    # Get the processor type
    proc_type = processor.get_supported_types()[0]
    
    # Create dataframes dict
    dataframes = {proc_type: processor.results_df}
    
    # Write combined DataFrame
    combined_df = pd.concat(dataframes.values(), ignore_index=True)
    combined_path = os.path.join(output_dir, "test_combined.csv")
    print(f"\nWriting combined results to: {combined_path}")
    combined_df.to_csv(combined_path, index=False)
    
    # Write separate results
    type_name = proc_type.replace('/', '_').replace('-', '_')
    type_path = os.path.join(output_dir, f"test_{type_name}.csv")
    print(f"Writing type results to: {type_path}")
    processor.results_df.to_csv(type_path, index=False)
    
    # Print the contents of the saved CSV
    print("\nContents of saved CSV:")
    print(pd.read_csv(type_path))

if __name__ == "__main__":
    main()

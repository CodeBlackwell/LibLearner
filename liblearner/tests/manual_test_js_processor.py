import os
from liblearner.processors.javascript_processor import JavaScriptProcessor

def main():
    # Path to the JavaScript file to test
    js_file_path = os.path.join(os.path.dirname(__file__), 'test_files', 'test.js')
    
    # Ensure the file exists
    if not os.path.exists(js_file_path):
        print(f"JavaScript file not found: {js_file_path}")
        return
    
    # Instantiate the JavaScriptProcessor
    processor = JavaScriptProcessor(debug=True)
    
    # Process the JavaScript file
    result = processor.process_file(js_file_path)
    
    # Print the processing result
    print("Processing Result:")
    print(f"File Info: {result}")
    print("Elements:")
    for element in result.elements:
        print(f"  - Type: {element['type']}, Name: {element['name']}")
        print(f"    Code: {element['code']}")
        print(f"    Props: {element.get('props', {})}")
    
    # Print any errors
    if result.errors:
        print("Errors:")
        for error in result.errors:
            print(f"  - {error}")

if __name__ == "__main__":
    main()
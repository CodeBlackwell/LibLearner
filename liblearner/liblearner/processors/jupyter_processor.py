import csv
import nbformat
from typing import List
from ..file_processor import FileProcessor

class JupyterProcessor(FileProcessor):
    def get_supported_types(self) -> List[str]:
        return [
            'application/x-ipynb+json',
            'application/json'
        ]
    
    def process_file(self, file_path: str) -> str:
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                nb = nbformat.read(f, as_version=4)
            
            csv_data = []
            
            for i, cell in enumerate(nb.cells, start=1):
                cell_data = [
                    file_path,
                    cell.cell_type,
                    i,
                    cell.source.replace('\n', '\\n'),
                    str(cell.outputs).replace('\n', '\\n'), 
                    cell.execution_count,
                    str(cell.metadata.get('attachments', {})).replace('\n', '\\n')
                ]
                csv_data.append(cell_data)
            
            csv_file = f"{file_path}.csv"
            with open(csv_file, 'w', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                writer.writerow(['path', 'cell_type', 'cell_number', 'source', 'outputs', 'execution_count', 'metadata'])
                writer.writerows(csv_data)

            return csv_file
            
        except Exception as e:
            print(f"Error processing {file_path}: {str(e)}")
            return None
import ast
import astunparse

from .extract_data_structures import DataStructureExtractor


class FunctionExtractor(ast.NodeVisitor):
    """
    Extracts functions, classes, and lambdas from an AST (Abstract Syntax Tree).

    Usage Example:
    --------------
    extractor = FunctionExtractor("filename.py", globals_only=True)
    extractor.visit(ast.parse(source_code))
    functions = extractor.functions
    """

    def __init__(self, filename, globals_only=False):
        self.functions = []
        self.current_class = None
        self.current_function = []
        self.order = 0
        self.lambda_count = 0
        self.filename = filename
        self.globals_only = globals_only

    def visit_FunctionDef(self, node):
        self._process_entity(node, entity_type="function")

    def visit_ClassDef(self, node):
        self.current_class = node.name  # Set the current class name
        self._process_entity(node, entity_type="class")  # Process the class entity
        self.generic_visit(node)  # Continue visiting other nodes
        self.current_class = None  # Reset the current class name

    def visit_Lambda(self, node):
        self._process_entity(node, entity_type="lambda")

    def extract_data_structures(self, source_code):
        tree = ast.parse(source_code)
        extractor = DataStructureExtractor()
        extractor.visit(tree)
        return extractor.data_structures

    def _process_entity(self, node, entity_type):
        self.order += 1
        parent_class = self.current_class or "Global"
        entity_name = (
            node.name
            if entity_type in ["function", "class"]
            else f"lambda_{self.lambda_count}"
        )

        # Check if this is a global class
        if entity_type == "class" and entity_name == self.current_class:
            parent_class = "Global"

        parameters = (
            [arg.arg for arg in node.args.args] if hasattr(node, "args") else []
        )  # Adjusted for class nodes
        docstring = ast.get_docstring(node) or "N/A"
        full_entity_name = (
            f"{parent_class}.{entity_name}" if parent_class != "Global" else entity_name
        )
        entity_code = astunparse.unparse(node)
        self.functions.append(
            (
                self.filename,
                parent_class,
                self.order,
                full_entity_name,
                parameters,
                docstring,
                entity_code,
            )
        )

import ast


class DataStructureExtractor(ast.NodeVisitor):
    """
    Extracts data structures from an AST (Abstract Syntax Tree).

    Usage Example:
    --------------
    extractor = DataStructureExtractor()
    extractor.visit(ast.parse(source_code))
    data_structures = extractor.data_structures
    """

    def __init__(self):
        self.data_structures = []

    def visit_Assign(self, node):
        for target in node.targets:
            if isinstance(target, ast.Name):
                self.data_structures.append(
                    {
                        "name": target.id,
                        "type": "assignment",
                        "value": ast.dump(node.value),
                    }
                )
        self.generic_visit(node)

    def visit_List(self, node):
        self.data_structures.append({"type": "list", "value": ast.dump(node)})
        self.generic_visit(node)

    def visit_Dict(self, node):
        self.data_structures.append({"type": "dictionary", "value": ast.dump(node)})
        self.generic_visit(node)

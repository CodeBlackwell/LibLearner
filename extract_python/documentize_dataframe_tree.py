class DocumentizeDataframeTree:
    """
    Transforms and documents a tree of dataframes.

    Usage Example:
    --------------
    doc_tree = DocumentizeDataframeTree(dataframe_tree)
    doc_tree.documentize()
    """

    def __init__(self, dataframe_tree):
        self.dataframe_tree = dataframe_tree

    def documentize(self):
        self.dataframe_tree = self.lowercase_columns_in_tree()
        self.dataframe_tree = self.dataframe_tree_apply(
            lambda x: x * 2, "input_col", "output_col"
        )
        self.dataframe_tree = self.document_columns_in_tree()
        self.report_keys(self.dataframe_tree)

    def dataframe_tree_apply(self, callback, input_col, output_col):
        def recurse_tree(tree):
            new_tree = {}
            for key, value in tree.items():
                if isinstance(value, dict):
                    new_tree[key] = recurse_tree(value)
                else:
                    if input_col in value.columns:
                        new_df = value.copy()
                        new_df[output_col] = value[input_col].apply(callback)
                        new_tree[key] = new_df
                    else:
                        new_tree[key] = value
            return new_tree

        return recurse_tree(self.dataframe_tree)

    def lowercase_columns_in_tree(self):
        def recurse_tree(tree):
            new_tree = {}
            for key, value in tree.items():
                if isinstance(value, dict):
                    new_tree[key] = recurse_tree(value)
                else:
                    new_tree[key] = value.rename(columns=str.lower)
            return new_tree

        return recurse_tree(self.dataframe_tree)

    def report_keys(self, d, depth=0):
        for key, value in d.items():
            print("-" * depth + str(key))
            if isinstance(value, dict):
                self.report_keys(value, depth + 1)

    def create_document(self, row):
        document = []
        for col_name, col_value in row.items():
            document.append(f"{col_name}:\n{col_value}\n-----")
        return "\n".join(document)

    def document_columns_in_tree(self):
        def recurse_tree(tree):
            new_tree = {}
            for key, value in tree.items():
                if isinstance(value, dict):
                    new_tree[key] = recurse_tree(value)
                else:
                    new_df = value.copy()
                    new_df["document"] = new_df.apply(self.create_document, axis=1)
                    new_tree[key] = new_df
            return new_tree

        return recurse_tree(self.dataframe_tree)

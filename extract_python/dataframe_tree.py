import os
import pandas as pd


class DataframeTree:
    """
    Generates a tree of dataframes based on the source code files in a directory.

    Usage Example:
    --------------
    df_tree = DataframeTree("path/to/code")
    dataframe_tree = df_tree.generate_dataframe_tree()
    """

    def __init__(self, input_path):
        self.input_path = input_path

    def tree_files(startpath):
        """
        Generates a tree structure for the directory.

        Usage Example:
        --------------
        tree = DataframeTree.tree_files("path/to/code")
        """
        tree = {
            "name": os.path.basename(startpath),
            "type": "directory",
            "files": [],
            "sub_directories": [],
        }

        for root, dirs, files in os.walk(startpath):
            dirs[:] = [
                d
                for d in dirs
                if d not in {"node_modules", ".git"}
                and "venv" not in d
                and "__pycache__" not in d
            ]
            current_node = tree
            relative_path = os.path.relpath(root, startpath)

            if relative_path != ".":
                for path_part in relative_path.split(os.sep):
                    for sub_dir in current_node["sub_directories"]:
                        if sub_dir["name"] == path_part:
                            current_node = sub_dir
                            break

            current_node["files"].extend(files)
            for dir in dirs:
                current_node["sub_directories"].append(
                    {
                        "name": dir,
                        "type": "directory",
                        "files": [],
                        "sub_directories": [],
                    }
                )

        return tree

    def list_files(tree):
        """
        Lists all files in the tree structure.

        Usage Example:
        --------------
        files = DataframeTree.list_files(tree)
        """
        file_list = []

        def recurse_tree(t, path=""):
            new_path = os.path.join(path, t["name"])
            file_list.extend([os.path.join(new_path, f) for f in t["files"]])
            for sub_t in t["sub_directories"]:
                recurse_tree(sub_t, new_path)

        recurse_tree(tree)
        return file_list

    def generate_dataframe_tree(self):
        """
        Generates a tree of dataframes based on the source code files.

        Usage Example:
        --------------
        df_tree = DataframeTree("path/to/code")
        dataframe_tree = df_tree.generate_dataframe_tree()
        """
        tree = self.tree_files(self.input_path)
        files_list = self.list_files(tree)
        dataframe_tree = {}
        for file_path in files_list:
            if file_path.endswith(".py"):
                # Ensure file_path is an absolute path or correctly relative
                file_path = os.path.join(self.input_path, file_path)
                with open(file_path, "r") as file:
                    source_code = file.read()
                functions = self._extract_functions_from_code(source_code, file_path)
                df = pd.DataFrame(
                    functions,
                    columns=[
                        "Filename",
                        "Parent Class",
                        "Order",
                        "Entity Name",
                        "Parameters",
                        "Docstring",
                        "Code",
                    ],
                )

                # Split the relative file path into its component parts
                path_parts = os.path.relpath(file_path, self.input_path).split(os.sep)
                # Start at the root of the output dictionary
                current_dict = dataframe_tree

                # Traverse or create the nested dictionaries for each directory in the path
                for part in path_parts[:-1]:  # Exclude the file name itself
                    current_dict = current_dict.setdefault(part, {})

                # Set the DataFrame as the value for the file name key
                current_dict[path_parts[-1]] = df

        return dataframe_tree

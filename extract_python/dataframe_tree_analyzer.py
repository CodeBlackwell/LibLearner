class TreeAnalyzer:
    """
    Analyzes a dataframe tree and returns consolidated results.

    Usage Example:
    --------------
    tree_analyzer = TreeAnalyzer(dataframe_tree)
    results = tree_analyzer.analyze()
    """

    def __init__(self, dataframe_tree):
        self.dataframe_tree = dataframe_tree

    def analyze(self):
        """
        Analyzes the dataframe tree and returns consolidated results.

        Usage Example:
        --------------
        tree_analyzer = TreeAnalyzer(dataframe_tree)
        results = tree_analyzer.analyze()
        """
        normal_results = {}
        zero_token_sum_results = {}

        def recurse_tree(tree, path=[]):
            for key, value in tree.items():
                new_path = path + [key]
                if isinstance(value, dict):
                    # If the value is a dictionary, recurse further
                    recurse_tree(value, new_path)
                else:
                    # Assume the value is a DataFrame
                    file_info = self.analyze_dataframe(value)
                    # Check the token_sum value to decide where to store the analysis results
                    if file_info["token_sum"] == 0:
                        zero_token_sum_results["/".join(new_path)] = file_info
                    else:
                        normal_results["/".join(new_path)] = file_info

        recurse_tree(self.dataframe_tree)

        # Consolidating the results into one dictionary with two keys
        consolidated_results = {
            "normal_results": normal_results,
            "zero_token_sum_results": zero_token_sum_results,
        }

        return consolidated_results

    def analyze_dataframe(self, dataframe):
        """
        Analyzes a single dataframe and returns metrics.

        Usage Example:
        --------------
        tree_analyzer = TreeAnalyzer(dataframe_tree)
        metrics = tree_analyzer.analyze_dataframe(single_dataframe)
        """
        # Splitting the dataframe into two based on the 'Parent Class' value
        global_rows = dataframe[dataframe["parent class"] == "Global"]
        sub_global_rows = dataframe[dataframe["parent class"] != "Global"]

        # Computing metrics for 'Global' rows
        largest_global = global_rows["tokens"].max() if not global_rows.empty else None
        smallest_global = global_rows["tokens"].min() if not global_rows.empty else None
        global_mean = global_rows["tokens"].mean() if not global_rows.empty else None

        # Computing metrics for non-'Global' rows
        largest_sub_global = (
            sub_global_rows["tokens"].max() if not sub_global_rows.empty else None
        )
        smallest_sub_global = (
            sub_global_rows["tokens"].min() if not sub_global_rows.empty else None
        )
        sub_global_mean = (
            sub_global_rows["tokens"].mean() if not sub_global_rows.empty else None
        )

        # Creating the file_info dictionary with all the computed metrics
        file_info = {
            "memory_usage_kb": dataframe.memory_usage(deep=True).sum() / 1024,
            "token_sum": dataframe["tokens"].sum(),
            "largest_global": largest_global,
            "smallest_global": smallest_global,
            "global_mean": global_mean,
            "largest_sub_global": largest_sub_global,
            "smallest_sub_global": smallest_sub_global,
            "sub_global_mean": sub_global_mean,
            # Add other analysis metrics here
        }
        return file_info

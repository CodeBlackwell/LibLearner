def calculate_sum(a: int, b: int) -> int:
    """Calculate the sum of two numbers.
    
    Args:
        a: First number
        b: Second number
        
    Returns:
        Sum of the two numbers
    """
    return a + b

class DataProcessor:
    """A sample class for processing data."""
    
    def __init__(self, data: list):
        self.data = data
        
    def process(self) -> list:
        """Process the data by doubling each element."""
        return [x * 2 for x in self.data]


from code_detection.astnodes.statement import Statement
from typing import List, Tuple

class Comment(Statement):
  
    def __init__(self, bounds: List[Tuple[int, int]], value: str):
        super().__init__(bounds, "Comment")
        self.value = value
        
    def python_print(self):
        return f"# {self.value}"
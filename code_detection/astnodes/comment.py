from code_detection.astnodes.statement import Statement
from code_detection.astnodes.expr import Expr
from typing import List, Tuple

class Comment(Statement):
  
    def __init__(self, bounds: List[Tuple[int, int]], value: Expr):
        super().__init__(bounds, "Comment")
        self.value = value
        
    def python_print(self):
        return f"# {self.value.python_print()}"
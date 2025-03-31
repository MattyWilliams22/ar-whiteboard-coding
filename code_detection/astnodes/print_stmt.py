from code_detection.astnodes.statement import Statement
from code_detection.astnodes.expr import Expr
from typing import List, Tuple

class PrintStatement(Statement):
  
    def __init__(self, bounds: List[Tuple[int, int]], value: Expr, toString: bool = False):
        super().__init__(bounds, "Print")
        self.value = value
        self.toString = toString
        
    def python_print(self):
        if self.toString:
            return f"print(str({self.value.python_print()}))"
        else:
            return f"print(\"{self.value.python_print()}\")"
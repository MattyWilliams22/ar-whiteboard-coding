from code_detection.astnodes.statement import Statement
from code_detection.astnodes.expr import Expr
from typing import List, Tuple


class ReturnStatement(Statement):

    def __init__(self, bounds: List[Tuple[int, int]], value: Expr):
        super().__init__(bounds, "Return")
        self.value = value

    def python_print(self):
        return f"return {self.value.python_print()}"

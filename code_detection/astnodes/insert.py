from code_detection.astnodes.statement import Statement
from code_detection.astnodes.expr import Expr
from typing import List, Tuple


class Insert(Statement):

    def __init__(self, bounds: List[Tuple[int, int]], value: str):
        super().__init__(bounds, "Insert")
        self.value = value

    def python_print(self):
        return f"# INSERT {self.value}"

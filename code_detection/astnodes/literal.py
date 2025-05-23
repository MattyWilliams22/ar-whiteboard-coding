from code_detection.astnodes.expr import Expr
from typing import List, Tuple


class Literal(Expr):

    def __init__(self, bounds: List[Tuple[int, int]], kind: str):
        super().__init__(bounds, kind)

    def python_print(self):
        raise Exception("Not implemented")

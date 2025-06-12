from code_detection.astnodes.node import Node
from typing import List, Tuple


class Expr(Node):

    def __init__(self, bounds: List[Tuple[int, int]], value: str):
        super().__init__(bounds, "Expr")
        self.value = value

    def python_print(self):
        return self.value

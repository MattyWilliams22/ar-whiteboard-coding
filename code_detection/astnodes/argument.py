from code_detection.astnodes.node import Node
from typing import List, Tuple


class Argument(Node):

    def __init__(self, bounds: List[Tuple[int, int]], name: str):
        super().__init__(bounds, "Argument")
        self.name = name

    def python_print(self):
        return self.name

from code_detection.astnodes.node import Node
from typing import List, Tuple


class Statement(Node):

    def __init__(self, bounds: List[Tuple[int, int]], kind: str):
        super().__init__(bounds, kind)

    def python_print(self):
        raise Exception("Not implemented")

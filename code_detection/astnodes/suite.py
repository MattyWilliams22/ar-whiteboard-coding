from code_detection.astnodes.node import Node
from typing import List, Tuple


class Suite(Node):

    def __init__(self, bounds: List[Tuple[int, int]], nodes: List[Node]):
        super().__init__(bounds, "Suite")
        self.nodes = nodes

    def python_print(self):
        suite_str = ""
        for node in self.nodes:
            suite_str += node.python_print()
        return suite_str

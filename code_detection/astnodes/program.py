from code_detection.astnodes.node import Node
from code_detection.astnodes.suite import Suite
from typing import List, Tuple

class Program(Node):

    def __init__(self, bounds: List[Tuple[int, int]], suite: Suite):
        super().__init__(bounds, "Program")
        self.suite = suite
        self.bounds = self.suite.bounds
        
    def python_print(self):
        program = self.suite.python_print()
        return program
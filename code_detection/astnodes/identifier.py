from code_detection.astnodes.literal import Literal
from typing import List, Tuple


class Identifier(Literal):

    def __init__(self, bounds: List[Tuple[int, int]], name: str):
        super().__init__(bounds, "Identifier")
        self.name = name

    def python_print(self):
        return f"{self.name}"

from code_detection.astnodes.statement import Statement
from typing import List, Tuple


class CustomStatement(Statement):
    def __init__(self, bounds: List[Tuple[int, int]], token: str):
        self.bounds = bounds
        self.token = token

    def python_print(self):
        return f"{self.token}"

from code_detection.astnodes.literal import Literal
from typing import List, Tuple

class BooleanLiteral(Literal):
  
    def __init__(self, bounds: List[Tuple[int, int]], value: bool):
        super().__init__(bounds, "BooleanLiteral")
        self.value = value
        
    def python_print(self):
        return f"{self.value}"
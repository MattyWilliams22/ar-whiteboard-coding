from code_detection.astnodes.statement import Statement
from typing import List, Tuple


class Call(Statement):

    def __init__(
        self, bounds: List[Tuple[int, int]], function_name: str, arguments: List[str]
    ):
        super().__init__(bounds, "Call")
        self.function_name = function_name
        self.arguments = arguments

    def python_print(self):
        call = f"{self.function_name}("

        for i, argument in enumerate(self.arguments):
            call += argument
            if i < len(self.arguments) - 1:
                call += ", "

        call += ")"

        return call

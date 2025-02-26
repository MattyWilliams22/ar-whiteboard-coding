from code_detection.astnodes.node import Node
from code_detection.astnodes.statement import Statement
from code_detection.astnodes.identifier import Identifier
from code_detection.astnodes.argument import Argument
from typing import List, Tuple

class Function(Node):

    def __init__(self, bounds: List[Tuple[int, int]], name: Identifier, arguments: List[str], body: List[Statement]):
        super().__init__(bounds, "Function")
        self.name = name
        self.arguments = arguments
        self.body = body
        
    def python_print(self):
        indent = "    "
        function = f"def {self.name.python_print()}("

        for i, argument in enumerate(self.arguments):
            function += argument
            if i < len(self.arguments) - 1:
                function += ", "

        function += "):\n"

        for statement in self.body:
            for line in statement.python_print().split("\n"):
                function += f"{indent}{line}\n"

        return function.rstrip()

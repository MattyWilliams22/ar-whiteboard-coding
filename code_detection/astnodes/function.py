from code_detection.astnodes.node import Node
from code_detection.astnodes.suite import Suite
from code_detection.astnodes.identifier import Identifier
from typing import List, Tuple


class Function(Node):

    def __init__(
        self,
        bounds: List[Tuple[int, int]],
        name: Identifier,
        arguments: str,
        body: Suite,
    ):
        super().__init__(bounds, "Function")
        self.name = name
        self.arguments = arguments
        self.body = body

    def python_print(self):
        indent = "    "
        function = f"def {self.name.python_print()}("

        function += self.arguments

        function += "):\n"

        for line in self.body.python_print().splitlines():
            function += indent + line + "\n"

        return function.rstrip()

from code_detection.astnodes.node import Node
from code_detection.astnodes.suite import Suite
from code_detection.astnodes.identifier import Identifier
from typing import List, Tuple


class ClassNode(Node):

    def __init__(
        self,
        bounds: List[Tuple[int, int]],
        name: Identifier,
        inherits: str,
        body: Suite,
    ):
        super().__init__(bounds, "Class")
        self.name = name
        self.inherits = inherits
        self.body = body

    def python_print(self):
        indent = "    "
        class_str = f"class {self.name.python_print()}("

        class_str += self.inherits

        class_str += "):\n"

        for line in self.body.python_print().splitlines():
            class_str += indent + line + "\n"

        return class_str.rstrip()

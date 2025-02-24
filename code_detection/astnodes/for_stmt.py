from code_detection.astnodes.statement import Statement
from code_detection.astnodes.expr import Expr
from code_detection.astnodes.identifier import Identifier
from typing import List, Tuple

class ForStatement(Statement):
    def __init__(self, bounds: List[Tuple[int, int]], count: Identifier, lower_bound: Expr, upper_bound: Expr, body: List[Statement]):
        super().__init__(bounds, "For")
        self.count = count
        self.lower_bound = lower_bound
        self.upper_bound = upper_bound
        self.body = body

    def python_print(self):
        indent = "    "
        loop_header = f"for {self.count.python_print()} in range({self.lower_bound.python_print()}, {self.upper_bound.python_print()}):\n"

        body_lines = []
        for statement in self.body:
            for line in statement.python_print().split("\n"):
                body_lines.append(f"{indent}{line}")

        return loop_header + "\n".join(body_lines)
        


from code_detection.astnodes.statement import Statement
from code_detection.astnodes.expr import Expr
from typing import List, Tuple


class WhileStatement(Statement):

    def __init__(
        self, bounds: List[Tuple[int, int]], condition: Expr, body: List[Statement]
    ):
        super().__init__(bounds, "While")
        self.condition = condition
        self.body = body

    def python_print(self):
        indent = "    "
        statement = f"while {self.condition.python_print()}:\n"

        for stmt in self.body:
            for line in stmt.python_print().split("\n"):
                statement += f"{indent}{line}\n"

        return statement.rstrip()

from code_detection.astnodes.statement import Statement
from code_detection.astnodes.call import Call
from typing import List, Tuple


class AssignCall(Statement):

    def __init__(
        self, bounds: List[Tuple[int, int]], lvalue: str, call_statement: Call
    ):
        super().__init__(bounds, "AssignCall")
        self.lvalue = lvalue
        self.call_statement = call_statement

    def python_print(self):
        assign_call = f"{self.lvalue} {self.call_statement.python_print()}"

        return assign_call

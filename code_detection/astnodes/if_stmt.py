from code_detection.astnodes.statement import Statement
from code_detection.astnodes.expr import Expr
from typing import List, Tuple

class IfStatement(Statement):
  
    def __init__(self, bounds: List[Tuple[int, int]], conditions: List[Expr], bodies: List[List[Statement]]):
        super().__init__(bounds, "If")
        self.conditions = conditions
        self.bodies = bodies
        
    def python_print(self):
        indent = "    "
        statement = f"if {self.conditions[0].python_print()}:\n"

        for stmt in self.bodies[0]:
            for line in stmt.python_print().split("\n"):
                statement += f"{indent}{line}\n"

        for i in range(1, len(self.conditions)):
            statement += f"elif {self.conditions[i].python_print()}:\n"
            for stmt in self.bodies[i]:
                for line in stmt.python_print().split("\n"):
                    statement += f"{indent}{line}\n"

        if len(self.bodies) > len(self.conditions):
            statement += "else:\n"
            for stmt in self.bodies[-1]:
                for line in stmt.python_print().split("\n"):
                    statement += f"{indent}{line}\n"

        return statement.rstrip()


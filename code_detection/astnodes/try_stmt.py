from code_detection.astnodes.statement import Statement
from code_detection.astnodes.expr import Expr
from typing import List, Tuple

class TryStatement(Statement):
  
    def __init__(self, bounds: List[Tuple[int, int]], try_body: List[Statement], exception_names: List[str], catch_bodies: List[List[Statement]] | None, else_body: List[Statement], finally_body: List[Statement] | None):
        super().__init__(bounds, "If")
        self.try_body = try_body
        self.exception_names = exception_names
        self.catch_bodies = catch_bodies
        self.else_body = else_body
        self.finally_body = finally_body
        
    def python_print(self):
        indent = "    "
        statement = f"try:\n"
        for stmt in self.try_body:
            for line in stmt.python_print().split("\n"):
                statement += f"{indent}{line}\n"
        
        if self.catch_bodies is not None:
            for catch_body, exception_name in zip(self.catch_bodies, self.exception_names):
                statement += f"except {exception_name}:\n"
                for stmt in catch_body:
                    for line in stmt.python_print().split("\n"):
                        statement += f"{indent}{line}\n"

        if self.else_body is not None:
            statement += "else:\n"
            for stmt in self.else_body:
                for line in stmt.python_print().split("\n"):
                    statement += f"{indent}{line}\n"

        if self.finally_body is not None:
            statement += "finally:\n"
            for stmt in self.finally_body:
                for line in stmt.python_print().split("\n"):
                    statement += f"{indent}{line}\n"

        return statement.rstrip()


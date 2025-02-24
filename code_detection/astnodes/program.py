from code_detection.astnodes.node import Node
from code_detection.astnodes.function import Function
from code_detection.astnodes.statement import Statement
from typing import List, Tuple

class Program(Node):

    def __init__(self, bounds: List[Tuple[int, int]], functions: List[Function], statements: List[Statement]):
        super().__init__(bounds, "Program")
        self.functions = functions
        self.statements = statements
    
    def add_function(self, function: Function):
        self.functions.append(function)

    def add_statement(self, statement: Statement):
        self.statements.append(statement)
        
    def python_print(self):
        program = ""
        for function in self.functions:
            program += function.python_print() + "\n\n"
        for statement in self.statements:
            program += statement.python_print() + "\n"
        return program
from code_detection.astnodes.node import Node
from code_detection.astnodes.function import Function
from code_detection.astnodes.statement import Statement
from typing import List, Tuple

class Program(Node):

    def __init__(self, bounds: List[Tuple[int, int]], functions: List[Function], statements: List[Statement]):
        super().__init__(bounds, "Program")
        self.functions = functions
        self.statements = statements

    def get_overall_bounds(self, bounds: List[List[Tuple[int, int]]]):
        min_x = min([min([x for x, y in box]) for box in bounds])
        min_y = min([min([y for x, y in box]) for box in bounds])
        max_x = max([max([x for x, y in box]) for box in bounds])
        max_y = max([max([y for x, y in box]) for box in bounds])

        # Check this later
        return [(min_x, min_y), (max_x, min_y), (max_x, max_y), (min_x, max_y)]
    
    def add_function(self, function: Function):
        self.functions.append(function)
        self.bounds = self.get_overall_bounds([self.bounds, function.bounds])

    def add_statement(self, statement: Statement):
        self.statements.append(statement)
        self.bounds = self.get_overall_bounds([self.bounds, statement.bounds])
        
    def python_print(self):
        program = ""
        for function in self.functions:
            program += function.python_print() + "\n\n"
        for statement in self.statements:
            program += statement.python_print() + "\n"
        return program
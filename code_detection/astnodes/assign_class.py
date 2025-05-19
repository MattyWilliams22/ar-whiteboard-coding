from code_detection.astnodes.statement import Statement
from code_detection.astnodes.call import Call
from typing import List, Tuple

class AssignClass(Statement):
  
      def __init__(self, bounds: List[Tuple[int, int]], lvalue: str, class_name: str, class_args: str):
          super().__init__(bounds, "AssignClass")
          self.lvalue = lvalue
          self.class_name = class_name
          self.class_args = class_args
          
      def python_print(self):
          assign_class = f"{self.lvalue} = {self.class_name}({self.class_args})"
  
          return assign_class
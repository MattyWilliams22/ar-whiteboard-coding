from code_detection.astnodes.statement import Statement
from code_detection.astnodes.expr import Expr
from typing import List, Tuple

class ImportStatement(Statement):
  
    def __init__(self, bounds: List[Tuple[int, int]], imported: str, module: str | None = None, alias: str | None = None):
        super().__init__(bounds, "Import")
        self.module = module
        self.imported = imported
        self.alias = alias
        
    def python_print(self):
        if self.module is not None:
            python = f"from {self.module} import {self.imported}"
        else:
            python = f"import {self.imported}"
        if self.alias is not None:
            python += f" as {self.alias}"
        return python
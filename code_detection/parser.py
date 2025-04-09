from code_detection.parse_code import parse_code

class Parser:
  def __init__(self, tokens):
    self.tokens = tokens
    self.program = None
    self.python_code = None
    self.error_message = None
    self.error_box = None

  def parse(self):
    self.program, self.error_message, self.error_box = parse_code(self.tokens)
    if self.program is None or self.error_message is not None:
      return None, None, "Error: Parsing failed (" + self.error_message + ")", self.error_box

    self.python_code = self.program.python_print() if self.program else None
    if self.python_code is None:
      return self.program, None, "Error: Python printing failed", None
    
    return self.program, self.python_code, None, None
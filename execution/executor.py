import io
import sys

class Executor:
  def __init__(self, python_code):
    self.python_code = python_code
    self.output = None
    self.error_message = None

  def execute(self):
    self.output = None
    self.error_message = None
  
    # Redirect stdout to capture the output
    output_capture = io.StringIO()
    sys.stdout = output_capture

    try:
      exec(self.python_code, {})
    except Exception as e:
      self.error_message = str(e)

    # Restore original stdout
    sys.stdout = sys.__stdout__
  
    if self.error_message is not None:
      return None, self.error_message

    # Get the captured output
    self.output = output_capture.getvalue()

    return self.output, None
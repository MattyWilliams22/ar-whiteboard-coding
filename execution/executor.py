import io
import sys
import tempfile
import os
import uuid
import shutil
import subprocess
from settings import settings

class Executor:
  def __init__(self, whiteboard_code):
    self.whiteboard_code = whiteboard_code
    self.helper_code = settings.get("HELPER_CODE", "")
    self.output = None
    self.error_message = None

  def _combine_code(self):
    """Combines helper and whiteboard code with proper indentation"""
    if not self.helper_code.strip():
      return self.whiteboard_code
        
    if "#INSERT" not in self.helper_code:
      return self.helper_code + "\n" + self.whiteboard_code
        
    # Find indentation of #INSERT
    insert_pos = self.helper_code.find("#INSERT")
    line_start = self.helper_code.rfind("\n", 0, insert_pos) + 1
    indent = self.helper_code[line_start:insert_pos]
    
    # Indent each line of whiteboard code
    indented_code = ""
    for line in self.whiteboard_code.splitlines(keepends=True):
      if line.strip():
        indented_code += indent + line
      else:
        indented_code += line
            
    return self.helper_code.replace("#INSERT", indented_code)

  def execute_locally(self):
    full_code = self._combine_code()
    self.output = None
    self.error_message = None

    # Redirect stdout to capture the output
    output_capture = io.StringIO()
    sys.stdout = output_capture

    try:
      exec(full_code, {})
    except Exception as e:
      self.error_message = str(e)

    # Restore original stdout
    sys.stdout = sys.__stdout__

    if self.error_message is not None:
      return None, self.error_message

    self.output = output_capture.getvalue()
    return self.output, None

  def execute_in_sandbox(self):
    full_code = self._combine_code()
    self.output = None
    self.error_message = None

    DOCKER_IMAGE = "python:3.10-slim"
    TIMEOUT_SECONDS = 5

    temp_dir = tempfile.mkdtemp()
    code_file_path = os.path.join(temp_dir, "script.py")

    try:
      # Write code to temp file
      with open(code_file_path, "w") as f:
        f.write(full_code)

      container_name = f"code-sandbox-{uuid.uuid4().hex[:8]}"

      # Build Docker run command
      result = subprocess.run([
        "docker", "run", "--rm",
        "--name", container_name,
        "--network", "none",  # no internet
        "--cpus", "0.5",      # cpu limit
        "--memory", "128m",   # memory limit
        "-v", f"{temp_dir}:/code",
        DOCKER_IMAGE,
        "timeout", str(TIMEOUT_SECONDS),
        "python3", "/code/script.py"
      ],
      stdout=subprocess.PIPE,
      stderr=subprocess.PIPE,
      text=True)

      # Capture outputs
      self.output = result.stdout
      if result.returncode != 0:
        self.error_message = result.stderr

    except Exception as e:
      self.error_message = str(e)

    finally:
      shutil.rmtree(temp_dir)

    if self.error_message:
      return None, self.error_message

    if not self.output:
      self.output = None

    return self.output, None

import io
import sys
import tempfile
import os
import uuid
import shutil
import subprocess

class Executor:
  def __init__(self, python_code):
    self.python_code = python_code
    self.output = None
    self.error_message = None

  def execute_locally(self):
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

    self.output = output_capture.getvalue()
    return self.output, None

  def execute_in_sandbox(self):
    self.output = None
    self.error_message = None

    DOCKER_IMAGE = "python:3.10-slim"
    TIMEOUT_SECONDS = 5

    temp_dir = tempfile.mkdtemp()
    code_file_path = os.path.join(temp_dir, "script.py")

    try:
      # Write code to temp file
      with open(code_file_path, "w") as f:
        f.write(self.python_code)

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

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

    def _detect_inserts(self):
        """Detects occurences of # INSERT X in the helper code"""
        insert_set = set()
        for line in self.helper_code.splitlines():
            if line.strip().startswith("# INSERT"):
                # Check if the line contains a valid insert
                parts = line.split()
                if len(parts) == 3:
                    insert_set.add(parts[2].strip())
                elif len(parts) == 2:
                    insert_set.add("")
        return insert_set

    def _split_whiteboard_code(self):
        """Split the whiteboard code based on the # INSERT comments"""
        segments = {}
        current_key = ""
        current_segment = []
        for line in self.whiteboard_code.splitlines():
            if line.strip().startswith("# INSERT") or line.strip().startswith(
                "#INSERT"
            ):
                if line.strip().startswith("# INSERT"):
                    rest_of_line = line.split("# INSERT", 1)[1].strip()
                else:
                    rest_of_line = line.split("#INSERT", 1)[1].strip()

                if rest_of_line:
                    next_key = rest_of_line.strip()
                else:
                    next_key = ""

                if current_segment:
                    segments[current_key] = "\n".join(current_segment)

                current_key = next_key
                current_segment = []
            else:
                current_segment.append(line)
        if current_segment:
            segments[current_key] = "\n".join(current_segment)

        return segments
    
    def _replace_with_indentation(self, insert_str, helper_code, whiteboard_code):
        # Find indentation of insert_str
        insert_pos = helper_code.find(insert_str)
        line_start = helper_code.rfind("\n", 0, insert_pos) + 1
        indent = helper_code[line_start:insert_pos]

        # Indent each line of whiteboard code
        indented_code = ""
        for line in whiteboard_code.splitlines(keepends=True):
            if line.strip():
                indented_code += indent + line
            else:
                indented_code += line

        return helper_code.replace(insert_str, indented_code)

    
    def _insert_whiteboard_code(self):
        """Inserts the whiteboard code into the helper code at the # INSERT positions"""
        segments = self._split_whiteboard_code()
        insert_set = self._detect_inserts()
        current_code = self.helper_code

        for key in insert_set:
            if key == "INSERT":
                key = ""
            if key in segments:
                segment = segments[key]
                if key == "":
                    # Replace the first occurrence of # INSERT
                    current_code = self._replace_with_indentation(
                        "# INSERT\n", current_code, segment + "\n"
                    )
                else:
                    # Replace the specific # INSERT X
                    current_code = self._replace_with_indentation(
                        f"# INSERT {key}\n", current_code, segment + "\n"
                    )

        return current_code

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
        full_code = self._insert_whiteboard_code()
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
            result = subprocess.run(
                [
                    "docker",
                    "run",
                    "--rm",
                    "--name",
                    container_name,
                    "--network",
                    "none",  # no internet
                    "--cpus",
                    "0.5",  # cpu limit
                    "--memory",
                    "128m",  # memory limit
                    "-v",
                    f"{temp_dir}:/code",
                    DOCKER_IMAGE,
                    "timeout",
                    str(TIMEOUT_SECONDS),
                    "python3",
                    "/code/script.py",
                ],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
            )

            # Capture outputs
            self.output = result.stdout
            if result.returncode != 0:
                self.error_message = result.stderr

        except Exception as e:
            self.error_message = str(e)

        finally:
            shutil.rmtree(temp_dir)

        if self.error_message:
            return None, self.error_message, full_code

        if not self.output:
            self.output = None

        return self.output, None, full_code

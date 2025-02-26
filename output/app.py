import tkinter as tk
from tkinter import scrolledtext, messagebox
import sys
import io

class CodeEditorApp:
    def __init__(self, root, initial_code=""):
        self.root = root
        self.root.title("Python Code Editor")

        # Text area for Python code
        self.text_area = scrolledtext.ScrolledText(root, wrap=tk.WORD, font=("Courier", 12))
        self.text_area.pack(expand=True, fill=tk.BOTH, padx=10, pady=5)
        self.text_area.bind("<KeyRelease>", self.check_syntax)

        # Run Button
        self.run_button = tk.Button(root, text="Run Code", command=self.run_code, state=tk.DISABLED)
        self.run_button.pack(pady=5)

        # Output Area
        self.output_area = scrolledtext.ScrolledText(root, wrap=tk.WORD, height=10, font=("Courier", 12))
        self.output_area.pack(expand=True, fill=tk.BOTH, padx=10, pady=5)
        self.output_area.insert(tk.END, "Output will be displayed here...\n")

        # Set initial code if provided
        if initial_code:
            self.set_code(initial_code)

    def check_syntax(self, event=None):
        """Checks syntax of the code and highlights errors."""
        code = self.text_area.get("1.0", tk.END).strip()
        self.text_area.tag_remove("error", "1.0", tk.END)

        if not code:
            self.run_button.config(state=tk.DISABLED)
            return
        
        try:
            compile(code, "<string>", "exec")
            self.run_button.config(state=tk.NORMAL)
        except SyntaxError as e:
            self.highlight_error(e.lineno, e.offset)
            self.run_button.config(state=tk.DISABLED)

    def highlight_error(self, line, column):
        """Highlights syntax errors in the text editor."""
        line_start = f"{line}.0"
        line_end = f"{line}.end"

        self.text_area.tag_add("error", line_start, line_end)
        self.text_area.tag_config("error", foreground="red")

    def run_code(self):
        """Runs the Python code and captures output/errors."""
        code = self.text_area.get("1.0", tk.END).strip()

        # Redirect stdout and stderr
        old_stdout, old_stderr = sys.stdout, sys.stderr
        sys.stdout = sys.stderr = io.StringIO()

        self.output_area.delete("1.0", tk.END)

        try:
            exec(code, {})
            output = sys.stdout.getvalue()
            self.output_area.insert(tk.END, output if output else "Code executed successfully.")
        except Exception as e:
            self.output_area.insert(tk.END, f"Error: {e}")

        # Restore stdout and stderr
        sys.stdout, sys.stderr = old_stdout, old_stderr

    def set_code(self, code_string):
        """Allows external scripts to pass a Python code string into the editor."""
        self.text_area.delete("1.0", tk.END)
        self.text_area.insert("1.0", code_string)
        self.check_syntax()

def run_editor(initial_code=""):
    """Function to easily launch the editor from another script."""
    root = tk.Tk()
    app = CodeEditorApp(root, initial_code)
    root.mainloop()

if __name__ == "__main__":
    run_editor()

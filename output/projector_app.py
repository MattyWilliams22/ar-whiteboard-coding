import tkinter as tk
from tkinter import scrolledtext
import sys
import io


class CodeEditorApp:
    def __init__(self, root, initial_code=""):
        self.root = root
        self.root.title("Python Code Editor")

        # Text area for Python code
        self.text_area = scrolledtext.ScrolledText(
            root, wrap=tk.WORD, font=("Courier", 12)
        )
        self.text_area.pack(expand=True, fill=tk.BOTH, padx=10, pady=5)
        self.text_area.bind(
            "<KeyRelease>", self.on_code_change
        )  # Bind key release to update projection

        # Run Button
        self.run_button = tk.Button(
            root, text="Run Code", command=self.run_code, state=tk.DISABLED
        )
        self.run_button.pack(pady=5)

        # Output Area
        self.output_area = scrolledtext.ScrolledText(
            root, wrap=tk.WORD, height=10, font=("Courier", 12)
        )
        self.output_area.pack(expand=True, fill=tk.BOTH, padx=10, pady=5)
        self.output_area.insert(tk.END, "Output will be displayed here...\n")

        # Projection Window
        self.projection_window = None
        self.check_projection()

        # Set initial code if provided
        if initial_code:
            self.set_code(initial_code)

    def on_code_change(self, event=None):
        """Handles changes in the code area to update projection and clear output."""
        self.check_syntax()  # Check syntax whenever code changes
        self.output_area.delete("1.0", tk.END)  # Clear output on code change
        self.update_projection()  # Update projection view

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

        try:
            exec(code, {})
            output = sys.stdout.getvalue()
            self.output_area.insert(
                tk.END, output if output else "Code executed successfully."
            )
        except Exception as e:
            self.output_area.insert(tk.END, f"Error: {e}")

        # Restore stdout and stderr
        sys.stdout, sys.stderr = old_stdout, old_stderr

        # Update projection
        self.update_projection()

    def set_code(self, code_string):
        """Allows external scripts to pass a Python code string into the editor."""
        self.text_area.delete("1.0", tk.END)
        self.text_area.insert("1.0", code_string)
        self.check_syntax()

    def check_projection(self):
        """Checks if a projector is connected and opens a projection window."""
        screen_width = self.root.winfo_screenwidth()
        screen_height = self.root.winfo_screenheight()

        # Assume projector if there's a larger-than-usual screen resolution
        if screen_width > 1920:  # Adjust threshold if needed
            self.open_projection_window(screen_width, screen_height)
        else:
            self.open_projection_window(None, None)  # Simulated projection

    def open_projection_window(self, screen_width, screen_height):
        """Opens the projection window on the projector if available, otherwise full-screen."""
        self.projection_window = tk.Toplevel(self.root)
        self.projection_window.title("Projected View")

        if screen_width and screen_height:
            # Move to the second screen
            self.projection_window.geometry(
                f"{screen_width}x{screen_height}+{screen_width}+0"
            )
        else:
            # Simulated projection on the main screen
            self.projection_window.attributes("-fullscreen", True)

        self.projection_text = tk.Text(
            self.projection_window,
            wrap=tk.WORD,
            font=("Courier", 20),
            bg="white",
            fg="black",
        )
        self.projection_text.pack(expand=True, fill=tk.BOTH)

        self.update_projection()

    def update_projection(self):
        """Updates the projected view with the latest code and output."""
        if self.projection_window:
            self.projection_text.delete("1.0", tk.END)
            code = self.text_area.get("1.0", tk.END).strip()
            output = self.output_area.get("1.0", tk.END).strip()

            self.projection_text.insert(tk.END, "### Python Code ###\n")
            self.projection_text.insert(tk.END, code + "\n\n")
            self.projection_text.insert(tk.END, "### Output ###\n")
            self.projection_text.insert(tk.END, output)


def run_editor(initial_code=""):
    """Function to easily launch the editor from another script."""
    root = tk.Tk()
    app = CodeEditorApp(root, initial_code)
    root.mainloop()


if __name__ == "__main__":
    run_editor()

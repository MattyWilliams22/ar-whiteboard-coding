from code_detection.parse_code import parse_code
import unicodedata
from typing import Dict
import re


class Parser:
    def __init__(self, tokens):
        self.tokens = tokens
        self.program = None
        self.python_code = None
        self.error_message = None
        self.error_box = None

    def normalise_python_code(self, ocr_code: str) -> str:
        """Normalise Python code extracted from OCR text."""
        
        # Homoglyph mapping (Unicode → ASCII)
        HOMOGLYPHS = {
            # Common OCR mistakes in code
            "＂": '"',
            "“": '"',
            "”": '"',
            "‟": '"',
            "˝": '"',
            "´": "'",
            "‘": "'",
            "’": "'",
            "｛": "{",
            "｝": "}",
            "［": "[",
            "］": "]",
            "（": "(",
            "）": ")",
            "〈": "<",
            "〉": ">",
            "﹤": "<",
            "﹥": ">",
            "＝": "=",
            "＋": "+",
            "－": "-",
            "＊": "*",
            "／": "/",
            "％": "%",
            "＃": "#",
            "＠": "@",
            "＼": "\\",
            "｜": "|",
            "～": "~",
            "＾": "^",
            "｀": "`",
            "；": ";",
            "：": ":",
            "，": ",",
            "．": ".",
            " ": " ",
            " ": " ",
            " ": " ",
            "​": "",  
            # Zero-width spaces
            "ᅳ": "_",
            "‐": "-",
            "‑": "-",
            "‒": "-",
            "–": "-",
            "—": "-",
            "―": "-",
            "−": "-",
        }

        # Normalise line endings first
        normalised_lines = []
        for line in ocr_code.splitlines():
            # Preserve indentation (tabs/spaces)
            leading_whitespace = len(line) - len(line.lstrip())
            indentation = line[:leading_whitespace]

            # Normalise characters in content
            content = line[leading_whitespace:]
            normalised_content = []

            for char in content:
                # Handle homoglyphs
                normalised_char = HOMOGLYPHS.get(char, char)

                # Normalise Unicode (e.g., fullwidth to ASCII)
                if unicodedata.category(normalised_char) == "So":  # Other symbols
                    normalised_char = unicodedata.normalize("NFKC", normalised_char)

                normalised_content.append(normalised_char)

            # Reconstruct line with original indentation
            normalised_line = indentation + "".join(normalised_content)
            normalised_lines.append(normalised_line)

        # Rebuild code with original line structure
        normalised_code = "\n".join(normalised_lines)

        # Fix common OCR errors specific to Python
        corrections = [
            (r"(\s)∶(\s)", r"\1:\2"),  # Mathematical colon → Python colon
            (r"［([^\]]*?)］", r"[\1]"),  # Fullwidth brackets
            (r"（([^\)]*?)）", r"(\1)"),  # Fullwidth parentheses
            (r"｛([^\}]*?)｝", r"{\1}"),  # Fullwidth braces
            (r"→", "->"),  # Arrow to Python operator
            (r"[“”]", '"'),  # Smart quotes to ASCII
            (r"[‘’]", "'"),  # Smart single quotes
        ]

        for pattern, replacement in corrections:
            normalised_code = re.sub(pattern, replacement, normalised_code)

        return normalised_code

    def parse(self):
        # Parse the code using the provided tokens
        self.program, self.error_message, self.error_box = parse_code(self.tokens)
        if self.program is None or self.error_message is not None:
            return (
                None,
                None,
                "Error: Parsing failed (" + self.error_message + ")",
                self.error_box,
            )

        # Generate Python code from the parsed program
        self.python_code = self.program.python_print() if self.program else None
        if self.python_code is None:
            return self.program, None, "Error: Python printing failed", None

        # Normalise the characters in the Python code
        self.python_code = self.normalise_python_code(self.python_code)
        if self.python_code is None:
            return self.program, None, "Error: Character normalisation failed", None

        return self.program, self.python_code, None, None

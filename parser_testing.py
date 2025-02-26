from code_detection.parse_code import *
from output.app import *

def main():
    python_code = test_parsing()
    run_editor(python_code)

if __name__ == "__main__":
    main()
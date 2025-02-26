from code_detection.parse_code import *
from output.projector_app import *

def main():
    python_code = test_parsing()
    run_editor(initial_code=python_code)

if __name__ == "__main__":
    main()
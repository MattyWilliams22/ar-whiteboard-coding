import cv2

from code_detection.detect_code import detect_text
from code_detection.tokenise import convert_to_tokens
from code_detection.parse_code import *
from code_detection.astnodes import *
from output.output import output

def main():
    image = cv2.imread("images/code/if/text/back_1_across_0.jpg")
    empty_mask = np.zeros(image.shape[:2], dtype="uint8")
    image, text = detect_text("paddleocr", image, empty_mask)

    print(text)
    print("\n")

    tokens = convert_to_tokens(text)
    print(tokens)
    print("\n")

    program = parse_code(tokens)
    print(program)
    print("\n")

    python_code = program.python_print()
    print(python_code)
    print("\n")

    output("project", image, python_code)

if __name__ == "__main__":
    main()
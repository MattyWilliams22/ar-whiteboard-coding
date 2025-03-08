import cv2

from code_detection.detect_code import detect_code
from code_detection.tokenise import convert_to_tokens, queue_to_string
from code_detection.parse_code import *
from code_detection.astnodes import *
from output.output import output

def main():
    image = cv2.imread("test_images/back_1_across_0.jpg")

    image, boxes = detect_code("aruco4x4_50", "paddleocr", image)

    print(boxes)
    print("\n")

    tokens = convert_to_tokens(boxes)
    print(queue_to_string(tokens))
    print("\n")

    program = parse_code(tokens)
    print(program)
    print("\n")

    python_code = program.python_print()
    print(python_code)
    print("\n")

    # python_code = test_parsing()

    output("window", image, python_code)

if __name__ == "__main__":
    main()
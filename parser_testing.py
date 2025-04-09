import cv2

from code_detection.detect_code import detect_code
from code_detection.tokeniser import convert_to_tokens, queue_to_string
from code_detection.parse_code import *
from code_detection.astnodes import *
from output.output import output
from output.boxes import display_bounding_boxes

def main():
    image = cv2.imread("test_images/normalised_test.jpg")

    image, boxes = detect_code("aruco6x6_50", "paddleocr", image)

    print(boxes)
    print("\n")

    # tokens = convert_to_tokens(boxes)
    # print(queue_to_string(tokens))
    # print("\n")

    # program = parse_code(tokens)
    # print(program)
    # print("\n")

    # python_code = program.python_print()
    # print(python_code)
    # print("\n")

    # python_code = test_parsing()

    # output("window", image, python_code)
    display_bounding_boxes(boxes, image_size=(1280, 790), aruco_dict_type=cv2.aruco.DICT_6X6_50, marker_size=35)

if __name__ == "__main__":
    main()
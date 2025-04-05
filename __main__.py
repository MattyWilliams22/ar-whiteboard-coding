import cv2
from preprocessing.normalisation import normalize_whiteboard
from code_detection.detect_code import detect_code
from code_detection.tokenise import convert_to_tokens
from code_detection.parse_code import *
from code_detection.astnodes import *
from output.output import output

INPUT_TYPE = "file"

PREPROCESSING_STEPS = [normalize_whiteboard]

MARKER_TYPE = "aruco6x6_50"
OCR_TYPE = "paddleocr"

OUTPUT_TYPE = "projector"

def get_input(input_type: str):
    if input_type == "file":
        image_path = input("Enter the path to the image: ")
        image = cv2.imread(image_path)
        return image
    elif input_type == "camera":
        cap = cv2.VideoCapture(0)
        _, image = cap.read()
        cap.release()
        return image
    
def main():
    image = get_input(INPUT_TYPE)

    if image is None:
        print("Error: Unable to load image")
        exit()

    for step in PREPROCESSING_STEPS:
        image = step(image)

    if image is None:
        print("Error: Preprocessing failed")
        exit()

    image, boxes = detect_code(MARKER_TYPE, OCR_TYPE, image)

    if image is None:
        print("Error: Code detection failed")
        exit()
    if boxes is None:
        print("Error: Box recognition failed")
        exit()
    print(boxes)
    print("\n")

    tokens = convert_to_tokens(boxes)
    if boxes is None:
        print("Error: Tokenisation failed")
        exit()
    print(tokens)
    print("\n")

    program = parse_code(tokens)
    if program is None:
        print("Error: Parsing failed")
        exit()
    print(program)
    print("\n")

    python_code = program.python_print()
    if program is None:
        print("Error: Python printing failed")
        exit()
    print(python_code)
    print("\n")

    output(OUTPUT_TYPE, image, python_code, boxes)

if __name__ == "__main__":
    main()


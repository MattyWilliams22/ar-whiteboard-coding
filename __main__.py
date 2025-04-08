import cv2
import io
import sys
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
        # image_path = input("Enter the path to the image: ")
        image_path = "test_images/IMG_1083.JPEG"

        image = cv2.imread(image_path)
        return image
    elif input_type == "camera":
        cap = cv2.VideoCapture(0)
        _, image = cap.read()
        cap.release()
        return image
    
def execute_python_code(python_code):
    # Redirect stdout to capture the output
    output_capture = io.StringIO()
    sys.stdout = output_capture

    try:
        exec(python_code, {})  # Execute the code in an isolated namespace
    except Exception as e:
        print(f"Error: {e}")  # Capture errors if any

    # Restore original stdout
    sys.stdout = sys.__stdout__

    # Get the captured output
    return output_capture.getvalue()
    
def process_image(image):
    for step in PREPROCESSING_STEPS:
        image = step(image)

    if image is None:
        return None, None, "Error: Preprocessing failed"

    image, boxes = detect_code(MARKER_TYPE, OCR_TYPE, image)

    if image is None:
        return boxes, None, "Error: Code detection failed"
    if boxes is None:
        return None, None, "Error: Box recognition failed"
    print(boxes)
    print("\n")

    tokens = convert_to_tokens(boxes)
    if boxes is None:
        return boxes, None, "Error: Tokenisation failed"
    print(tokens)
    print("\n")

    program = parse_code(tokens)
    if program is None:
        return boxes, None, "Error: Parsing failed"
    print(program)
    print("\n")

    python_code = program.python_print()
    if python_code is None:
        return boxes, None, "Error: Python printing failed"
    print(python_code)
    print("\n")

    code_output = execute_python_code(python_code)
    if code_output is None:
        return boxes, python_code, "Error: Code execution failed"

    return boxes, python_code, code_output
    
def main():
    image = get_input(INPUT_TYPE)

    if image is None:
        print("Error: Unable to load image")
        exit()

    boxes, python_code, code_output = process_image(image)

    projection = output(OUTPUT_TYPE, image, python_code, code_output, boxes)
    if projection is None:
        print("Error: Output failed")
        exit()

    cv2.imshow("Output", projection)
    cv2.waitKey(0)
    cv2.destroyAllWindows()

if __name__ == "__main__":
    main()


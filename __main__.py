import cv2
import io
import sys
from preprocessing.preprocessor import Preprocessor
from code_detection.detect_code import detect_code
from code_detection.tokenise import convert_to_tokens
from code_detection.parse_code import *
from code_detection.astnodes import *
from output.output import output
from output.projector import Projector

INPUT_TYPE = "file"

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
    preprocessor = Preprocessor(image)
    image = preprocessor.preprocess_image()
    if image is None:
        return None, None, None, "Error: Preprocessing failed", None

    image, boxes = detect_code(MARKER_TYPE, OCR_TYPE, image)

    if image is None:
        return image, boxes, None, "Error: Code detection failed", None
    if boxes is None:
        return image, None, None, "Error: Box recognition failed", None
    # print(boxes)
    # print("\n")

    tokens = convert_to_tokens(boxes)
    if boxes is None:
        return image, boxes, None, "Error: Tokenisation failed", None
    # print(tokens)
    # print("\n")

    program, error, error_box = parse_code(tokens)
    if program is None or error is not None:
        return image, boxes, None, "Error: Parsing failed (" + error + ")", error_box
    # print(program)
    # print("\n")

    python_code = program.python_print()
    if python_code is None:
        return image, boxes, None, "Error: Python printing failed", None
    # print(python_code)
    # print("\n")

    code_output = execute_python_code(python_code)
    if code_output is None:
        return image, boxes, python_code, "Error: Code execution failed", None

    return image, boxes, python_code, code_output, error_box
    
def main():
    image = get_input(INPUT_TYPE)

    if image is None:
        print("Error: Unable to load image")
        exit()

    image, boxes, python_code, code_output, error_box = process_image(image)

    if python_code is None:
        python_code = "..."
    if code_output is None:
        code_output = "..."

    projector = Projector(image, python_code, code_output, boxes, error_box)

    projection = projector.display_full_projection()
    if projection is None:
        print("Error: Projection failed")
        exit()

    cv2.namedWindow('Output', cv2.WINDOW_NORMAL)
    cv2.setWindowProperty('Output', cv2.WND_PROP_FULLSCREEN, cv2.WINDOW_FULLSCREEN)
    cv2.imshow("Output", projection)
    cv2.waitKey(0)
    cv2.destroyAllWindows()

if __name__ == "__main__":
    main()


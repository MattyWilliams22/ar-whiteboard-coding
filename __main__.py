import cv2
import io
import sys
from input.camera import Camera
from preprocessing.preprocessor import Preprocessor
from code_detection.detector import Detector
from code_detection.tokeniser import Tokeniser
from code_detection.parser import Parser
from execution.executor import Executor
from output.projector import Projector

MARKER_TYPE = "aruco6x6_50"
OCR_TYPE = "paddleocr"

OUTPUT_TYPE = "projector"
    
def process_image(image):
    preprocessor = Preprocessor(image)
    image = preprocessor.preprocess_image()
    if image is None:
        return None, None, None, "Error: Preprocessing failed", None

    detector = Detector(image)
    image, boxes = detector.detect_code()
    if image is None:
        return image, boxes, None, "Error: Code detection failed", None
    if boxes is None:
        return image, None, None, "Error: Box recognition failed", None

    tokeniser = Tokeniser(boxes)
    tokens = tokeniser.tokenise()
    if tokens is None:
        return image, boxes, None, "Error: Tokenisation failed", None

    parser = Parser(tokens)
    program, python_code, error_message, error_box = parser.parse()
    if program is None or python_code is None:
        return image, boxes, python_code, error_message, error_box

    executor = Executor(python_code)
    code_output, error_message = executor.execute()
    if error_message is not None:
        return image, boxes, python_code, error_message, None
    if code_output is None:
        return image, boxes, python_code, "Error: Code execution failed", None

    return image, boxes, python_code, code_output, error_box
    
def main():
    camera = Camera(debug_mode=True)

    image = camera.capture_frame()
    if image is None:
        print("Error: Unable to capture frame")
        exit()

    image, boxes, python_code, code_output, error_box = process_image(image)

    if python_code is None:
        python_code = "..."
    if code_output is None:
        code_output = "..."

    projector = Projector(image, python_code, code_output, boxes, error_box, debug_mode=True)
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


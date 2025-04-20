import cv2
import time
from controller import Controller
from input.camera_preview import CameraPreviewThread
from preprocessing.preprocessor import Preprocessor
from code_detection.detector import Detector
from code_detection.tokeniser import Tokeniser
from code_detection.parser import Parser
from execution.executor import Executor
from output.projector import Projector

PROJECT_IMAGE = True

def process_image(image):
    preprocessor = Preprocessor(image)
    image = preprocessor.preprocess_image()
    if image is None:
        return None, None, None, "Error: Preprocessing failed", None

    detector = Detector(image)
    image, boxes = detector.detect_code()
    if image is None or boxes is None:
        return image, boxes, None, "Error: Code detection failed", None

    tokeniser = Tokeniser(boxes)
    tokens = tokeniser.tokenise()
    if tokens is None:
        return image, boxes, None, "Error: Tokenisation failed", None

    parser = Parser(tokens)
    program, python_code, error_message, error_box = parser.parse()
    if program is None or python_code is None:
        return image, boxes, python_code, error_message, error_box

    executor = Executor(python_code)
    code_output, error_message = executor.execute_in_sandbox()
    if error_message is not None:
        return image, boxes, python_code, error_message, None
    if code_output is None:
        return image, boxes, python_code, "Error: Code execution failed", None

    return image, boxes, python_code, code_output, error_box

def run_code_from_frame(preview):
    # Display minimal projection first
    projector = Projector(None, None, None, None, None, debug_mode=False)
    minimal_projection = projector.display_minimal_projection()

    if minimal_projection is None:
        print("Error: Minimal projection failed.")
        return None

    # Show minimal projection
    cv2.imshow("Output", minimal_projection)
    cv2.waitKey(1)  # Let window update

    # Wait a short moment to ensure projection is visible (adjust if needed)
    time.sleep(1.0)

    # Capture stable frame from preview
    frame = None
    for _ in range(10):
        frame = preview.get_frame()
        if frame is not None:
            break
        time.sleep(0.1)

    if frame is None:
        print("Failed to get frame from preview.")
        return None

    # Process the image from camera
    image, boxes, python_code, code_output, error_box = process_image(frame)

    if python_code is None:
        python_code = "..."
    if code_output is None:
        code_output = "..."

    # Show full projection
    projector = Projector(image, python_code, code_output, boxes, error_box, debug_mode=True)
    projection = projector.display_full_projection()

    if projection is not None:
        cv2.imshow("Output", projection)

    return projection


def main():
    preview = CameraPreviewThread(source=1, resolution=(3840, 2160), fps=10)
    preview.start()

    cv2.namedWindow("Camera Feed", cv2.WINDOW_NORMAL)
    cv2.resizeWindow("Camera Feed", 1280, 720)
    cv2.namedWindow("Output", cv2.WINDOW_NORMAL)
    cv2.setWindowProperty("Output", cv2.WND_PROP_FULLSCREEN, cv2.WINDOW_FULLSCREEN)

    try:
        while True:
            frame = preview.get_frame()
            if frame is not None:
                cv2.imshow("Camera Feed", frame)

            # Check if the Output window is closed
            if cv2.getWindowProperty("Output", cv2.WND_PROP_VISIBLE) < 1:
                break

            key = cv2.waitKey(1) & 0xFF
            if key == ord('q'):
                break
            elif key == ord('r'):
                # Run code processing on current frame
                projection = run_code_from_frame(preview)
                if projection is not None:
                    cv2.imshow("Output", projection)

    finally:
        preview.stop()
        preview.join()
        cv2.destroyAllWindows()

if __name__ == "__main__":
    main()

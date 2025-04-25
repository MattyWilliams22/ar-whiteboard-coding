import cv2
import time
from input.camera_preview import CameraPreviewThread
from input.voice_control import VoiceCommandListener  # ✅ Uses updated implementation
from preprocessing.preprocessor import Preprocessor
from code_detection.detector import Detector
from code_detection.tokeniser import Tokeniser
from code_detection.parser import Parser
from execution.executor import Executor
from output.projector import Projector

ACCESS_KEY = "duY+um2g68Nn2ctqSjm2QlIkmyaMRV2mRkgG4XmpjYHruBDK4AsWWw=="
PROJECT_IMAGE = False

def process_image(preprocessor):
    warped_image = preprocessor.preprocess_image()
    if warped_image is None:
        return None, None, None, "Error: Image preprocessing failed", None

    detector = Detector(warped_image)
    warped_image, boxes = detector.detect_code()
    if warped_image is None or boxes is None:
        return warped_image, boxes, None, "Error: Code detection failed", None

    tokeniser = Tokeniser(boxes)
    tokens = tokeniser.tokenise()
    if tokens is None:
        return warped_image, boxes, None, "Error: Tokenisation failed", None
    print(tokeniser.tokens_to_string())

    parser = Parser(tokens)
    program, python_code, error_message, error_box = parser.parse()
    if program is None or python_code is None:
        return warped_image, boxes, python_code, error_message, error_box

    executor = Executor(python_code)
    code_output, error_message = executor.execute_in_sandbox()
    if error_message is not None:
        return warped_image, boxes, python_code, error_message, None
    if code_output is None:
        return warped_image, boxes, python_code, "Error: Code execution failed", None

    return warped_image, boxes, python_code, code_output, error_box

def run_code_from_frame(preview):
    projector = Projector(None, None, None, None, None, debug_mode=False)
    minimal_projection = projector.display_minimal_projection()

    if minimal_projection is None:
        print("Error: Minimal projection failed.")
        return None

    cv2.imshow("Output", minimal_projection)
    cv2.waitKey(1)
    time.sleep(1.0)

    max_attempts = 20
    interval = 0.3

    preprocessor = None
    warped_image = None

    for attempt in range(max_attempts):
        frame = preview.get_frame()
        if frame is None:
            time.sleep(interval)
            continue

        preprocessor = Preprocessor(frame)
        warped_image = preprocessor.preprocess_image()

        if warped_image is not None:
            print(f"Valid frame captured on attempt {attempt + 1}")
            break

        print(f"Attempt {attempt + 1}/{max_attempts}: Not all corner markers detected.")
        time.sleep(interval)

    if preprocessor is None or warped_image is None:
        print("Failed to detect all 4 corner markers after multiple attempts.")
        return None

    image, boxes, python_code, code_output, error_box = process_image(preprocessor)

    if python_code is None:
        python_code = "..."
    if code_output is None:
        code_output = "..."

    projector = Projector(image, python_code, code_output, boxes, error_box, debug_mode=PROJECT_IMAGE)
    projection = projector.display_full_projection()

    if projection is not None:
        cv2.imshow("Output", projection)

    return projection

def handle_voice_command(command):
    if "start" in command or "execute" in command:
        print("Voice: Running code...")
        projection = run_code_from_frame(preview)
        if projection is not None:
            cv2.imshow("Output", projection)
    elif "clear" in command:
        print("Voice: Returning to minimal projection.")
        projector = Projector(None, None, None, None, None, debug_mode=False)
        minimal = projector.display_minimal_projection()
        if minimal is not None:
            cv2.imshow("Output", minimal)
    elif "exit" in command or "quit" in command:
        print("Voice: Exiting...")
        listener.stop()
        preview.stop()
        preview.join()
        listener.join()
        cv2.destroyAllWindows()
        exit()

def main():
    global preview, listener

    preview = CameraPreviewThread(source=1, resolution=(3840, 2160), fps=10)
    preview.start()

    listener = VoiceCommandListener(callback=handle_voice_command, access_key=ACCESS_KEY)
    listener.start()

    cv2.namedWindow("Camera Feed", cv2.WINDOW_NORMAL)
    cv2.resizeWindow("Camera Feed", 1280, 720)
    cv2.namedWindow("Output", cv2.WINDOW_NORMAL)
    cv2.setWindowProperty("Output", cv2.WND_PROP_FULLSCREEN, cv2.WINDOW_FULLSCREEN)

    try:
        while True:
            frame = preview.get_frame()
            if frame is not None:
                cv2.imshow("Camera Feed", frame)

            if cv2.getWindowProperty("Output", cv2.WND_PROP_VISIBLE) < 1:
                break

            key = cv2.waitKey(1) & 0xFF
            if key == ord('q'):
                break
            elif key == ord('r'):
                projection = run_code_from_frame(preview)
                if projection is not None:
                    cv2.imshow("Output", projection)

    finally:
        listener.stop()
        listener.join()
        preview.stop()
        preview.join()
        cv2.destroyAllWindows()

if __name__ == "__main__":
    main()

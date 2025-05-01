import cv2
import time
import tkinter as tk
from enum import Enum, auto
from threading import Lock
from input.camera_preview import CameraPreviewThread
from preprocessing.preprocessor import Preprocessor
from code_detection.detector import Detector
from code_detection.tokeniser import Tokeniser
from code_detection.parser import Parser
from execution.executor import Executor
from output.projector import Projector
from input.settings_menu import SettingsMenu
from settings import settings, load_settings
from fsm.states import SystemState, Event
from fsm.state_machine import SystemFSM

# ======================
# APPLICATION FUNCTIONS
# ======================
def collect_valid_images(preview, num_required, max_attempts=50, interval=0.2):
    valid_images = []
    attempts = 0
    while len(valid_images) < num_required and attempts < max_attempts:
        frame = preview.get_frame()
        if frame is None:
            time.sleep(interval)
            attempts += 1
            continue

        preprocessor = Preprocessor(frame)
        warped_image = preprocessor.preprocess_image()

        if warped_image is not None:
            valid_images.append(warped_image)
            print(f"Captured valid image {len(valid_images)} of {num_required}")
        else:
            print(f"Attempt {attempts + 1}/{max_attempts}: Not all corner markers detected.")
        attempts += 1
        time.sleep(interval)
    return valid_images

def process_images(warped_images):
    detector = Detector(warped_images)
    warped_image, boxes = detector.detect_code()
    if warped_image is None or boxes is None:
        return warped_image, boxes, None, "Error: Code detection failed", None

    tokeniser = Tokeniser(boxes)
    tokens = tokeniser.tokenise()
    if tokens is None:
        return warped_image, boxes, None, "Error: Tokenisation failed", None

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

def run_code_from_frame(preview, fsm):
    if not fsm.transition(Event.START_RUN):
        return None

    projector = Projector(None, None, None, None, None,
                        output_size=tuple(settings["PROJECTION_RESOLUTION"]),
                        marker_size=settings["CORNER_MARKER_SIZE"],
                        debug_mode=False)
    minimal_projection = projector.display_minimal_projection()

    if minimal_projection is None:
        print("Error: Minimal projection failed.")
        fsm.transition(Event.ERROR)
        return None

    cv2.imshow("Output", minimal_projection)
    cv2.waitKey(1)
    time.sleep(1.0)

    valid_images = collect_valid_images(preview, settings["NUM_VALID_IMAGES"])
    if len(valid_images) < settings["NUM_VALID_IMAGES"]:
        print("Insufficient valid images collected.")
        fsm.transition(Event.ERROR)
        return None

    image, boxes, python_code, code_output, error_box = process_images(valid_images)
    if python_code is None:
        python_code = "..."
    if code_output is None:
        code_output = "..."

    projector = Projector(image, python_code, code_output, boxes, error_box,
                        output_size=tuple(settings["PROJECTION_RESOLUTION"]),
                        marker_size=settings["CORNER_MARKER_SIZE"],
                        debug_mode=settings["PROJECT_IMAGE"])
    projection = projector.display_full_projection()

    if projection is not None:
        cv2.imshow("Output", projection)
        fsm.transition(Event.TOGGLE_PROJECT)
        return projection
    else:
        fsm.transition(Event.ERROR)
        return None

def show_settings_menu(fsm):
    if not fsm.transition(Event.OPEN_SETTINGS):
        return

    root = tk.Tk()
    app = SettingsMenu(root, None)
    root.mainloop()
    load_settings()
    fsm.transition(Event.CLOSE_SETTINGS)

def main():
    fsm = SystemFSM()
    show_settings_menu(fsm)  # Start with settings

    preview = CameraPreviewThread(
        source=settings["CAMERA"],
        resolution=tuple(settings["CAMERA_RESOLUTION"]),
        fps=settings["CAMERA_FPS"]
    )
    preview.start()

    cv2.namedWindow("Camera Feed", cv2.WINDOW_NORMAL)
    cv2.resizeWindow("Camera Feed", 1280, 720)
    cv2.namedWindow("Output", cv2.WINDOW_NORMAL)
    cv2.setWindowProperty("Output", cv2.WND_PROP_FULLSCREEN, cv2.WINDOW_FULLSCREEN)

    try:
        while fsm.state != SystemState.EXITING:
            frame = preview.get_frame()
            if frame is not None and fsm.state != SystemState.SETTINGS:
                cv2.imshow("Camera Feed", frame)

            if cv2.getWindowProperty("Output", cv2.WND_PROP_VISIBLE) < 1:
                fsm.transition(Event.EXIT)
                break

            key = cv2.waitKey(1) & 0xFF
            if key == ord('q'):
                fsm.transition(Event.STOP_RUN)
            elif key == ord('r') and fsm.state in (SystemState.IDLE, SystemState.PROJECTING):
                run_code_from_frame(preview, fsm)
            elif key == ord('s') and fsm.state != SystemState.SETTINGS:
                show_settings_menu(fsm)
            elif key == 27:  # ESC key
                fsm.transition(Event.EXIT)

    finally:
        preview.stop()
        preview.join()
        cv2.destroyAllWindows()

if __name__ == "__main__":
    main()
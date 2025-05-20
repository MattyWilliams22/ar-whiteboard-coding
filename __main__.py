import cv2
import os
import time
import tkinter as tk
from threading import Lock
from input.camera_preview import CameraPreviewThread
from input.voice_commands import VoiceCommandThread
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
from dotenv import load_dotenv

load_dotenv()


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
            print(
                f"Attempt {attempts + 1}/{max_attempts}: Not all corner markers detected."
            )
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
    print(tokeniser.tokens_to_string())
    if tokens is None:
        return warped_image, boxes, None, "Error: Tokenisation failed", None

    parser = Parser(tokens)
    program, python_code, error_message, error_box = parser.parse()
    if program is None or python_code is None:
        return warped_image, boxes, python_code, error_message, error_box

    executor = Executor(python_code)
    code_output, error_message, python_code = executor.execute_in_sandbox()
    if error_message is not None:
        return warped_image, boxes, python_code, error_message, None
    if code_output is None:
        return warped_image, boxes, python_code, "Error: Code execution failed", None

    return warped_image, boxes, python_code, code_output, error_box


def run_code_from_frame(preview, fsm):
    try:
        # Display minimal projection
        projector = Projector(
            None,
            None,
            None,
            None,
            None,
            output_size=tuple(settings["PROJECTION_RESOLUTION"]),
            marker_size=settings["CORNER_MARKER_SIZE"],
            debug_mode=False,
        )
        minimal_projection = projector.display_minimal_projection()
        cv2.imshow("Output", minimal_projection)
        cv2.waitKey(1)

        # Collect and process images
        valid_images = collect_valid_images(preview, settings["NUM_VALID_IMAGES"])
        if len(valid_images) < settings["NUM_VALID_IMAGES"]:
            error_projection = Projector(
                None,
                None,
                "Failed to capture enough valid images.",
                None,
                None,
                output_size=tuple(settings["PROJECTION_RESOLUTION"]),
                marker_size=settings["CORNER_MARKER_SIZE"],
                debug_mode=settings["PROJECT_IMAGE"],
            ).display_error_projection()
            cv2.imshow("Output", error_projection)
            fsm.transition(Event.ERROR_OCCURRED)
            return None

        image, boxes, python_code, code_output, error_box = process_images(valid_images)
        if code_output is None or python_code is None:
            error_projection = Projector(
                image,
                python_code,
                code_output,
                boxes,
                error_box,
                output_size=tuple(settings["PROJECTION_RESOLUTION"]),
                marker_size=settings["CORNER_MARKER_SIZE"],
                debug_mode=settings["PROJECT_IMAGE"],
            ).display_full_projection()
            cv2.imshow("Output", error_projection)
            fsm.transition(Event.ERROR_OCCURRED)
            return None

        # Display full projection
        projector = Projector(
            image,
            python_code,
            code_output,
            boxes,
            error_box,
            output_size=tuple(settings["PROJECTION_RESOLUTION"]),
            marker_size=settings["CORNER_MARKER_SIZE"],
            debug_mode=settings["PROJECT_IMAGE"],
        )
        projection = projector.display_full_projection()
        cv2.imshow("Output", projection)
        fsm.transition(Event.FINISH_RUN)
        return python_code

    except Exception as e:
        error_projection = Projector(
                None,
                None,
                str(e),
                None,
                None,
                output_size=tuple(settings["PROJECTION_RESOLUTION"]),
                marker_size=settings["CORNER_MARKER_SIZE"],
                debug_mode=settings["PROJECT_IMAGE"],
            ).display_error_projection()
        cv2.imshow("Output", error_projection)
        fsm.transition(Event.ERROR_OCCURRED)
        return None


def show_settings_menu(camera_preview=None, voice_thread=None):
    root = tk.Tk()
    app = SettingsMenu(root, camera_preview, voice_thread)
    root.mainloop()
    load_settings()

def save_code_to_file(python_code):
    if python_code is None:
        print("No code to save.")
        return

    if os.path.exists(settings["CODE_SAVE_PATH"]):
        with open(settings["CODE_SAVE_PATH"], "r") as file:
            existing_code = file.read()
        if existing_code == python_code:
            print("Code is already saved.")
            return
    else: 
        os.makedirs(os.path.dirname(settings["CODE_SAVE_PATH"]), exist_ok=True)
    with open(settings["CODE_SAVE_PATH"], "w") as file:
        file.write(python_code)
    print(f"Code saved to {settings["CODE_SAVE_PATH"]}")


def main():
    fsm = SystemFSM()
    load_settings()

    # Initialize voice thread based on settings
    voice_thread = None
    try:
        voice_thread = VoiceCommandThread(
            fsm=fsm,
            access_key=os.getenv("PORCUPINE_ACCESS_KEY"),
            settings=settings,
            hotword_sensitivity=0.5,
            command_timeout=3,
        )
        voice_thread.start()
        if settings["VOICE_COMMANDS"]:
            voice_thread.set_active()
    except Exception as e:
        print(f"Failed to initialize voice commands: {e}")
        settings["VOICE_COMMANDS"] = False

    show_settings_menu(voice_thread=voice_thread)

    preview = CameraPreviewThread(
        source=settings["CAMERA"],
        resolution=tuple(settings["CAMERA_RESOLUTION"]),
        fps=settings["CAMERA_FPS"],
    )
    preview.start()

    cv2.namedWindow("Camera Feed", cv2.WINDOW_NORMAL)
    cv2.resizeWindow("Camera Feed", 1280, 720)
    cv2.namedWindow("Output", cv2.WINDOW_NORMAL)
    cv2.setWindowProperty("Output", cv2.WND_PROP_FULLSCREEN, cv2.WINDOW_FULLSCREEN)

    python_code = None

    try:
        while fsm.state != SystemState.EXITING:
            frame = preview.get_frame()
            if frame is not None:
                cv2.imshow("Camera Feed", frame)

            if cv2.getWindowProperty("Output", cv2.WND_PROP_VISIBLE) < 1:
                fsm.transition(Event.EXIT)
                break

            # Handle state-specific rendering
            if fsm.state == SystemState.IDLE:
                projector = Projector(
                    None,
                    None,
                    None,
                    None,
                    None,
                    output_size=tuple(settings["PROJECTION_RESOLUTION"]),
                    marker_size=settings["CORNER_MARKER_SIZE"],
                    debug_mode=False,
                )
                minimal_projection = projector.display_minimal_projection()
                cv2.imshow("Output", minimal_projection)
            elif fsm.state == SystemState.RUNNING:
                python_code = run_code_from_frame(preview, fsm)

            # Handle key inputs
            key = cv2.waitKey(1) & 0xFF
            if key == ord("q"):
                fsm.transition(Event.CLEAR)
            elif key == ord("r"):
                fsm.transition(Event.START_RUN)
            elif key == ord("s"):
                show_settings_menu(preview, voice_thread)
            elif key == ord("v"):
                save_code_to_file(python_code)
            elif key == 27:  # ESC key
                fsm.transition(Event.EXIT)

    finally:
        preview.stop()
        preview.join()
        if voice_thread:
            voice_thread.stop()
            voice_thread.join()
        cv2.destroyAllWindows()


if __name__ == "__main__":
    main()

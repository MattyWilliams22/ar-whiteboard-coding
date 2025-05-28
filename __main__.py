import cv2
import os
import time
import tkinter as tk
from accuracy_metrics import analyse_code_quality, save_metrics_to_csv
import numpy as np
import csv
from datetime import datetime
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

GROUND_TRUTH_FILE = "evaluation_programs/program_1.py"

load_dotenv()


def collect_valid_images(preview, num_required, max_attempts=50, interval=0.2):
    """Collect valid images from the camera preview window."""
    start_time = time.time()
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
            continue
        else:
            print(
                f"Attempt {attempts + 1}/{max_attempts}: Not all corner markers detected."
            )
        attempts += 1
        time.sleep(interval)
    end_time = time.time()
    return valid_images, end_time - start_time


def process_images(warped_images):
    """Process the images to detect code, tokenise, parse, and execute."""
    timing_data = {}

    # Code detection
    start_time = time.time()
    detector = Detector(warped_images)
    warped_image, boxes = detector.detect_code()
    timing_data["detection"] = time.time() - start_time

    if warped_image is None or boxes is None:
        return (
            warped_image,
            boxes,
            None,
            "Error: Code detection failed",
            None,
            timing_data,
        )

    # Tokenisation
    start_time = time.time()
    tokeniser = Tokeniser(boxes)
    tokens = tokeniser.tokenise()
    timing_data["tokenisation"] = time.time() - start_time
    print(tokeniser.tokens_to_string())
    if tokens is None:
        return (
            warped_image,
            boxes,
            None,
            "Error: Tokenisation failed",
            None,
            timing_data,
        )

    # Parsing
    start_time = time.time()
    parser = Parser(tokens)
    program, python_code, error_message, error_box = parser.parse()
    timing_data["parsing"] = time.time() - start_time
    if program is None or python_code is None:
        return warped_image, boxes, python_code, error_message, error_box, timing_data

    # Execution
    start_time = time.time()
    executor = Executor(python_code)
    code_output, error_message, python_code = executor.execute_in_sandbox()
    timing_data["execution"] = time.time() - start_time
    if error_message is not None:
        return warped_image, boxes, python_code, error_message, None, timing_data

    return warped_image, boxes, python_code, code_output, error_box, timing_data


def save_timing_data(timing_data):
    """Save timing data to a CSV file."""
    filename = "timing_data.csv"
    file_exists = os.path.isfile(filename)

    # Prepare data row
    row = {
        "timestamp": datetime.now().isoformat(),
        "total_time": timing_data.get("total", 0),
        "image_capture": timing_data.get("image_capture", 0),
        "detection": timing_data.get("detection", 0),
        "tokenisation": timing_data.get("tokenisation", 0),
        "parsing": timing_data.get("parsing", 0),
        "execution": timing_data.get("execution", 0),
        "projection": timing_data.get("projection", 0),
        "success": timing_data.get("success", False),
    }

    # Write to CSV
    with open(filename, "a", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=row.keys())
        if not file_exists:
            writer.writeheader()
        writer.writerow(row)


def detect_and_run_code(preview, fsm):
    """Detect and run the whiteboard code"""
    timing_data = {}
    total_start_time = time.time()

    try:
        # Display minimal projection
        start_time = time.time()
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
        timing_data["projection"] = time.time() - start_time

        # Collect valid images
        timing_data["detection_confidence"] = settings["NUM_VALID_IMAGES"]
        valid_images, capture_time = collect_valid_images(
            preview, settings["NUM_VALID_IMAGES"]
        )
        timing_data["image_capture"] = capture_time

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
            timing_data["total_time"] = time.time() - total_start_time
            timing_data["success"] = False
            save_metrics_to_csv(timing_data, {})
            return None, None

        # Detect and execute code
        image, boxes, python_code, code_output, error_box, process_timing = (
            process_images(valid_images)
        )
        timing_data.update(process_timing)

        # Calculate accuracy metrics if we have code
        accuracy_metrics = {}
        if python_code:
            accuracy_metrics = analyse_code_quality(
                python_code,
                ground_truth_path=GROUND_TRUTH_FILE,
            )
        if code_output is None or python_code is None:
            error_projection, code_box = Projector(
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
            timing_data["total_time"] = time.time() - total_start_time
            timing_data["success"] = False
            save_metrics_to_csv(timing_data, accuracy_metrics)
            return None, code_box
        
        # Display full projection
        start_time = time.time()
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
        projection, code_box = projector.display_full_projection()
        cv2.imshow("Output", projection)
        timing_data["projection"] += time.time() - start_time

        fsm.transition(Event.FINISH_RUN)
        timing_data["total_time"] = time.time() - total_start_time
        timing_data["success"] = True
        save_metrics_to_csv(timing_data, accuracy_metrics)
        return python_code, code_box

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
        timing_data["total_time"] = time.time() - total_start_time
        timing_data["success"] = False
        save_metrics_to_csv(timing_data, {})
        return None, None


def show_settings_menu(camera_preview=None, voice_thread=None):
    """Display the settings menu."""
    root = tk.Tk()
    app = SettingsMenu(root, camera_preview, voice_thread)
    root.mainloop()
    load_settings()


def save_code_to_file(python_code):
    """Save the generated Python code to a file."""

    if python_code is None:
        print("No code to save.")
        return

    # Get the absolute path relative to this module's location
    base_dir = os.path.dirname(os.path.abspath(__file__))
    full_path = os.path.join(base_dir, settings["CODE_SAVE_PATH"])

    if os.path.exists(full_path):
        with open(full_path, "r") as file:
            existing_code = file.read()
        if existing_code == python_code:
            print("Code is already saved.")
            return
    else:
        os.makedirs(os.path.dirname(full_path), exist_ok=True)

    with open(full_path, "w") as file:
        file.write(python_code)

    print(f"Code saved to {full_path}")


def main():
    """Main function to run the system."""
    fsm = SystemFSM()
    load_settings()

    # Initialise voice thread based on settings
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

    # Display the settings menu
    show_settings_menu(voice_thread=voice_thread)

    # Initialise camera preview window
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
    code_box = None

    # Start the main loop
    try:
        while fsm.state != SystemState.EXITING:
            # Display camera feed
            frame = preview.get_frame()
            if frame is not None:
                cv2.imshow("Camera Feed", frame)

            if cv2.getWindowProperty("Output", cv2.WND_PROP_VISIBLE) < 1:
                fsm.transition(Event.EXIT)
                break

            # Handle current state if necessary
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
                minimal_projection = projector.display_idle_projection(code_box)
                cv2.imshow("Output", minimal_projection)
            elif fsm.state == SystemState.RUNNING:
                python_code, code_box = detect_and_run_code(preview, fsm)

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
        # Clean up resources
        preview.stop()
        preview.join()
        if voice_thread:
            voice_thread.stop()
            voice_thread.join()
        cv2.destroyAllWindows()


if __name__ == "__main__":
    main()

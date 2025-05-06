import cv2
import os
import time
import tkinter as tk
from threading import Thread
from input.camera import CameraManager
from input.camera_preview import CameraPreviewThread
from input.hand_gestures import HandGestureThread
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

class WhiteboardSystem:
    def __init__(self):
        self.fsm = SystemFSM()
        self.camera_manager = None
        self.camera_thread = None
        self.preview_thread = None
        self.voice_thread = None
        self.gesture_thread = None

    def initialize_system(self):
        """Initialize all system components"""
        load_settings()

        show_settings_menu()
        
        # Initialize Camera Manager (core camera access)
        self.camera_manager = CameraManager(
            camera_index=settings["CAMERA"],
            resolution=tuple(settings["CAMERA_RESOLUTION"]),
            fps=settings["CAMERA_FPS"]
        )
        self.camera_thread = Thread(target=self.camera_manager.run, daemon=True)
        self.camera_thread.start()

        # Initialize Preview Thread
        self.preview_thread = CameraPreviewThread(
            camera_manager=self.camera_manager,
            window_name="Camera Preview",
        )
        self.preview_thread.start()

        # Initialize Voice Thread
        if settings["VOICE_COMMANDS"]:
            try:
                self.voice_thread = VoiceCommandThread(
                    fsm=self.fsm,
                    access_key=os.getenv("PORCUPINE_ACCESS_KEY"),
                    settings=settings
                )
                self.voice_thread.start()
            except Exception as e:
                print(f"Voice init failed: {e}")
                settings["VOICE_COMMANDS"] = False

        # Initialize Gesture Thread
        if settings["HAND_GESTURES"]:
            try:
                self.gesture_thread = HandGestureThread(
                    fsm=self.fsm,
                    camera_manager=self.camera_manager,
                    settings=settings
                )
                self.gesture_thread.start()
            except Exception as e:
                print(f"Gesture init failed: {e}")
                settings["HAND_GESTURES"] = False

    def run(self):
        """Main application loop"""
        cv2.namedWindow("Output", cv2.WINDOW_NORMAL)
        cv2.setWindowProperty("Output", cv2.WND_PROP_FULLSCREEN, cv2.WINDOW_FULLSCREEN)

        try:
            while self.fsm.state != SystemState.EXITING:
                # Handle state transitions
                if self.fsm.state == SystemState.IDLE:
                    self.show_minimal_projection()
                elif self.fsm.state == SystemState.RUNNING:
                    self.run_code_from_frame()

                # Handle key inputs
                key = cv2.waitKey(1) & 0xFF
                if key == ord("q"): self.fsm.transition(Event.CLEAR)
                elif key == ord("r"): self.fsm.transition(Event.START_RUN)
                elif key == ord("s"): self.show_settings()
                elif key == 27: self.fsm.transition(Event.EXIT)

        finally:
            self.cleanup()

    def show_minimal_projection(self):
        """Display idle state projection"""
        projector = Projector(
            None, None, None, None, None,
            output_size=tuple(settings["PROJECTION_RESOLUTION"]),
            marker_size=settings["CORNER_MARKER_SIZE"]
        )
        cv2.imshow("Output", projector.display_minimal_projection())

    def show_error(self, message):
        """Display error message in projection"""
        error_projection = Projector(
            None,
            None,
            message,
            None,
            None,
            output_size=tuple(settings["PROJECTION_RESOLUTION"]),
            marker_size=settings["CORNER_MARKER_SIZE"],
            debug_mode=settings["PROJECT_IMAGE"],
        ).display_error_projection()
        cv2.imshow("Output", error_projection)
        self.fsm.transition(Event.ERROR_OCCURRED)

    def show_result(self, image, boxes, python_code, code_output, error_box=None):
        """Display successful processing result"""
        projection = Projector(
            image,
            python_code,
            code_output,
            boxes,
            error_box,
            output_size=tuple(settings["PROJECTION_RESOLUTION"]),
            marker_size=settings["CORNER_MARKER_SIZE"],
            debug_mode=settings["PROJECT_IMAGE"],
        ).display_full_projection()
        cv2.imshow("Output", projection)
        self.fsm.transition(Event.FINISH_RUN)

    def run_code_from_frame(self):
        """Execute the full whiteboard processing pipeline"""
        try:
            valid_images = self.collect_valid_images(settings["NUM_VALID_IMAGES"])
            if len(valid_images) < settings["NUM_VALID_IMAGES"]:
                self.show_error("Failed to capture enough valid images.")
                return

            result = self.process_images(valid_images)
            if result.error:
                self.show_error(result.error_message)
            else:
                self.show_result(*result)

        except Exception as e:
            self.show_error(str(e))

    def collect_valid_images(self, num_required):
        """Capture valid preprocessed images"""
        valid_images = []
        attempts = 0
        while len(valid_images) < num_required and attempts < 50:
            frame = self.camera_manager.get_frame()
            if frame is None:
                time.sleep(0.2)
                attempts += 1
                continue

            warped = Preprocessor(frame).preprocess_image()
            if warped is not None:
                valid_images.append(warped)
                print(f"Captured {len(valid_images)}/{num_required} valid images")
            attempts += 1
        return valid_images

    def process_images(self, images):
        """Process images through detection pipeline"""
        detector = Detector(images)
        warped_image, boxes = detector.detect_code()
        if not warped_image:
            return ProcessResult(error=True, error_message="Code detection failed")

        tokens = Tokeniser(boxes).tokenise()
        if not tokens:
            return ProcessResult(error=True, error_message="Tokenization failed")

        parse_result = Parser(tokens).parse()
        if not parse_result.program:
            return ProcessResult(
                error=True,
                error_message=parse_result.error_message,
                error_box=parse_result.error_box
            )

        exec_result = Executor(parse_result.python_code).execute_in_sandbox()
        if exec_result.error_message:
            return ProcessResult(error=True, error_message=exec_result.error_message)

        return ProcessResult(
            image=warped_image,
            boxes=boxes,
            python_code=parse_result.python_code,
            code_output=exec_result.code_output,
            error_box=parse_result.error_box
        )

    def show_settings(self):
        """Display settings menu"""
        show_settings_menu(
            camera_preview=self.preview_thread,
            voice_thread=self.voice_thread,
            gesture_thread=self.gesture_thread
        )
        load_settings()

    def cleanup(self):
        """Clean up all resources"""
        print("Shutting down system...")
        
        # Stop threads in reverse order of initialization
        if self.gesture_thread:
            self.gesture_thread.stop()
            self.gesture_thread.join()
            
        if self.voice_thread:
            self.voice_thread.stop()
            self.voice_thread.join()
            
        if self.preview_thread:
            self.preview_thread.stop()
            self.preview_thread.join()
            
        if self.camera_manager:
            self.camera_manager.stop()
            
        cv2.destroyAllWindows()
        print("System shutdown complete")

class ProcessResult:
    """Simple container for processing results"""
    def __init__(self, error=False, **kwargs):
        self.error = error
        self.__dict__.update(kwargs)

def show_settings_menu(**kwargs):
    """Wrapper for settings menu"""
    root = tk.Tk()
    SettingsMenu(root, **kwargs)
    root.mainloop()
    load_settings()

if __name__ == "__main__":
    system = WhiteboardSystem()
    system.initialize_system()
    system.run()
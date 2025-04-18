import cv2
import numpy as np
from input.camera import Camera
from preprocessing.preprocessor import Preprocessor
from code_detection.detector import Detector
from code_detection.tokeniser import Tokeniser
from code_detection.parser import Parser
from execution.executor import Executor
from output.projector import Projector

class Controller:
    def __init__(self, camera=None, preprocessor=None, detector=None, tokeniser=None, 
                 parser=None, executor=None, projector=None, debug_mode=False):
        self.camera = camera or Camera(debug_mode=debug_mode)
        self.preprocessor = preprocessor or Preprocessor(None)
        self.detector = detector or Detector(None)
        self.tokeniser = tokeniser or Tokeniser(None)
        self.parser = parser or Parser(None)
        self.executor = executor or Executor(None)
        self.projector = projector or Projector(None, "...", "...", None, None, debug_mode=debug_mode)
        self.debug_mode = debug_mode
        self.running = False
        self.current_frame = None
        self.last_result = None
        
        # Create output window
        cv2.namedWindow('Output', cv2.WINDOW_NORMAL)
        cv2.setWindowProperty('Output', cv2.WND_PROP_FULLSCREEN, cv2.WINDOW_FULLSCREEN)
        
        # Show initial minimal projection
        self.show_minimal_projection()

    def __del__(self):
        self.stop()
        cv2.destroyAllWindows()

    def start(self):
        """Start the continuous processing loop"""
        self.running = True
        while self.running:
            # First show minimal projection
            self.show_minimal_projection()
            
            # Process one frame
            self.process_frame()
            
            # Then show full projection if we have results
            if self.last_result and len(self.last_result) == 5:
                image, python_code, code_output, boxes, error_box = self.last_result
                # Ensure python_code and code_output are never None
                safe_python_code = "..." if python_code is None else python_code
                safe_code_output = "..." if code_output is None else code_output
                self.show_full_projection(image, safe_python_code, safe_code_output, boxes, error_box)
            
            # Check for quit key (ESC)
            if cv2.waitKey(1) == 27:
                self.stop()
                break

    def stop(self):
        """Stop the processing loop"""
        self.running = False

    def show_minimal_projection(self):
        """Display just the camera view with minimal UI"""
        projection = self.projector.display_minimal_projection()
        if projection is not None:
            cv2.imshow("Output", projection)

    def show_full_projection(self, image, python_code, code_output, boxes, error_box=None):
        """Display the full processed results"""
        # Ensure values are safe for projector (should already be handled before calling)
        safe_python_code = "..." if python_code is None else python_code
        safe_code_output = "..." if code_output is None else code_output
        
        self.projector.update(
            image=image,
            python_code=safe_python_code,
            code_output=safe_code_output,
            boxes=boxes,
            error_box=error_box
        )
        projection = self.projector.display_full_projection()
        if projection is not None:
            cv2.imshow("Output", projection)

    def process_frame(self):
        """Process a single frame through the pipeline"""
        try:
            # Show minimal projection while capturing
            self.show_minimal_projection()
            
            # Capture frame
            image = self.camera.capture_frame()
            if image is None:
                self.last_result = (None, "...", "Error: Unable to capture frame", None, None)
                return

            # Keep showing minimal projection during processing
            self.show_minimal_projection()
            
            # Preprocess
            self.preprocessor.image = image
            processed_image = self.preprocessor.preprocess_image()
            if processed_image is None:
                self.last_result = (image, "...", "Error: Preprocessing failed", None, None)
                return

            # Detect code
            self.detector.image = processed_image
            detected_image, boxes = self.detector.detect_code()
            if detected_image is None or boxes is None:
                self.last_result = (processed_image, "...", "Error: Code detection failed", None, None)
                return

            # Tokenize
            self.tokeniser.boxes = boxes
            tokens = self.tokeniser.tokenise()
            if tokens is None:
                self.last_result = (detected_image, "...", "Error: Tokenisation failed", boxes, None)
                return

            # Parse
            self.parser.tokens = tokens
            program, python_code, error_message, error_box = self.parser.parse()
            if program is None or python_code is None:
                safe_python_code = "..." if python_code is None else python_code
                self.last_result = (detected_image, safe_python_code, error_message, boxes, error_box)
                return

            # Execute
            self.executor.python_code = python_code
            code_output, exec_error = self.executor.execute()
            
            # Store results for full projection (5 elements)
            safe_python_code = "..." if python_code is None else python_code
            safe_code_output = "..." if (code_output is None and exec_error is None) else (exec_error if exec_error else code_output)
            
            self.last_result = (
                detected_image,                   # image
                safe_python_code,                 # python_code (never None)
                safe_code_output,                 # code_output (never None)
                boxes,                           # boxes
                error_box                        # error_box
            )

        except Exception as e:
            self.last_result = (None, "...", f"System error: {str(e)}", None, None)

    def compile_code(self):
        """Compile the current code (placeholder)"""
        pass

    def run_code(self):
        """Run the processing pipeline once"""
        self.process_frame()
        if self.last_result and len(self.last_result) == 5:
            image, python_code, code_output, boxes, error_box = self.last_result
            safe_python_code = "..." if python_code is None else python_code
            safe_code_output = "..." if code_output is None else code_output
            self.show_full_projection(image, safe_python_code, safe_code_output, boxes, error_box)
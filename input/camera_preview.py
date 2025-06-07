import cv2
import threading
import time


class CameraPreviewThread(threading.Thread):
    def __init__(
        self, source=0, resolution=(3840, 2160), fps=10, window_name="Camera Feed"
    ):
        super().__init__()
        self.source = source
        self.resolution = resolution
        self.fps = fps
        self.window_name = window_name

        self._lock = threading.Lock()
        self._frame = None
        self._running = threading.Event()
        self._running.set()
        self._update_settings_event = threading.Event()
        self._settings_lock = threading.Lock()

        self.capture = None
        self._init_camera()

    def _init_camera(self):
        """Initialize the camera with the current settings."""
        if self.capture is not None:
            self.capture.release()

        self.capture = cv2.VideoCapture(self.source, cv2.CAP_DSHOW)
        
        # Set basic properties
        self.capture.set(cv2.CAP_PROP_FRAME_WIDTH, self.resolution[0])
        self.capture.set(cv2.CAP_PROP_FRAME_HEIGHT, self.resolution[1])
        self.capture.set(cv2.CAP_PROP_FPS, self.fps)
        
        # Try to set the requested camera settings
        try:
            # Note: ISO setting might not work on all cameras
            self.capture.set(cv2.CAP_PROP_ISO_SPEED, 80)  # Not universally supported
            
            # Exposure time (1/250 sec). Value is camera-specific, often in fractions
            # For many cameras, exposure is set as 1/value (so 1/250 would be 250)
            self.capture.set(cv2.CAP_PROP_EXPOSURE, 250)
            
            # White balance temperature (4300K)
            self.capture.set(cv2.CAP_PROP_WB_TEMPERATURE, 4300)
            
            # For EV compensation (-2.5 EV), we might need to adjust exposure
            # This is a workaround as OpenCV doesn't have direct EV control
            current_exposure = self.capture.get(cv2.CAP_PROP_EXPOSURE)
            if current_exposure > 0:
                self.capture.set(cv2.CAP_PROP_EXPOSURE, current_exposure * (2 ** -2.5))
            
            # Enable auto exposure off for manual control (if supported)
            self.capture.set(cv2.CAP_PROP_AUTO_EXPOSURE, 0.25)  # 0.25 means manual mode
            
            # Enable manual white balance mode (if supported)
            self.capture.set(cv2.CAP_PROP_AUTO_WB, 0)
        except Exception as e:
            print(f"Warning: Could not set all camera settings: {e}")

        time.sleep(0.5)

    def update_settings(self, source, resolution, fps):
        """Update the camera settings and reinitialize the camera."""
        with self._settings_lock:
            self.source = source
            self.resolution = resolution
            self.fps = fps
            self._update_settings_event.set()

    def run(self):
        """Thread run method to capture frames from the camera."""
        while self._running.is_set():
            if self._update_settings_event.is_set():
                with self._settings_lock:
                    self._init_camera()
                    self._update_settings_event.clear()

            ret, frame = self.capture.read()
            if not ret:
                print("Warning: Frame capture failed.")
                continue

            with self._lock:
                self._frame = frame.copy()

        self.capture.release()

    def get_frame(self):
        with self._lock:
            return self._frame.copy() if self._frame is not None else None

    def stop(self):
        self._running.clear()
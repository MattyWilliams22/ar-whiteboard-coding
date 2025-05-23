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
        if self.capture is not None:
            self.capture.release()

        self.capture = cv2.VideoCapture(self.source, cv2.CAP_DSHOW)
        self.capture.set(cv2.CAP_PROP_FRAME_WIDTH, self.resolution[0])
        self.capture.set(cv2.CAP_PROP_FRAME_HEIGHT, self.resolution[1])
        self.capture.set(cv2.CAP_PROP_FPS, self.fps)
        time.sleep(0.5)

    def update_settings(self, source, resolution, fps):
        with self._settings_lock:
            self.source = source
            self.resolution = resolution
            self.fps = fps
            self._update_settings_event.set()

    def run(self):
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

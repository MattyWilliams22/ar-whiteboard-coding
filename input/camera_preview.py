import cv2
import threading
import time

class CameraPreviewThread(threading.Thread):
    def __init__(self, source=0, resolution=(3840, 2160), fps=10, window_name="Camera Feed"):
        super().__init__()
        self.capture = cv2.VideoCapture(source, cv2.CAP_DSHOW)
        self.capture.set(cv2.CAP_PROP_FRAME_WIDTH, resolution[0])
        self.capture.set(cv2.CAP_PROP_FRAME_HEIGHT, resolution[1])
        self.capture.set(cv2.CAP_PROP_FPS, fps)
        time.sleep(0.5)  # Let camera warm up

        self.window_name = window_name
        self.running = self.capture.isOpened()
        self._frame = None
        self._lock = threading.Lock()

    def run(self):
        while self.running:
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
        self.running = False

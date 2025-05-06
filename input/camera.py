import cv2
import threading
import time
from settings import settings


class CameraManager:
    def __init__(self, camera_index=0, resolution=(1920, 1080), fps=10):
        self.cap = cv2.VideoCapture(camera_index)
        self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, resolution[0])
        self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, resolution[1])
        self.cap.set(cv2.CAP_PROP_FPS, fps)
        self.lock = threading.Lock()
        self.current_frame = None

    def update_settings(self):
        """Reinitialize camera with new settings"""
        self.cap.release()
        self.cap = cv2.VideoCapture(settings["CAMERA"])
        self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, settings["CAMERA_RESOLUTION"][0])
        self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, settings["CAMERA_RESOLUTION"][1])
        self.cap.set(cv2.CAP_PROP_FPS, settings["CAMERA_FPS"])

    def get_frame(self):
        with self.lock:
            return self.current_frame.copy() if self.current_frame is not None else None

    def run(self):
        while True:
            ret, frame = self.cap.read()
            if ret:
                with self.lock:
                    self.current_frame = frame
            # Sleep relative to fps
            time.sleep(1 / settings["CAMERA_FPS"])

import cv2
import threading
from typing import Optional
import time


class CameraPreviewThread(threading.Thread):
    def __init__(self, camera_manager, window_name: str = "Camera Feed"):
        """
        Thread for displaying camera preview using shared CameraManager

        Args:
            camera_manager: Shared camera manager instance
            window_name: Name of the preview window
        """
        super().__init__()
        self.camera_manager = camera_manager
        self.window_name = window_name

        self._running = threading.Event()
        self._running.set()
        self._frame_lock = threading.Lock()
        self._current_frame = None

        # Create window in main thread to avoid OpenCV issues
        cv2.namedWindow(self.window_name, cv2.WINDOW_NORMAL)
        cv2.resizeWindow(self.window_name, 1280, 720)

    def run(self):
        """Main preview loop"""
        print(f"Camera preview thread started for {self.window_name}")

        while self._running.is_set():
            try:
                # Get frame from shared camera manager
                frame = self.camera_manager.get_frame()
                if frame is None:
                    time.sleep(0.01)
                    continue

                # Store frame for external access
                with self._frame_lock:
                    self._current_frame = frame.copy()

                # Display the frame
                cv2.imshow(self.window_name, frame)
                cv2.waitKey(1)

            except Exception as e:
                print(f"Preview error: {e}")
                time.sleep(0.1)

    def get_frame(self) -> Optional[cv2.Mat]:
        """Get the current preview frame"""
        with self._frame_lock:
            return (
                self._current_frame.copy() if self._current_frame is not None else None
            )

    def stop(self):
        """Cleanly stop the preview thread"""
        self._running.clear()
        cv2.destroyWindow(self.window_name)
        print("Camera preview thread stopped")

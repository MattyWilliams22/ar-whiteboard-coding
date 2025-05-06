import cv2
import mediapipe as mp
import threading
from fsm.states import Event
import time
import numpy as np


class HandGestureThread(threading.Thread):
    def __init__(self, fsm, settings, detection_confidence=0.7, cooldown=0.5):
        super().__init__()
        self.fsm = fsm
        self.settings = settings
        self.detection_confidence = detection_confidence

        self._running = threading.Event()
        self._running.set()

        # MediaPipe setup
        self.mp_hands = mp.solutions.hands
        self.mp_drawing = mp.solutions.drawing_utils
        self.hands = self.mp_hands.Hands(
            max_num_hands=1,
            min_detection_confidence=self.detection_confidence,
            min_tracking_confidence=0.5,
        )

        # Gesture mapping (add your own gestures)
        self.gesture_map = {
            "fist": Event.CLEAR,
            "thumbs_up": Event.START_RUN,
            "peace": Event.EXIT,
            "open_palm": None,  # Can be used for activation
            "pointing": None,  # For navigation
        }

        # Camera setup
        self.cap = None
        self._initialize_camera()

        # State variables
        self.last_gesture_time = time.time()
        self.active_gesture = None
        self.cooldown = cooldown
        self.last_event_time = 0
        self.gesture_active = True

    def _initialize_camera(self):
        """Initialize or reinitialize camera with current settings"""
        if self.cap is not None:
            self.cap.release()

        try:
            self.cap = cv2.VideoCapture(self.settings["CAMERA"])
            self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, 1280)
            self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 720)
            print(f"Initialized camera: {self.settings['CAMERA']}")
        except Exception as e:
            print(f"Failed to initialize camera: {e}")
            raise

    def _recognize_gesture(self, hand_landmarks):
        """Convert hand landmarks to gesture classification"""
        # Get landmark coordinates
        landmarks = []
        for lm in hand_landmarks.landmark:
            landmarks.append([lm.x, lm.y, lm.z])
        landmarks = np.array(landmarks)

        # Thumb detection (for thumbs up)
        thumb_tip = landmarks[4]
        thumb_ip = landmarks[3]
        thumb_mcp = landmarks[2]

        # Index finger
        index_tip = landmarks[8]
        index_dip = landmarks[7]
        index_pip = landmarks[6]
        index_mcp = landmarks[5]

        # Middle finger
        middle_tip = landmarks[12]

        # Check for thumbs up
        if (
            thumb_tip[1] < thumb_ip[1] < thumb_mcp[1]  # Thumb is extended up
            and index_tip[1] > index_pip[1]  # Other fingers closed
            and middle_tip[1] > landmarks[11][1]
        ):
            return "thumbs_up"

        # Check for fist (all fingers closed)
        if all(
            lm[1] > landmarks[i * 4 + 3][1]
            for i, lm in enumerate(
                [landmarks[8], landmarks[12], landmarks[16], landmarks[20]]
            )
        ):
            return "fist"

        # Check for peace sign (index and middle extended, others closed)
        if (
            index_tip[1] < index_pip[1]
            and middle_tip[1] < landmarks[11][1]
            and landmarks[16][1] > landmarks[13][1]
            and landmarks[20][1] > landmarks[17][1]
        ):
            return "peace"

        # Check for open palm (all fingers extended)
        if all(
            lm[1] < landmarks[i * 4 + 3][1]
            for i, lm in enumerate(
                [landmarks[8], landmarks[12], landmarks[16], landmarks[20]]
            )
        ):
            return "open_palm"

        return None

    def _process_gesture(self, gesture):
        """Map gesture to FSM event"""
        if gesture in self.gesture_map:
            return self.gesture_map[gesture]
        return None

    def update_settings(self):
        """Reinitialize with new settings"""
        self._initialize_camera()

    def run(self):
        print("Hand gesture thread started - continuous detection mode")
        while self._running.is_set():
            try:
                success, frame = self.cap.read()
                if not success:
                    time.sleep(0.1)
                    continue

                frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                results = self.hands.process(frame_rgb)

                current_time = time.time()

                # Only process new gestures if cooldown has passed
                if results.multi_hand_landmarks and (
                    current_time - self.last_event_time > self.cooldown
                ):
                    for hand_landmarks in results.multi_hand_landmarks:
                        gesture = self._recognize_gesture(hand_landmarks)
                        if gesture and gesture in self.gesture_map:
                            event = self._process_gesture(gesture)
                            if event:
                                print(f"Executing gesture: {gesture}")
                                self.fsm.transition(event)
                                self.last_event_time = current_time

                # Optional: Visual feedback
                if settings["DEBUG_MODE"]:
                    self._display_feedback(frame, results)

            except Exception as e:
                print(f"Gesture error: {e}")
                time.sleep(0.1)

    def _display_feedback(self, frame, results):
        """Visual feedback (for debugging)"""
        if results.multi_hand_landmarks:
            for hand_landmarks in results.multi_hand_landmarks:
                self.mp_drawing.draw_landmarks(
                    frame, hand_landmarks, self.mp_hands.HAND_CONNECTIONS
                )

        status = "Active" if self.gesture_active else "Inactive"
        cv2.putText(
            frame,
            f"Gesture Control: {status}",
            (10, 30),
            cv2.FONT_HERSHEY_SIMPLEX,
            1,
            (0, 255, 0),
            2,
        )

        if self.active_gesture:
            cv2.putText(
                frame,
                f"Current: {self.active_gesture}",
                (10, 70),
                cv2.FONT_HERSHEY_SIMPLEX,
                1,
                (0, 255, 255),
                2,
            )

        cv2.imshow("Gesture Control", frame)
        cv2.waitKey(1)

    def stop(self):
        self._running.clear()
        if self.cap is not None:
            self.cap.release()
        if self.hands is not None:
            self.hands.close()
        cv2.destroyAllWindows()

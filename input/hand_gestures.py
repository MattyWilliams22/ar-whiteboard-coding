import cv2
import mediapipe as mp
import threading
from fsm.states import Event
import time
import numpy as np


class HandGestureThread(threading.Thread):
    def __init__(self, fsm, camera_manager, settings, detection_confidence=0.7, cooldown=0.5):
        super().__init__()
        self.fsm = fsm
        self.camera_manager = camera_manager
        self.settings = settings
        self.detection_confidence = detection_confidence
        self.cooldown = cooldown

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

        # Gesture mapping
        self.gesture_map = {
            "fist": Event.CLEAR,
            "thumbs_up": Event.START_RUN,
            "peace": Event.EXIT,
            "open_palm": None,
            "pointing": None,
        }

        # State variables
        self.last_event_time = 0
        self.active_gesture = None
        self.gesture_active = True

    def _recognize_gesture(self, hand_landmarks):
        """Convert hand landmarks to gesture classification"""
        landmarks = []
        for lm in hand_landmarks.landmark:
            landmarks.append([lm.x, lm.y, lm.z])
        landmarks = np.array(landmarks)

        # Thumb detection
        thumb_tip = landmarks[4]
        thumb_ip = landmarks[3]
        thumb_mcp = landmarks[2]

        # Finger landmarks
        index_tip = landmarks[8]
        index_pip = landmarks[6]
        middle_tip = landmarks[12]

        # Thumbs up gesture
        if (thumb_tip[1] < thumb_ip[1] < thumb_mcp[1] and  # Thumb extended up
            index_tip[1] > index_pip[1] and  # Other fingers closed
            middle_tip[1] > landmarks[11][1]):
            return "thumbs_up"

        # Fist gesture
        if all(lm[1] > landmarks[i*4 + 3][1] 
               for i, lm in enumerate([landmarks[8], landmarks[12], landmarks[16], landmarks[20]])):
            return "fist"

        # Peace gesture
        if (index_tip[1] < index_pip[1] and 
            middle_tip[1] < landmarks[11][1] and
            landmarks[16][1] > landmarks[13][1] and
            landmarks[20][1] > landmarks[17][1]):
            return "peace"

        # Open palm gesture
        if all(lm[1] < landmarks[i*4 + 3][1] 
               for i, lm in enumerate([landmarks[8], landmarks[12], landmarks[16], landmarks[20]])):
            return "open_palm"

        return None

    def _process_gesture(self, gesture):
        """Map gesture to FSM event"""
        return self.gesture_map.get(gesture)

    def run(self):
        print("Hand gesture thread started - using CameraManager")
        while self._running.is_set():
            try:
                frame = self.camera_manager.get_frame()
                if frame is None:
                    time.sleep(0.1)
                    continue

                frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                results = self.hands.process(frame_rgb)
                current_time = time.time()

                # Process gestures if cooldown has passed
                if results.multi_hand_landmarks and (current_time - self.last_event_time > self.cooldown):
                    for hand_landmarks in results.multi_hand_landmarks:
                        gesture = self._recognize_gesture(hand_landmarks)
                        if gesture and gesture in self.gesture_map:
                            event = self._process_gesture(gesture)
                            if event:
                                print(f"Executing gesture: {gesture}")
                                self.fsm.transition(event)
                                self.last_event_time = current_time

                # Debug visualization
                if self.settings.get("DEBUG_MODE", False):
                    self._display_feedback(frame, results)

            except Exception as e:
                print(f"Gesture processing error: {e}")
                time.sleep(0.1)

    def _display_feedback(self, frame, results):
        """Visual feedback for debugging"""
        if results.multi_hand_landmarks:
            for hand_landmarks in results.multi_hand_landmarks:
                self.mp_drawing.draw_landmarks(
                    frame, hand_landmarks, self.mp_hands.HAND_CONNECTIONS)

        status = "Active" if self.gesture_active else "Inactive"
        cv2.putText(frame, f"Gesture Control: {status}", (10, 30),
                    cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
        
        if self.active_gesture:
            cv2.putText(frame, f"Current: {self.active_gesture}", (10, 70),
                        cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 255), 2)
        
        cv2.imshow('Gesture Control', frame)
        cv2.waitKey(1)

    def stop(self):
        self._running.clear()
        self.hands.close()
        cv2.destroyAllWindows()
import os
os.environ["PROTOCOL_BUFFERS_PYTHON_IMPLEMENTATION"] = "python"

import cv2
import numpy as np
import time
import mediapipe as mp

class HandGestureTester:
    def __init__(self):
        self.mp_hands = mp.solutions.hands
        self.hands = self.mp_hands.Hands(
            static_image_mode=False,
            max_num_hands=1,
            min_detection_confidence=0.7,
            min_tracking_confidence=0.5
        )
        self.mp_drawing = mp.solutions.drawing_utils
        
        self.gesture_emojis = {
            "fist": "✊",
            "peace": "✌️",
            "open_palm": "🖐️"
        }

        # Gesture tracking
        self.current_gesture = None
        self.gesture_start_time = 0
        self.last_gesture_landmarks = None
        self.detection_count = 0
        self.cooldown_end_time = 0
        self.COOLDOWN_DURATION = 3.0  # seconds
        self.last_detected_gesture = None

        # Thresholds
        self.MIN_HOLD_TIME = 2.0  # seconds
        self.MIN_HAND_SIZE = 0.2   # relative to frame size
        self.MAX_MOVEMENT = 0.1    # max allowed movement

    def recognize_gesture(self, hand_landmarks):
        landmarks = hand_landmarks.landmark
        tip_y = [landmarks[i].y for i in [4, 8, 12, 16, 20]]  # Thumb to pinky tips
        pip_y = [landmarks[i].y for i in [2, 6, 10, 14, 18]]  # PIP joints
        
        extended = [tip < pip for tip, pip in zip(tip_y, pip_y)]
        
        if all(extended[1:]):  # Open palm
            return "open_palm", self.MIN_HAND_SIZE  # Default size threshold
        elif extended[1:] == [True, True, False, False]:  # Peace sign
            return "peace", self.MIN_HAND_SIZE
        elif not any(extended[1:]):  # Fist
            return "fist", self.MIN_HAND_SIZE * 0.5  # 50% smaller threshold
        return None, None

    def get_hand_size(self, landmarks):
        """Calculate hand size based on wrist to middle finger tip distance"""
        wrist = np.array([landmarks[0].x, landmarks[0].y])
        middle_tip = np.array([landmarks[12].x, landmarks[12].y])
        return np.linalg.norm(wrist - middle_tip)

    def get_hand_movement(self, current_landmarks):
        """Calculate movement from previous position (normalized 0-1)"""
        if self.last_gesture_landmarks is None:
            return 0
        
        prev_pos = np.array([self.last_gesture_landmarks[0].x, self.last_gesture_landmarks[0].y])
        current_pos = np.array([current_landmarks[0].x, current_landmarks[0].y])
        return np.linalg.norm(current_pos - prev_pos)

    def run_test(self):
        cap = cv2.VideoCapture(0)
        if not cap.isOpened():
            print("❌ Error: Could not access camera")
            return

        print("\n🎮 Deliberate Gesture Detection")
        print("============================")
        print("Hold a gesture steady for 2 seconds:")
        for name, emoji in self.gesture_emojis.items():
            print(f"{emoji} {name}")
        print("\nPress 'Q' to quit\n")

        while True:
            ret, frame = cap.read()
            if not ret:
                print("⚠️ Frame capture error")
                time.sleep(0.1)
                continue

            frame = cv2.flip(frame, 1)
            frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            results = self.hands.process(frame_rgb)

            current_time = time.time()
            in_cooldown = current_time < self.cooldown_end_time
            
            display_text = "Show hand gesture..."
            display_color = (0, 0, 255)  # Red
            gesture_detected = False

            if results.multi_hand_landmarks and not in_cooldown:
                for hand_landmarks in results.multi_hand_landmarks:
                    self.mp_drawing.draw_landmarks(
                        frame, hand_landmarks, self.mp_hands.HAND_CONNECTIONS)

                    # Recognize gesture and get its size threshold
                    new_gesture, gesture_size_threshold = self.recognize_gesture(hand_landmarks)
                    
                    # Skip if no gesture detected
                    if new_gesture is None:
                        continue

                    # Check hand size with gesture-specific threshold
                    hand_size = self.get_hand_size(hand_landmarks.landmark)
                    if hand_size < gesture_size_threshold:
                        display_text = f"Move {new_gesture} closer"
                        continue

                    # Check for movement
                    movement = self.get_hand_movement(hand_landmarks.landmark)
                    if movement > self.MAX_MOVEMENT:
                        self.current_gesture = None
                        display_text = "Hold still"
                        continue

                    # Recognize gesture
                    new_gesture, gesture_size_threshold = self.recognize_gesture(hand_landmarks)
                    
                    # Gesture stability check
                    if new_gesture != self.current_gesture:
                        self.current_gesture = new_gesture
                        self.gesture_start_time = current_time
                    else:
                        hold_time = current_time - self.gesture_start_time
                        if hold_time >= self.MIN_HOLD_TIME:
                            display_text = f"{new_gesture} {self.gesture_emojis[new_gesture]}"
                            display_color = (0, 255, 0)  # Green
                            if not gesture_detected:
                                self.detection_count += 1
                                print(f"✅ [{self.detection_count}] Confirmed: {new_gesture} "
                                      f"(held for {hold_time:.1f}s) {self.gesture_emojis[new_gesture]}")
                                self.last_detected_gesture = new_gesture
                                self.cooldown_end_time = current_time + self.COOLDOWN_DURATION
                                gesture_detected = True
                        else:
                            display_text = f"Hold {new_gesture}... {hold_time:.1f}s/{self.MIN_HOLD_TIME}s"
                            display_color = (0, 255, 255)  # Yellow

                    self.last_gesture_landmarks = hand_landmarks.landmark

            if in_cooldown:
                remaining = self.cooldown_end_time - current_time
                display_text = f"Ready in {remaining:.1f}s"
                display_color = (200, 200, 200)  # Gray

            # Display UI
            cv2.putText(frame, "Deliberate Gesture Test", (10, 30),
                       cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 200, 255), 2)
            cv2.putText(frame, display_text, (10, 70),
                       cv2.FONT_HERSHEY_SIMPLEX, 1, display_color, 2)
            
            cv2.imshow('Gesture Test', frame)
            
            if cv2.waitKey(1) & 0xFF == ord('q'):
                break

        cap.release()
        cv2.destroyAllWindows()
        self.hands.close()
        print("\n✅ Test completed successfully")

if __name__ == "__main__":
    print("🚀 Starting gesture detection test...")
    tester = HandGestureTester()
    tester.run_test()
import cv2
import numpy as np
import os
import sys
import time

# Force protobuf compatibility before importing mediapipe
os.environ["PROTOCOL_BUFFERS_PYTHON_IMPLEMENTATION"] = "python"
try:
    import google.protobuf
    google.protobuf.__version__ = "3.20.3"  # Force version
except ImportError:
    pass

import mediapipe as mp

class HandGestureTester:
    def __init__(self):
        """Initialize with guaranteed working configuration"""
        # MediaPipe Hands configuration
        self.mp_hands = mp.solutions.hands
        self.hands = self.mp_hands.Hands(
            static_image_mode=False,
            max_num_hands=1,
            min_detection_confidence=0.7,
            min_tracking_confidence=0.5
        )
        self.mp_drawing = mp.solutions.drawing_utils
        
        # Gesture definitions with emojis
        self.gesture_emojis = {
            "fist": "✊",
            "thumbs_up": "👍", 
            "peace": "✌️",
            "open_palm": "🖐️",
            "pointing": "👉"
        }

    def recognize_gesture(self, hand_landmarks):
        """Simplified and robust gesture recognition"""
        # Get key landmark positions
        landmarks = hand_landmarks.landmark
        tip_y = [landmarks[i].y for i in [4, 8, 12, 16, 20]]  # Thumb to pinky tips
        pip_y = [landmarks[i].y for i in [2, 6, 10, 14, 18]]  # Corresponding PIP joints
        
        # Determine extended fingers (tip above PIP joint)
        extended = [tip < pip for tip, pip in zip(tip_y, pip_y)]
        
        # Gesture patterns
        if extended == [True, False, False, False, False]:  # Only thumb
            return "thumbs_up"
        elif extended == [False, True, True, False, False]:  # Index + middle
            return "peace"
        elif extended == [False, True, False, False, False]:  # Only index
            return "pointing"
        elif all(extended):  # All fingers
            return "open_palm"
        elif not any(extended):  # No fingers
            return "fist"
        return None

    def run_test(self):
        """Main test routine with bulletproof error handling"""
        cap = cv2.VideoCapture(0)
        if not cap.isOpened():
            print("❌ Error: Could not access camera")
            return

        print("\n🎮 Gesture Detection Test")
        print("======================")
        print("Show these gestures to the camera:")
        for name, emoji in self.gesture_emojis.items():
            print(f"{emoji} {name}")
        print("\nPress 'Q' to quit\n")

        last_gesture = None
        detection_count = 0

        try:
            while True:
                ret, frame = cap.read()
                if not ret:
                    print("⚠️ Frame capture error")
                    time.sleep(0.1)
                    continue

                # Mirror the frame for more intuitive control
                frame = cv2.flip(frame, 1)
                
                # Convert to RGB and process
                frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                results = self.hands.process(frame_rgb)
                
                current_gesture = None
                if results.multi_hand_landmarks:
                    for hand_landmarks in results.multi_hand_landmarks:
                        # Draw hand landmarks
                        self.mp_drawing.draw_landmarks(
                            frame, hand_landmarks, self.mp_hands.HAND_CONNECTIONS)
                        
                        # Recognize gesture
                        current_gesture = self.recognize_gesture(hand_landmarks)
                        if current_gesture and current_gesture != last_gesture:
                            detection_count += 1
                            print(f"✅ [{detection_count}] Detected: {current_gesture} "
                                  f"{self.gesture_emojis[current_gesture]}")
                            last_gesture = current_gesture
                
                # Display UI
                cv2.putText(frame, "Gesture Test", (10, 30),
                           cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 200, 255), 2)
                if current_gesture:
                    cv2.putText(frame, f"{current_gesture} {self.gesture_emojis[current_gesture]}", 
                               (10, 70), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
                else:
                    cv2.putText(frame, "Show hand gesture...", (10, 70),
                               cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 2)
                
                cv2.imshow('Gesture Test', frame)
                
                if cv2.waitKey(1) & 0xFF == ord('q'):
                    break

        except Exception as e:
            print(f"❌ Unexpected error: {str(e)}")
        finally:
            cap.release()
            cv2.destroyAllWindows()
            self.hands.close()
            print("\n✅ Test completed successfully")

if __name__ == "__main__":
    print("🚀 Starting gesture detection test...")
    tester = HandGestureTester()
    tester.run_test()
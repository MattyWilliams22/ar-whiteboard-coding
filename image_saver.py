import os
import cv2

def capture_images(save_directory):
    if not os.path.exists(save_directory):
        os.makedirs(save_directory)

    cap = cv2.VideoCapture(0)
    if not cap.isOpened():
        print("Error: Could not open webcam.")
        return

    try:
        while True:
            distance = input("Enter distance (or type 'exit' to quit): ")
            if distance.lower() == 'exit':
                break

            angle = input("Enter angle: ")
            filename = f"image_{distance}m_{angle}deg.jpg"
            filepath = os.path.join(save_directory, filename)

            ret, frame = cap.read()
            if not ret:
                print("Error: Failed to capture image.")
                continue

            cv2.imwrite(filepath, frame)
            print(f"Image saved as {filename}")
    
    finally:
        cap.release()
        cv2.destroyAllWindows()

if __name__ == "__main__":
    save_directory = input("Enter directory to save images: ")
    capture_images(save_directory)
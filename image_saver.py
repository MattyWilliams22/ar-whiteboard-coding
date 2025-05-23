import os
import cv2


def capture_images(save_directory):
    if not os.path.exists(save_directory):
        os.makedirs(save_directory)

    cap = cv2.VideoCapture(0)
    if not cap.isOpened():
        print("Error: Could not open webcam.")
        return

    # Set the webcam to its full resolution (modify values based on your webcam's specs)
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, 1920)  # Adjust width
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 1080)  # Adjust height

    try:
        while True:
            distance = input("Enter main distance (or type 'exit' to quit): ")
            if distance.lower() == "exit":
                break

            offset = input("Enter offset distance: ")
            filename = f"image_{distance}m_offset_{offset}m.jpg"
            filepath = os.path.join(save_directory, filename)

            print("Press SPACE to capture the image, or 'q' to quit.")

            while True:
                ret, frame = cap.read()
                if not ret:
                    print("Error: Failed to capture frame.")
                    break

                # Show the webcam feed
                cv2.imshow("Webcam Preview", frame)

                key = cv2.waitKey(1) & 0xFF
                if key == ord(" "):  # Spacebar to capture
                    cv2.imwrite(filepath, frame)
                    print(f"Image saved as {filename}")
                    break
                elif key == ord("q"):  # 'q' to quit
                    return

    finally:
        cap.release()
        cv2.destroyAllWindows()


if __name__ == "__main__":
    save_directory = input("Enter directory to save images: ")
    capture_images(save_directory)

import cv2

capture = cv2.VideoCapture(1)  # Use 0 or 1 depending on your camera

# ✅ Set desired resolution (e.g., 1920x1080 for Full HD)
capture.set(cv2.CAP_PROP_FRAME_WIDTH, 3840)
capture.set(cv2.CAP_PROP_FRAME_HEIGHT, 2160)

window_name = "camera feed"
running = capture.isOpened()

cv2.namedWindow(window_name, cv2.WINDOW_NORMAL)

while running:
    ret, frame = capture.read()
    if not ret:
        print("Warning: Frame capture failed.")
        break

    cv2.imshow(window_name, frame)

    key = cv2.waitKey(1) & 0xFF
    if key == ord("q"):
        running = False

capture.release()
cv2.destroyWindow(window_name)

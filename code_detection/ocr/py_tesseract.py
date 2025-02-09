import cv2
import cv2.aruco as aruco
import numpy as np
import pytesseract

# Configure pytesseract (optional: specify the path if not in system variables)
# pytesseract.pytesseract.tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe"

# Function to detect handwritten text using pytesseract
def detect_pytesseract_text(image, aruco_mask):
    # Convert image to grayscale (Tesseract performs better on grayscale images)
    gray_image = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

    # Apply the ArUco mask: Set the regions with ArUco markers to black
    masked_image = cv2.bitwise_and(gray_image, gray_image, mask=~aruco_mask)

    # Perform OCR detection and recognition on the masked image
    custom_config = r'--oem 3 --psm 6'  # Optimize for block text detection
    detected_text = pytesseract.image_to_data(masked_image, config=custom_config, output_type=pytesseract.Output.DICT)

    # Draw bounding boxes and text on the image
    for i in range(len(detected_text["text"])):
        if int(detected_text["conf"][i]) > 0:  # Filter out low-confidence detections
            startX, startY = detected_text["left"][i], detected_text["top"][i]
            endX, endY = startX + detected_text["width"][i], startY + detected_text["height"][i]
            text = detected_text["text"][i]

            # Draw rectangle around detected text
            cv2.rectangle(image, (startX, startY), (endX, endY), (255, 0, 0), 2)

            # Put recognized text above the rectangle
            cv2.putText(image, text, (startX, startY - 10), 
                        cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 1, cv2.LINE_AA)

    return image, detected_text

def test_detection(image):
    gray_image = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    detected_text = pytesseract.image_to_string(gray_image)
    return detected_text
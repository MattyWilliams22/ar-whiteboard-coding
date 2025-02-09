import cv2
import cv2.aruco as aruco
import numpy as np
import easyocr

# Initialize EasyOCR reader
reader = easyocr.Reader(['en'])

# Function to detect handwritten text using EasyOCR
def detect_easyocr_text(image, aruco_mask):
    # Convert image to grayscale (optional, EasyOCR works with RGB too)
    gray_image = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

    # Apply the ArUco mask: Set the regions with ArUco markers to black
    masked_image = cv2.bitwise_and(gray_image, gray_image, mask=~aruco_mask)

    # Perform OCR detection and recognition on the masked image
    results = reader.readtext(masked_image)

    # Draw bounding boxes and text on the image
    for (bbox, text, prob) in results:
        (startX, startY), (_, _), (endX, endY), (_, _) = bbox  # Extract bounding box coordinates

        # Draw rectangle around detected text
        cv2.rectangle(image, (int(startX), int(startY)), (int(endX), int(endY)), (255, 0, 0), 2)

        # Put recognized text above the rectangle
        cv2.putText(image, f"{text}", (int(startX), int(startY) - 10), 
                    cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 1, cv2.LINE_AA)

    return image, results

def test_detection(image):
    results = reader.readtext(image)
    detected_text = ' '.join([result[1] for result in results])
    return detected_text
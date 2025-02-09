import cv2
import cv2.aruco as aruco
import numpy as np
import keras_ocr

# Initialize Keras-OCR pipeline
pipeline = keras_ocr.pipeline.Pipeline()

# Function to detect handwritten text using Keras-OCR
def detect_kerasocr_text(image, aruco_mask):
    # Convert image to RGB (Keras-OCR expects RGB format)
    rgb_image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)

    # Apply the ArUco mask: Set the regions with ArUco markers to black
    masked_image = cv2.bitwise_and(rgb_image, rgb_image, mask=~aruco_mask)

    # Convert OpenCV image to a format compatible with Keras-OCR
    keras_image = keras_ocr.tools.read(masked_image)

    # Perform OCR detection and recognition on the masked image
    predictions = pipeline.recognize([keras_image])[0]

    # Draw bounding boxes and text on the image
    for text, bbox in predictions:
        (startX, startY), (_, _), (endX, endY), (_, _) = bbox  # Extract bounding box coordinates

        # Draw rectangle around detected text
        cv2.rectangle(image, (int(startX), int(startY)), (int(endX), int(endY)), (255, 0, 0), 2)

        # Put recognized text above the rectangle
        cv2.putText(image, text, (int(startX), int(startY) - 10), 
                    cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 1, cv2.LINE_AA)

    return image, predictions

def test_detection(image):
    image_rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
    predictions = pipeline.recognize([image_rgb])[0]
    detected_text = ' '.join([text for text, _ in predictions])
    return detected_text
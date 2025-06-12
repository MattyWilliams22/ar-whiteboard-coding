import cv2
import cv2.aruco as aruco
import numpy as np
from paddleocr import PaddleOCR

# Initialise PaddleOCR (with angle classification disabled)
ocr = PaddleOCR(use_angle_cls=False, lang="en")


def detect_paddleocr_text(image, aruco_mask):
    # Convert image to RGB (PaddleOCR expects RGB format)
    rgb_image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)

    # Mean colour of the image
    mean_colour = np.mean(rgb_image, axis=(0, 1))

    # Create a background image filled with the mean colour
    background = np.full(rgb_image.shape, mean_colour, dtype=np.uint8)
    
    # Blend masked regions with the background (adjust alpha for transparency)
    blended_image = rgb_image.copy()
    blended_image[aruco_mask == 255] = (background[aruco_mask == 255]).astype(np.uint8)
    
    # Perform OCR on the blended image
    results = ocr.ocr(blended_image, cls=True)

    # # Draw bounding boxes and text on the image
    # for line in results[0]:
    #     box, text = line  # Unpack the bounding box and text (no confidence in this version)

    #     startX, startY = int(box[0][0]), int(box[0][1])
    #     endX, endY = int(box[2][0]), int(box[2][1])

    #     # Draw rectangle around detected text
    #     cv2.rectangle(image, (startX, startY), (endX, endY), (255, 0, 0), 2)

    #     # Put recognised text above the rectangle
    #     cv2.putText(image, f"{text}", (startX, startY - 10),
    #                 cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 1, cv2.LINE_AA)
        
    return image, results

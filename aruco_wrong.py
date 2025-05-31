import cv2
from code_detection.ocr.paddleocr import detect_paddleocr_text

image = cv2.imread("captured_images/warped_1.png")

image, results = detect_paddleocr_text(image, None)

cv2.imwrite("captured_images/output_image.jpg", image)
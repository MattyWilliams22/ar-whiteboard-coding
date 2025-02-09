import cv2
import cv2.aruco as aruco
import numpy as np
from transformers import TrOCRProcessor, VisionEncoderDecoderModel
from PIL import Image

# Initialize TrOCR processor and model
processor = TrOCRProcessor.from_pretrained("microsoft/trocr-base-handwritten")
model = VisionEncoderDecoderModel.from_pretrained("microsoft/trocr-base-handwritten")

# Function to detect handwritten text using TrOCR
def detect_trocr_text(image, aruco_mask):
    # Convert image to grayscale (optional, but can improve OCR accuracy)
    gray_image = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

    # Apply the ArUco mask: Set the regions with ArUco markers to black
    masked_image = cv2.bitwise_and(gray_image, gray_image, mask=~aruco_mask)

    # Convert OpenCV image (NumPy array) to PIL image (required for TrOCR)
    pil_image = Image.fromarray(masked_image)

    # Perform OCR detection using TrOCR
    pixel_values = processor(pil_image, return_tensors="pt").pixel_values
    generated_ids = model.generate(pixel_values)
    recognized_text = processor.batch_decode(generated_ids, skip_special_tokens=True)[0]

    # Draw the recognized text on the image
    cv2.putText(image, recognized_text, (10, 30),
                cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2, cv2.LINE_AA)

    return image, recognized_text

def test_detection(image):
    # Convert the input image to PIL format (TrOCR works with PIL images)
    pil_image = Image.fromarray(image)  # Assuming image is a NumPy array
    
    # Preprocess the image and convert it to tensor format
    pixel_values = processor(pil_image, return_tensors="pt").pixel_values
    
    # Generate text from the image using the model
    generated_ids = model.generate(pixel_values)
    
    # Decode the generated ids into text (skip special tokens)
    detected_text = processor.batch_decode(generated_ids, skip_special_tokens=True)[0]
    
    return detected_text
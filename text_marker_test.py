import os
import cv2
import numpy as np
from code_detection.ocr.paddleocr import detect_paddleocr_text

def main():
  # Ask user for file path
  file_path = input("Please enter the file path of the image: ").strip()
  
  # Verify file exists
  if not os.path.isfile(file_path):
    print("Error: The specified file does not exist.")
    return
  
  # Verify file is a JPG or JPEG
  if not (file_path.lower().endswith('.jpg') or file_path.lower().endswith('.jpeg')):
    print("Error: The specified file is not a JPG or JPEG image.")
    return
  
  try:
    # Read the image
    image = cv2.imread(file_path)
    
    if image is None:
      print("Error: Could not read the image.")
      return
    
    # Create a blank ArUco mask (since we're not using ArUco markers in this case)
    aruco_mask = np.zeros(image.shape[:2], dtype=np.uint8)
    
    # Process the image with text detection
    processed_image, results = detect_paddleocr_text(image, aruco_mask)
    
    # Draw bounding boxes and text on the image
    if results is not None and len(results) > 0 and results[0] is not None:
      for line in results[0]:
        if line:  # Check if line is not empty
          box, (text, confidence) = line  # Unpack the bounding box and text with confidence
          
          startX, startY = int(box[0][0]), int(box[0][1])
          endX, endY = int(box[2][0]), int(box[2][1])
          
          # Draw rectangle around detected text
          cv2.rectangle(processed_image, (startX, startY), (endX, endY), (255, 0, 0), 2)
          
          # Put recognized text above the rectangle
          cv2.putText(processed_image, f"{text} ({confidence:.2f})", (startX, startY - 10), 
                cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 1, cv2.LINE_AA)
          
          # Display the detection info in console
          print(f"Text: {text}")
          print(f"Confidence: {confidence:.2f}")
          print(f"Bounding Box: ({startX}, {startY}) to ({endX}, {endY})")
          print("-" * 40)
    else:
      print("No text detected in the image.")
    
    # Save the processed image (even if no text is detected)
    output_filename = f"processed_{os.path.basename(file_path)}"
    output_path = os.path.join(os.path.dirname(file_path), output_filename)
    cv2.imwrite(output_path, processed_image)
    print(f"Processed image saved as: {output_filename}\n")
    
  except Exception as e:
    print(f"Error processing the file: {str(e)}")
  
  print("Processing complete.")

if __name__ == "__main__":
  while True:
    main()

import cv2
import numpy as np
from code_detection.markers.aruco import detect_aruco_markers, create_aruco_mask, draw_aruco_keywords
from code_detection.ocr.paddleocr import detect_paddleocr_text
from code_detection.markers.keywords import get_keyword

class Detector:
  def __init__(self, image, aruco_dict_type=cv2.aruco.DICT_6X6_50):
    self.image = image
    self.aruco_dict_type = aruco_dict_type
    self.text = None
    self.corners = None
    self.ids = None
    self.boxes = None
    
  def combine_markers_and_text(self):
    self.boxes = []

    # Draw bounding boxes and text on the image
    if self.text[0] is not None:
      for line in self.text[0]:
        box, prediction = line  # Unpack the bounding box and text
        text, _ = prediction

        startX, startY = int(box[0][0]), int(box[0][1])
        endX, endY = int(box[2][0]), int(box[2][1])

        corners = np.array([[startX, startY], [endX, startY], [endX, endY], [startX, endY]])

        self.boxes.append((corners, text))

    for i in range(len(self.corners)):
      box = self.corners[i][0]

      corners = np.array([[box[0][0], box[0][1]], [box[1][0], box[1][1]], 
                      [box[2][0], box[2][1]], [box[3][0], box[3][1]]])
      
      text = get_keyword(self.ids[i][0])

      self.boxes.append((corners, text))

  def detect_code(self):
    if self.image is None:
      return None, None
    
    self.image, self.corners, self.ids = detect_aruco_markers(self.image, self.aruco_dict_type)

    if self.image is None:
      print("Error: Marker detection failed")
      return None, None

    mask = create_aruco_mask(self.image, self.corners)

    self.image, self.text = detect_paddleocr_text(self.image, mask)

    if self.image is None:
      print("Error: Text detection failed")
      return None, None

    self.combine_markers_and_text()

    return self.image, self.boxes
  
  def set_image(self, image):
    self.image = image
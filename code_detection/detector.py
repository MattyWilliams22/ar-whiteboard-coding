import cv2
import numpy as np
from code_detection.markers.aruco import detect_aruco_markers, create_aruco_mask, draw_aruco_keywords
from code_detection.ocr.paddleocr import detect_paddleocr_text
from code_detection.markers.keywords import get_keyword

class Detector:
  def __init__(self, image=None, aruco_dict_type=cv2.aruco.DICT_6X6_50):
    self.image = image
    self.aruco_dict_type = aruco_dict_type
    self.text = None
    self.corners = None
    self.ids = None
    self.boxes = None

  @staticmethod
  def compute_iou(box1, box2):
    poly1 = cv2.convexHull(box1.astype(np.float32))
    poly2 = cv2.convexHull(box2.astype(np.float32))

    intersection_area = cv2.intersectConvexConvex(poly1, poly2)[0]
    if intersection_area <= 0:
      return 0.0

    area1 = cv2.contourArea(poly1)
    area2 = cv2.contourArea(poly2)
    union_area = area1 + area2 - intersection_area

    return intersection_area / union_area if union_area > 0 else 0

  @staticmethod
  def is_contained(inner, outer):
    inner_poly = cv2.convexHull(inner.astype(np.float32))
    outer_poly = cv2.convexHull(outer.astype(np.float32))

    for point in inner_poly:
      if cv2.pointPolygonTest(outer_poly, tuple(point[0]), False) < 0:
        return False
    return True

  @classmethod
  def from_multiple_images(cls, images, aruco_dict_type=cv2.aruco.DICT_6X6_50, min_appearance_ratio=0.4):
    all_boxes = []

    for img in images:
      detector = cls(img, aruco_dict_type)
      detector.detect_code()

      for candidate_corners, candidate_text in detector.boxes:
        matched = False
        for existing in all_boxes:
          existing_corners, existing_text, existing_count = existing

          if (cls.is_contained(candidate_corners, existing_corners) or
              cls.is_contained(existing_corners, candidate_corners) or
              cls.compute_iou(candidate_corners, existing_corners) > 0.2):
            if "ARUCO" in candidate_text.upper():
              existing[0] = candidate_corners
              existing[1] = candidate_text
            existing[2] += 1
            matched = True
            break

        if not matched:
          all_boxes.append([candidate_corners, candidate_text, 1])

    threshold = max(1, int(min_appearance_ratio * len(images)))
    merged_boxes = [(corners, text) for corners, text, count in all_boxes if count >= threshold]
    instance = cls(images[0], aruco_dict_type)
    instance.boxes = merged_boxes
    return instance

  def combine_markers_and_text(self):
    self.boxes = []

    if self.text[0] is not None:
      for line in self.text[0]:
        box, prediction = line
        text, _ = prediction

        if text == "PYTHON":
          text = "PYTHON:"
        elif text == "OUTPUT":
          text = "OUTPUT:"

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

  def set_images(self, image):
    self.image = image
    self.text = None
    self.corners = None
    self.ids = None
    self.boxes = None
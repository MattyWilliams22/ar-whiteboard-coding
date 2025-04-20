import numpy as np
import cv2
from code_detection.markers.keywords import get_keyword

class Preprocessor:
  def __init__(self, image, aruco_dict_type=cv2.aruco.DICT_6X6_50):
    self.original_image = image
    self.aruco_dict_type = aruco_dict_type
    self.aruco_dict = cv2.aruco.getPredefinedDictionary(self.aruco_dict_type)
    self.aruco_params = cv2.aruco.DetectorParameters()
    
    self.warped_image = None
    self.aruco_image = None
    self.ocr_image = None

    self.corners = None
    self.ids = None

  def warp_image(self, image, margin=10):
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    corners, ids, _ = cv2.aruco.detectMarkers(gray, self.aruco_dict, parameters=self.aruco_params)

    if corners is None or ids is None or len(ids) < 4:
      return None, "Error: Not enough markers detected!"

    self.corners = corners
    self.ids = ids

    src_points = self.get_corner_markers() or self.get_outermost_markers()
    if src_points is None:
      return None, "Error: Could not compute source points!"

    h, w = image.shape[:2]
    dst_points = np.array([
      [margin, margin],
      [w - margin, margin],
      [w - margin, h - margin],
      [margin, h - margin]
    ], dtype=np.float32)

    H = cv2.getPerspectiveTransform(src_points, dst_points)
    warped = cv2.warpPerspective(image, H, (w + 2 * margin, h + 2 * margin))
    return warped, None

  def get_corner_markers(self):
    top_left, top_right, bottom_left, bottom_right = None, None, None, None
    for corner, id in zip(self.corners, self.ids):
      label = get_keyword(id[0])
      if label == "Top Left": top_left = corner[0][0]
      elif label == "Top Right": top_right = corner[0][0]
      elif label == "Bottom Left": bottom_left = corner[0][0]
      elif label == "Bottom Right": bottom_right = corner[0][0]
    if all([top_left, top_right, bottom_left, bottom_right]):
      return np.array([top_left, top_right, bottom_right, bottom_left], dtype=np.float32)
    return None

  def get_outermost_markers(self):
    if self.corners is None:
      return None
    points = np.concatenate(self.corners).reshape(-1, 2)
    top_left = min(points, key=lambda p: p[0] + p[1])
    top_right = max(points, key=lambda p: p[0] - p[1])
    bottom_right = max(points, key=lambda p: p[0] + p[1])
    bottom_left = min(points, key=lambda p: p[0] - p[1])
    return np.array([top_left, top_right, bottom_right, bottom_left], dtype=np.float32)

  def preprocess_for_aruco(self):
    if self.aruco_image is not None:
      return self.aruco_image

    if self.warped_image is None:
      self.warped_image, err = self.warp_image(self.original_image)
      if err:
        print(err)
        return None

    gray = cv2.cvtColor(self.warped_image, cv2.COLOR_BGR2GRAY)
    self.aruco_image = cv2.equalizeHist(gray)
    return self.aruco_image

  def preprocess_for_ocr(self):
    if self.ocr_image is not None:
      return self.ocr_image

    if self.warped_image is None:
      self.warped_image, err = self.warp_image(self.original_image)
      if err:
        print(err)
        return None

    gray = cv2.cvtColor(self.warped_image, cv2.COLOR_BGR2GRAY)
    blurred = cv2.GaussianBlur(gray, (5, 5), 0)
    thresh = cv2.adaptiveThreshold(
      blurred, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
      cv2.THRESH_BINARY, 11, 2
    )
    kernel = np.ones((2, 2), np.uint8)
    self.ocr_image = cv2.morphologyEx(thresh, cv2.MORPH_OPEN, kernel)
    return self.ocr_image
  
  def get_warped_image(self):
    return self.warped_image

  def set_image(self, image):
    self.original_image = image
    self.warped_image = None
    self.aruco_image = None
    self.ocr_image = None
    self.corners = None
    self.ids = None

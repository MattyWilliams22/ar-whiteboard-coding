import numpy as np
import cv2
from code_detection.markers.keywords import get_keyword

class Preprocessor:
    def __init__(self, image, aruco_dict_type=cv2.aruco.DICT_6X6_50):
      self.image = image
      self.aruco_dict_type = aruco_dict_type
      self.aruco_dict = cv2.aruco.getPredefinedDictionary(self.aruco_dict_type)
      self.aruco_params = cv2.aruco.DetectorParameters()
      self.preprocessed_image = None
      self.corners = None
      self.ids = None

    def get_markers(self):
      gray = cv2.cvtColor(self.image, cv2.COLOR_BGR2GRAY)
      corners, ids, _ = cv2.aruco.detectMarkers(gray, self.aruco_dict, parameters=self.aruco_params)
      self.corners = corners
      self.ids = ids

    def get_corner_markers(self):
      top_left, top_right, bottom_left, bottom_right = None, None, None, None
      for corner, id in zip(self.corners, self.ids):
        text = get_keyword(id[0])
        if text == "Top Left":
          top_left = corner[0][0]
        elif text == "Top Right":
          top_right = corner[0][0]
        elif text == "Bottom Left":
          bottom_left = corner[0][0]
        elif text == "Bottom Right":
          bottom_right = corner[0][0]
      if all(x is not None for x in [top_left, top_right, bottom_left, bottom_right]):
        return np.array([top_left, top_right, bottom_right, bottom_left], dtype=np.float32)
      return None

    def get_outermost_markers(self):
      all_points = np.concatenate(self.corners).reshape(-1, 2)
      top_left = min(all_points, key=lambda p: p[0] + p[1])
      top_right = max(all_points, key=lambda p: p[0] - p[1])
      bottom_right = max(all_points, key=lambda p: p[0] + p[1])
      bottom_left = min(all_points, key=lambda p: p[0] - p[1])
      return np.array([top_left, top_right, bottom_right, bottom_left], dtype=np.float32)

    def warp_image(self, margin=10):
      self.get_markers()
      if self.corners is None or self.ids is None:
        return "Error: No markers detected!"
      if len(self.ids) < 4:
        return "Error: Not enough markers detected! Need at least 4."

      src_points = self.get_corner_markers()
      if src_points is None:
        src_points = self.get_outermost_markers()

      dst_points = np.array([
        [margin, margin],
        [self.image.shape[1] - margin, margin],
        [self.image.shape[1] - margin, self.image.shape[0] - margin],
        [margin, self.image.shape[0] - margin],
      ], dtype=np.float32)

      homography_matrix = cv2.getPerspectiveTransform(src_points, dst_points)
      width, height = self.image.shape[1] + 2 * margin, self.image.shape[0] + 2 * margin
      self.preprocessed_image = cv2.warpPerspective(self.image, homography_matrix, (width, height))

      return None

    def to_grayscale(self):
      if self.preprocessed_image is not None:
        self.preprocessed_image = cv2.cvtColor(self.preprocessed_image, cv2.COLOR_BGR2GRAY)

    def gaussian_blur(self, ksize=5):
      if self.preprocessed_image is not None:
        self.preprocessed_image = cv2.GaussianBlur(self.preprocessed_image, (ksize, ksize), 0)

    def adaptive_threshold(self):
      if self.preprocessed_image is not None:
        self.preprocessed_image = cv2.adaptiveThreshold(
          self.preprocessed_image, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
          cv2.THRESH_BINARY, 11, 2
        )

    def morphological_opening(self, kernel_size=3):
      if self.preprocessed_image is not None:
        kernel = np.ones((kernel_size, kernel_size), np.uint8)
        self.preprocessed_image = cv2.morphologyEx(self.preprocessed_image, cv2.MORPH_OPEN, kernel)

    def edge_detection(self):
      if self.preprocessed_image is not None:
        self.preprocessed_image = cv2.Canny(self.preprocessed_image, 50, 150)

    def threshold(self):
      if self.preprocessed_image is None:
        return "Error: No preprocessed image available!"
      gray = cv2.cvtColor(self.preprocessed_image, cv2.COLOR_BGR2GRAY)
      _, self.preprocessed_image = cv2.threshold(gray, 127, 255, cv2.THRESH_BINARY)
      return None
    
    def preprocess_for_ocr(self):
      self.warp_image()

      gray = cv2.cvtColor(self.preprocessed_image, cv2.COLOR_BGR2GRAY)
      blurred = cv2.GaussianBlur(gray, (5, 5), 0)
      thresh = cv2.adaptiveThreshold(
        blurred, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
        cv2.THRESH_BINARY, 11, 2
      )
      kernel = np.ones((2, 2), np.uint8)
      cleaned = cv2.morphologyEx(thresh, cv2.MORPH_OPEN, kernel)
      self.preprocessed_image = cleaned
      return self.preprocessed_image
    
    def preprocess_for_aruco(self):
      gray = cv2.cvtColor(self.image, cv2.COLOR_BGR2GRAY)
      equalized = cv2.equalizeHist(gray)
      self.preprocessed_image = equalized
      return self.preprocessed_image

    def preprocess_image(self):
      self.preprocessed_image = self.image
      result = self.warp_image()
      if result is not None:
        print(result)
      return self.preprocessed_image

    def set_image(self, image):
      self.image = image
      self.preprocessed_image = None

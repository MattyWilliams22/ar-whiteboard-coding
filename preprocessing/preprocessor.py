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
    self.corners = None
    self.ids = None

  def warp_image(self, image, margin=0.01):
    gray = image if len(image.shape) == 2 else cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    corners, ids, _ = cv2.aruco.detectMarkers(gray, self.aruco_dict, parameters=self.aruco_params)

    if corners is None or ids is None or len(ids) < 4:
      if ids is not None:
        return None, f"Error: Not enough markers detected! Detected: {len(ids)}"
      else:
        return None, "Error: No markers detected!"

    self.corners = corners
    self.ids = ids

    src_points = self.get_corner_markers()
    if src_points is None:
      src_points = self.get_outermost_markers()
    if src_points is None:
      return None, "Error: Could not compute source points!"

    # Calculate width and height based on source points
    width_top = np.linalg.norm(src_points[0] - src_points[1])
    width_bottom = np.linalg.norm(src_points[3] - src_points[2])
    width = int(max(width_top, width_bottom))

    height_left = np.linalg.norm(src_points[0] - src_points[3])
    height_right = np.linalg.norm(src_points[1] - src_points[2])
    height = int(max(height_left, height_right))

    # Add 1% margin
    margin_x = int(margin * width)
    margin_y = int(margin * height)

    dst_points = np.array([
        [margin_x, margin_y],
        [width - 1 - margin_x, margin_y],
        [width - 1 - margin_x, height - 1 - margin_y],
        [margin_x, height - 1 - margin_y]
    ], dtype=np.float32)

    # Increase output size to include margin
    full_width = width
    full_height = height

    H = cv2.getPerspectiveTransform(src_points, dst_points)
    warped = cv2.warpPerspective(image, H, (full_width, full_height))
    return warped, None

  def get_corner_markers(self):
    marker_map = {
      "Top Left": None,
      "Top Right": None,
      "Bottom Left": None,
      "Bottom Right": None
    }

    for corner, id in zip(self.corners, self.ids):
      label = get_keyword(id[0])
      if label in marker_map:
        marker_map[label] = corner[0]  # all 4 corners of the detected marker

    if any(v is None for v in marker_map.values()):
      return None  # Not all 4 required corner markers were found

    top_left = marker_map["Top Left"][0]         # top-left of TL marker
    top_right = marker_map["Top Right"][1]       # top-right of TR marker
    bottom_right = marker_map["Bottom Right"][2] # bottom-right of BR marker
    bottom_left = marker_map["Bottom Left"][3]   # bottom-left of BL marker

    return np.array([top_left, top_right, bottom_right, bottom_left], dtype=np.float32)

  def get_outermost_markers(self):
    if self.corners is None:
      return None
    points = np.concatenate(self.corners).reshape(-1, 2)
    top_left = min(points, key=lambda p: p[0] + p[1])
    top_right = max(points, key=lambda p: p[0] - p[1])
    bottom_right = max(points, key=lambda p: p[0] + p[1])
    bottom_left = min(points, key=lambda p: p[0] - p[1])
    return np.array([top_left, top_right, bottom_right, bottom_left], dtype=np.float32)
  
  def preprocess_image(self):
    if self.original_image is None:
      return None

    if self.warped_image is None:
      self.warped_image, err = self.warp_image(self.original_image)
      if err:
        print(err)
        return None

    return self.warped_image
  
  def get_warped_image(self):
    return self.warped_image

  def set_image(self, image):
    self.original_image = image
    self.warped_image = None
    self.corners = None
    self.ids = None

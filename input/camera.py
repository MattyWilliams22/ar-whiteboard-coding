import cv2

TEST_FILE_PATH = "test_images/IMG_1097.JPEG"

class Camera:
  def __init__(self, debug_mode=False):
    self.video_source = 1  # Default to the first camera device
    self.capture = None
    self.frame = None
    self.debug_mode = debug_mode

  def __del__(self):
    if self.capture is not None:
      self.capture.release()

  def load_image(self, image_path):
    image = cv2.imread(image_path)
    if image is None:
      return None

    return image

  def capture_frame(self):
    if self.debug_mode:
      if self.frame is None:
        self.frame = self.load_image(TEST_FILE_PATH)
      return self.frame
    
    if self.capture is None:
      self.capture = cv2.VideoCapture(self.video_source)

    ret, self.frame = self.capture.read()
    if not ret:
      return None

    return self.frame
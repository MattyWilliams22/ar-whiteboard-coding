import cv2
from preprocessing.preprocessor import Preprocessor  # Update this with your module path

# Load your test image
image = cv2.imread("test_images/IMG_1081.JPEG")
pre = Preprocessor(image)

ocr = pre.preprocess_for_ocr()

cv2.imshow("Preprocessed Image", ocr)

cv2.waitKey(0)  # Wait for a key press to close the window

aruco = pre.preprocess_for_aruco()
cv2.imshow("Preprocessed ArUco Image", aruco)

cv2.waitKey(0)  # Wait for a key press to close the window

cv2.destroyAllWindows()

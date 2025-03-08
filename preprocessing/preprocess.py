import cv2
import numpy as np

def preprocess_image(image):
    # Step 1: Convert to grayscale
    gray_image = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

    # Step 2: Apply Gaussian blur to reduce noise
    blurred_image = cv2.GaussianBlur(gray_image, (5, 5), 0)

    # Step 3: Adaptive thresholding for high contrast
    thresh_image = cv2.adaptiveThreshold(blurred_image, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, 11, 2)

    # Step 4: Apply morphological transformations to remove noise
    kernel = np.ones((3, 3), np.uint8)
    processed_image = cv2.morphologyEx(thresh_image, cv2.MORPH_OPEN, kernel)

    return processed_image

if __name__ == "__main__":
    image = cv2.imread("test_images/persp.jpg")
    cv2.imshow("Original Image", image)
    processed_image = preprocess_image(image)
    cv2.imshow("Processed Image", processed_image)
    cv2.waitKey(0)
    cv2.destroyAllWindows()

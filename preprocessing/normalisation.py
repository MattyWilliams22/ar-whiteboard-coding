import cv2
import numpy as np

def find_outermost_markers(corners):
    """
    Given detected marker corners, find the four outermost points
    to define the region for perspective transformation.
    """
    all_points = np.concatenate(corners).reshape(-1, 2)  # Flatten all corner points

    # Find the outermost points
    top_left = min(all_points, key=lambda p: p[0] + p[1])  # Smallest x + y
    top_right = max(all_points, key=lambda p: p[0] - p[1])  # Largest x - y
    bottom_right = max(all_points, key=lambda p: p[0] + p[1])  # Largest x + y
    bottom_left = min(all_points, key=lambda p: p[0] - p[1])  # Smallest x - y

    return np.array([top_left, top_right, bottom_right, bottom_left], dtype=np.float32)

def normalize_whiteboard(image, aruco_dict_type=cv2.aruco.DICT_4X4_50):
    # Load ArUco dictionary and parameters
    aruco_dict = cv2.aruco.getPredefinedDictionary(aruco_dict_type)
    aruco_params = cv2.aruco.DetectorParameters()

    # Detect markers
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    corners, ids, _ = cv2.aruco.detectMarkers(gray, aruco_dict, parameters=aruco_params)

    if ids is None or len(ids) < 4:
        raise ValueError("Not enough markers detected! Need at least 4 for perspective transformation.")

    # Find the four outermost markers dynamically
    src_points = find_outermost_markers(corners)

    # Define the corresponding points in the rectified (normalized) space (keeping as before)
    dst_points = np.array([
        [0, 0],                      # Top-left
        [image.shape[1], 0],          # Top-right
        [image.shape[1], image.shape[0]],  # Bottom-right
        [0, image.shape[0]],          # Bottom-left
    ], dtype=np.float32)

    # Compute the homography matrix
    homography_matrix = cv2.getPerspectiveTransform(src_points, dst_points)

    # Get the corners of the transformed image to calculate the bounds
    corners_transformed = cv2.perspectiveTransform(np.float32([src_points]), homography_matrix)

    # Get the bounding box of the transformed image
    min_x = min(corners_transformed[0][:, 0])
    max_x = max(corners_transformed[0][:, 0])
    min_y = min(corners_transformed[0][:, 1])
    max_y = max(corners_transformed[0][:, 1])

    # Calculate the dimensions of the new image
    width = int(max_x - min_x)
    height = int(max_y - min_y)

    # Define the translation matrix to fit the transformed image into the new bounds
    translation_matrix = np.array([[1, 0, -min_x], [0, 1, -min_y], [0, 0, 1]], dtype=np.float32)

    # Apply the homography matrix with translation to the whole image
    normalized_image = cv2.warpPerspective(image, homography_matrix.dot(translation_matrix), (width, height))

    return normalized_image, homography_matrix

def scale_image_for_screen(image, screen_width=1920, screen_height=1080):
    """
    Scales the image to fit within the screen resolution.
    """
    # Get the current image size
    height, width = image.shape[:2]

    # Calculate the scaling factor to fit the image within the screen
    scale_factor = min(screen_width / width, screen_height / height)

    # Calculate new dimensions based on the scale factor
    new_width = int(width * scale_factor)
    new_height = int(height * scale_factor)

    # Resize the image to fit the screen
    scaled_image = cv2.resize(image, (new_width, new_height))

    return scaled_image

# Example usage
if __name__ == "__main__":
    image = cv2.imread("test_images/persp.jpg")  # Load your image
    normalized_image, H = normalize_whiteboard(image, aruco_dict_type=cv2.aruco.DICT_6X6_50)

    # Scale the normalized image to fit the screen
    scaled_image = scale_image_for_screen(normalized_image)

    # Show the results
    cv2.imshow("Normalized Whiteboard", scaled_image)
    cv2.waitKey(0)
    cv2.destroyAllWindows()

    # Save the image if needed
    # cv2.imwrite("normalized_whiteboard_scaled.jpg", scaled_image)

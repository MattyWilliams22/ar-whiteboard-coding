import cv2
import numpy as np
from code_detection.markers.keywords import get_keyword


def find_outermost_markers(corners):
    all_points = np.concatenate(corners).reshape(-1, 2)
    top_left = min(all_points, key=lambda p: p[0] + p[1])
    top_right = max(all_points, key=lambda p: p[0] - p[1])
    bottom_right = max(all_points, key=lambda p: p[0] + p[1])
    bottom_left = min(all_points, key=lambda p: p[0] - p[1])
    return np.array([top_left, top_right, bottom_right, bottom_left], dtype=np.float32)


def find_corner_markers(corners, ids):
    top_left, top_right, bottom_left, bottom_right = None, None, None, None
    for corner, id in zip(corners, ids):
        keyword = get_keyword(id[0])
        if keyword == "Top Left":
            top_left = corner[0][0]
        elif keyword == "Top Right":
            top_right = corner[0][0]
        elif keyword == "Bottom Left":
            bottom_left = corner[0][0]
        elif keyword == "Bottom Right":
            bottom_right = corner[0][0]
    if all(x is not None for x in [top_left, top_right, bottom_left, bottom_right]):
        return np.array(
            [top_left, top_right, bottom_right, bottom_left], dtype=np.float32
        )
    return None


def normalize_whiteboard(image, aruco_dict_type=cv2.aruco.DICT_6X6_50, margin=10):
    aruco_dict = cv2.aruco.getPredefinedDictionary(aruco_dict_type)
    aruco_params = cv2.aruco.DetectorParameters()
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    corners, ids, _ = cv2.aruco.detectMarkers(gray, aruco_dict, parameters=aruco_params)
    if ids is None or len(ids) < 4:
        raise ValueError("Not enough markers detected! Need at least 4.")
    src_points = find_corner_markers(corners, ids)
    if src_points is None:
        src_points = find_outermost_markers(corners)
    dst_points = np.array(
        [
            [margin, margin],
            [image.shape[1] - margin, margin],
            [image.shape[1] - margin, image.shape[0] - margin],
            [margin, image.shape[0] - margin],
        ],
        dtype=np.float32,
    )
    homography_matrix = cv2.getPerspectiveTransform(src_points, dst_points)
    width, height = image.shape[1] + 2 * margin, image.shape[0] + 2 * margin
    normalized_image = cv2.warpPerspective(image, homography_matrix, (width, height))
    return normalized_image


def scale_image_for_screen(image, screen_width=1920, screen_height=1080):
    height, width = image.shape[:2]
    scale_factor = min(screen_width / width, screen_height / height)
    new_width, new_height = int(width * scale_factor), int(height * scale_factor)
    return cv2.resize(image, (new_width, new_height))


def test_normalisation():
    image = cv2.imread("test_images/IMG_1083.JPEG")
    normalized_image, _ = normalize_whiteboard(image, cv2.aruco.DICT_6X6_50)
    scaled_image = scale_image_for_screen(normalized_image)
    cv2.imshow("Normalized Whiteboard", scaled_image)
    cv2.waitKey(0)
    cv2.destroyAllWindows()
    cv2.imwrite("test_images/normalised_test.jpg", scaled_image)

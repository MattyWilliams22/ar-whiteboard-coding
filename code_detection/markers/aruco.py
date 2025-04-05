import cv2
import cv2.aruco as aruco
import numpy as np
from code_detection.markers.keywords import get_keyword

def transform_bounding_boxes(bboxs):
    ARUCO_COORDS = np.array([[-1, 1], [1, 1], [1, -1], [-1, -1]], dtype=np.float32)
    CARD_COORDS = np.array([[-1.3, 1.3], [8.2, 1.3], [8.2, -1.3], [-1.3, -1.3]], dtype=np.float32)
    
    transformed_bboxs = []
    
    for bbox in bboxs:
        pixel_coords = np.array(bbox, dtype=np.float32).reshape(1, 4, 2)  # Ensure it's the right shape
        
        # Compute transformation matrix from pixel coordinates to ARUCO_COORDS
        transform_matrix = cv2.getPerspectiveTransform(pixel_coords.reshape(4, 2), ARUCO_COORDS)
        
        # Compute inverse transformation matrix
        inverse_matrix = np.linalg.inv(transform_matrix)
        
        # Transform CARD_COORDS to new pixel coordinates
        new_bbox = cv2.perspectiveTransform(CARD_COORDS.reshape(1, 4, 2), inverse_matrix)
        
        transformed_bboxs.append(new_bbox)
    
    return transformed_bboxs

def transform_bounding_boxes_simple(bboxes):
    ARUCO_COORDS = np.array([[-1, 1], [1, 1], [1, -1], [-1, -1]], dtype=np.float32)
    CARD_COORDS = np.array([[-1.3, 1.3], [8.2, 1.3], [8.2, -1.3], [-1.3, -1.3]], dtype=np.float32)
    
    transformed_bboxes = []
    
    for bbox in bboxes:
        bbox = np.array(bbox, dtype=np.float32).reshape(4, 2)
        
        # Ensure bbox has the shape (4, 2) for four points (x, y)
        if bbox.shape != (4, 2):
            print(bbox.shape)
            raise ValueError("Each bounding box must have 4 corner points (x, y).")
        
        # Calculate the width, height, and center of the original bounding box
        min_x, min_y = np.min(bbox, axis=0)
        max_x, max_y = np.max(bbox, axis=0)
        
        width = max_x - min_x
        height = max_y - min_y
        
        # The side length of the new square bounding box is the maximum of width and height
        side_length = max(width, height)
        
        # The center of the bounding box
        center_x = (min_x + max_x) / 2
        center_y = (min_y + max_y) / 2
        
        # Create a square bounding box with the center as the original center
        half_side = side_length / 2
        square_bbox = np.array([
            [center_x - half_side, center_y + half_side],  # Top-left
            [center_x + half_side, center_y + half_side],  # Top-right
            [center_x + half_side, center_y - half_side],  # Bottom-right
            [center_x - half_side, center_y - half_side]   # Bottom-left
        ], dtype=np.float32)
        
        # Compute the transformation matrix from pixel coordinates to ARUCO_COORDS
        transform_matrix = cv2.getPerspectiveTransform(square_bbox.reshape(4, 2), ARUCO_COORDS)
        
        # Compute the inverse transformation matrix
        inverse_matrix = np.linalg.inv(transform_matrix)
        
        # Transform CARD_COORDS to new pixel coordinates
        new_bbox = cv2.perspectiveTransform(CARD_COORDS.reshape(1, 4, 2), inverse_matrix)
        
        transformed_bboxes.append(new_bbox)
    
    return transformed_bboxes


# ArUco marker detection function
def detect_aruco_markers(image, dictionary=cv2.aruco.DICT_4X4_50):
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    aruco_dict = cv2.aruco.getPredefinedDictionary(dictionary)
    aruco_params = cv2.aruco.DetectorParameters()
    corners, ids, _ = aruco.detectMarkers(gray, aruco_dict, parameters=aruco_params)

    corners = transform_bounding_boxes_simple(corners)

    if ids is not None:
        aruco.drawDetectedMarkers(image, corners, ids)
    return image, corners, ids

# Function to create a mask for ArUco markers
def create_aruco_mask(image, bboxs, buffer=10):
    mask = np.zeros(image.shape[:2], dtype=np.uint8)  # Create a blank mask of the same size as the image

    if bboxs is None:
        return mask

    for i in range(len(bboxs)):
        box = bboxs[i][0]

        # Convert box points to integers
        box = np.int32(box)

        # Create a bounding rectangle around the marker (with buffer)
        x_min = min(box[:, 0]) - buffer
        x_max = max(box[:, 0]) + buffer
        y_min = min(box[:, 1]) - buffer
        y_max = max(box[:, 1]) + buffer

        # Ensure the coordinates are within the image bounds
        x_min = max(0, x_min)
        x_max = min(image.shape[1], x_max)
        y_min = max(0, y_min)
        y_max = min(image.shape[0], y_max)

        # Convert to integers to ensure proper indexing
        x_min = int(x_min)
        x_max = int(x_max)
        y_min = int(y_min)
        y_max = int(y_max)

        # Fill the region in the mask
        mask[y_min:y_max, x_min:x_max] = 255

    return mask

# Function to draw ArUco-associated keywords on the image after both stages of detection
def draw_aruco_keywords(image, bboxs, ids):
    if bboxs is None:
        return None

    for i in range(len(bboxs)):
        box = bboxs[i][0]

        # Calculate the center of the marker
        center_x = int((box[0][0] + box[2][0]) / 2)
        center_y = int((box[0][1] + box[2][1]) / 2)

        # Calculate the direction vector (from top-left to top-right)
        dir_x = box[1][0] - box[0][0]
        dir_y = box[1][1] - box[0][1]

        # Normalize the direction vector to get the correct orientation
        magnitude = np.sqrt(dir_x ** 2 + dir_y ** 2)
        dir_x /= magnitude
        dir_y /= magnitude

        # Calculate the position for the text (to the right of the marker)
        offset = 70  # Distance to place the text away from the marker
        text_x = int(center_x + dir_x * offset)
        text_y = int(center_y + dir_y * offset)

        # Ensure the text is not too close to the marker
        if text_x < 0:
            text_x = center_x + 80  # If calculated text position is out of bounds
        if text_y < 0:
            text_y = center_y + 80

        # Draw the corresponding keyword to the right of the marker
        text = get_keyword(ids[i][0])
        cv2.putText(image, text, (text_x, text_y), 
                    cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 255, 0), 2, cv2.LINE_AA)

    return image
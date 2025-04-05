import cv2
import numpy as np

def generate_aruco_marker(dictionary, marker_id, size):
    """
    Generate an ArUco marker image.
    """
    marker_image = np.zeros((size, size), dtype=np.uint8)
    marker_image = cv2.aruco.generateImageMarker(dictionary, marker_id, size)
    return marker_image

def display_bounding_boxes(text_map, image_size=(1920, 1080), aruco_dict_type=cv2.aruco.DICT_4X4_50, marker_size=100, image=None):
    """
    Displays colored rectangles on an image or a transparent background for projector display with ArUco markers in corners.

    :param text_map: List of tuples (corners, text), where corners is a numpy array of shape (4,2)
    :param image_size: Tuple (width, height) of the projector display
    :param aruco_dict_type: ArUco dictionary type
    :param marker_size: Size of each ArUco marker in pixels
    :param image: Optional image to overlay the bounding boxes on
    """
    # Load or create a blank transparent image
    if image is not None:
        background = cv2.resize(image, (image_size[0], image_size[1]))  # Resize to the target image size
        # If the image is in BGR format, convert it to BGRA by adding an alpha channel
        if background.shape[2] == 3:
            background = cv2.cvtColor(background, cv2.COLOR_BGR2BGRA)
    else:
        background = np.zeros((image_size[1], image_size[0], 4), dtype=np.uint8)  # Transparent background
    
    # If an image is provided, determine the scaling factors based on the image's size
    if image is not None:
        scale_x = image_size[0] / image.shape[1]
        scale_y = image_size[1] / image.shape[0]
    else:
        scale_x = scale_y = 1  # No scaling needed if no image is provided

    # Generate random colors for each text label
    colors = {text: (np.random.randint(0, 255), np.random.randint(0, 255), np.random.randint(0, 255), 255) for _, text in text_map}
    
    # Scale and draw each bounding box
    for corners, text in text_map:
        # Scale the corners based on the image size
        scaled_corners = (corners * [scale_x, scale_y]).astype(int)
        color = colors[text]
        cv2.polylines(background, [scaled_corners], isClosed=True, color=color, thickness=2)
    
    # Load ArUco dictionary
    aruco_dict = cv2.aruco.getPredefinedDictionary(aruco_dict_type)
    
    # Define corner positions for the ArUco markers
    aruco_positions = [
        (0, 0),
        (image_size[0] - marker_size, 0),
        (image_size[0] - marker_size, image_size[1] - marker_size),
        (0, image_size[1] - marker_size)
    ]
    
    # Generate and place ArUco markers
    for i, pos in enumerate(aruco_positions):
        marker_image = generate_aruco_marker(aruco_dict, i, marker_size)
        marker_resized = cv2.resize(marker_image, (marker_size, marker_size))  # Ensure correct size
        marker_bgr = cv2.cvtColor(marker_resized, cv2.COLOR_GRAY2BGR)
        marker_bgra = cv2.merge((marker_bgr, np.full((marker_size, marker_size), 255, dtype=np.uint8)))  # Add alpha channel
        
        # Place the ArUco marker on the background (using BGRA format)
        background[pos[1]:pos[1]+marker_size, pos[0]:pos[0]+marker_size] = marker_bgra
    
    # Show the image
    cv2.imshow("Projected Bounding Boxes with ArUco Markers", background)
    cv2.waitKey(0)
    cv2.destroyAllWindows()

# Example usage
if __name__ == "__main__":
    text_map = [
        (np.array([[100, 100], [300, 100], [300, 300], [100, 300]]), "Box 1"),
        (np.array([[500, 200], [700, 200], [700, 500], [500, 500]]), "Box 2"),
        (np.array([[800, 100], [1000, 100], [1000, 400], [800, 400]]), "Box 3")
    ]
    # Provide an optional image here, or leave it None to use a transparent background
    display_bounding_boxes(text_map, image_size=(1280, 720), image=None)

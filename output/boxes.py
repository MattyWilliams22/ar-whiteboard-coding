import cv2
import numpy as np
import textwrap

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

def render_code_in_bbox(image, code, bbox, font_scale=0.6, font=cv2.FONT_HERSHEY_SIMPLEX, thickness=1):
    """
    Renders Python code inside a bounding box on an image while preserving indentation and formatting.

    :param image: The image on which to draw.
    :param code: The string of Python code to display.
    :param bbox: The bounding box as a list/array of four points (x, y).
    :param font_scale: Initial font scale (adjusted dynamically if needed).
    :param font: OpenCV font type.
    :param thickness: Thickness of the text.
    :return: Image with rendered code.
    """
    bbox = np.array(bbox, dtype=int)

    # Get bounding box dimensions
    min_x, min_y = np.min(bbox, axis=0)
    max_x, max_y = np.max(bbox, axis=0)
    box_width = max_x - min_x
    box_height = max_y - min_y

    # Split code into lines while preserving indentation
    code_lines = code.split("\n")
    wrapped_lines = []
    max_chars_per_line = max(10, box_width // 10)

    for line in code_lines:
        leading_spaces = len(line) - len(line.lstrip(" "))
        wrapped = textwrap.wrap(line.lstrip(" "), width=max_chars_per_line - leading_spaces) or [""]
        wrapped = [(" " * leading_spaces) + w for w in wrapped]
        wrapped_lines.extend(wrapped)

    # Adjust font size dynamically
    while True:
        text_size = cv2.getTextSize("A", font, font_scale, thickness)[0]  # Sample text size
        line_height = int(text_size[1] * 1.6)  # Dynamic spacing
        total_text_height = line_height * len(wrapped_lines)

        if total_text_height > box_height:
            font_scale -= 0.1
            if font_scale < 0.4:  # Prevent excessive shrinking
                break
        else:
            break

    # Draw text inside the bounding box
    y_offset = min_y + line_height
    for line in wrapped_lines:
        text_size = cv2.getTextSize(line, font, font_scale, thickness)[0]
        text_x = min_x + 5  # Left padding
        cv2.putText(image, line, (text_x, y_offset), font, font_scale, (255, 255, 255), thickness, cv2.LINE_AA)
        y_offset += line_height  # Move to the next line

    return image

def create_boxes(text_map, image_size=None):
    # Find the markers for "Python Code:" and "Output:"
    python_marker = None
    output_marker = None
    existing_boxes = []
    
    for corners, text in text_map:
        if text == "Python Code:":
            python_marker = corners
        elif text == "Output:":
            output_marker = corners
        else:
            existing_boxes.append(corners)
    
    # Get the bounding box coordinates for a set of corners
    def get_bbox_extents(corners):
        x_coords = [p[0] for p in corners]
        y_coords = [p[1] for p in corners]
        min_x, max_x = min(x_coords), max(x_coords)
        min_y, max_y = min(y_coords), max(y_coords)
        return (min_x, min_y, max_x, max_y)
    
    # Check if two bounding boxes overlap
    def boxes_overlap(box1, box2):
        box1_min_x, box1_min_y, box1_max_x, box1_max_y = get_bbox_extents(box1)
        box2_min_x, box2_min_y, box2_max_x, box2_max_y = get_bbox_extents(box2)
        
        # Check if one box is to the left of the other
        if box1_max_x < box2_min_x or box2_max_x < box1_min_x:
            return False
        # Check if one box is above the other
        if box1_max_y < box2_min_y or box2_max_y < box1_min_y:
            return False
        return True
    
    # Determine the image boundaries
    if image_size is not None:
        image_max_x, image_max_y = image_size
    else:
        all_x = []
        all_y = []
        for corners in existing_boxes:
            for point in corners:
                all_x.append(point[0])
                all_y.append(point[1])
        image_max_x = max(all_x) if all_x else (python_marker[2][0] if python_marker is not None else (output_marker[2][0] if output_marker is not None else 100))
        image_max_y = max(all_y) if all_y else (python_marker[2][1] if python_marker is not None else (output_marker[2][1] if output_marker is not None else 100))
    
    py_box = None
    out_box = None
    
    if python_marker is not None:
        py_min_x, py_min_y, py_max_x, py_max_y = get_bbox_extents(python_marker)
        py_start_x = py_min_x
        py_start_y = py_max_y  # starts just below the Python marker
        
        # Initialize Python box to extend to image boundaries
        py_box = [
            [py_start_x, py_start_y],
            [image_max_x, py_start_y],
            [image_max_x, image_max_y],
            [py_start_x, image_max_y]
        ]
        
        # Adjust the Python box to avoid overlapping with existing boxes
        for box in existing_boxes:
            if boxes_overlap(py_box, box):
                box_min_x, box_min_y, box_max_x, box_max_y = get_bbox_extents(box)
                # Adjust py_box to stop before the overlapping box
                if box_min_y > py_start_y:
                    # The overlapping box is below, adjust the height of py_box
                    py_box[2][1] = box_min_y
                    py_box[3][1] = box_min_y
                elif box_min_x > py_start_x:
                    # The overlapping box is to the right, adjust the width of py_box
                    py_box[1][0] = box_min_x
                    py_box[2][0] = box_min_x
    
    if output_marker is not None:
        out_min_x, out_min_y, out_max_x, out_max_y = get_bbox_extents(output_marker)
        out_start_x = out_min_x
        out_start_y = out_max_y  # starts just below the Output marker
        
        # Initialize Output box to extend to image boundaries
        out_box = [
            [out_start_x, out_start_y],
            [image_max_x, out_start_y],
            [image_max_x, image_max_y],
            [out_start_x, image_max_y]
        ]
        
        # Adjust the Output box to avoid overlapping with existing boxes
        for box in existing_boxes:
            if boxes_overlap(out_box, box):
                box_min_x, box_min_y, box_max_x, box_max_y = get_bbox_extents(box)
                # Adjust out_box to stop before the overlapping box
                if box_min_y > out_start_y:
                    # The overlapping box is below, adjust the height of out_box
                    out_box[2][1] = box_min_y
                    out_box[3][1] = box_min_y
                elif box_min_x > out_start_x:
                    # The overlapping box is to the right, adjust the width of out_box
                    out_box[1][0] = box_min_x
                    out_box[2][0] = box_min_x
    
    # If both boxes exist, check if they overlap with each other and adjust
    if py_box is not None and out_box is not None:
        if boxes_overlap(py_box, out_box):
            # Find the overlapping region and adjust the boxes
            py_min_x, py_min_y, py_max_x, py_max_y = get_bbox_extents(py_box)
            out_min_x, out_min_y, out_max_x, out_max_y = get_bbox_extents(out_box)
            
            if py_min_x < out_min_x:
                # Python box is to the left of Output box, split vertically
                split_x = (out_min_x + py_max_x) / 2
                py_box[1][0] = split_x
                py_box[2][0] = split_x
                out_box[0][0] = split_x
                out_box[3][0] = split_x
            else:
                # Python box is to the right of Output box or same x, split horizontally
                split_y = (out_min_y + py_max_y) / 2
                py_box[2][1] = split_y
                py_box[3][1] = split_y
                out_box[0][1] = split_y
                out_box[1][1] = split_y
    
    # Convert to numpy arrays if they exist
    if py_box is not None:
        py_box = np.array(py_box)
    if out_box is not None:
        out_box = np.array(out_box)
    
    return py_box, out_box

# # Example usage
# if __name__ == "__main__":
#     text_map = [
#         (np.array([[100, 100], [300, 100], [300, 300], [100, 300]]), "Box 1"),
#         (np.array([[500, 200], [700, 200], [700, 500], [500, 500]]), "Box 2"),
#         (np.array([[800, 100], [1000, 100], [1000, 400], [800, 400]]), "Box 3")
#     ]
#     # Provide an optional image here, or leave it None to use a transparent background
#     display_bounding_boxes(text_map, image_size=(1280, 720), image=None)

# Example usage:
if __name__ == "__main__":
    img = np.zeros((720, 1280, 3), dtype=np.uint8)  # Create a black image
    code_snippet = "def hello():\n    print('Hello, world!')"  # Sample Python code
    bbox = [[100, 100], [500, 100], [500, 500], [100, 500]]  # Example bounding box

    output_img = render_code_in_bbox(img, code_snippet, bbox)

    cv2.imshow("Rendered Code", output_img)
    cv2.waitKey(0)
    cv2.destroyAllWindows()
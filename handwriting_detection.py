import cv2
import cv2.aruco as aruco
import numpy as np
from paddleocr import PaddleOCR

# Initialize PaddleOCR (with angle classification disabled)
ocr = PaddleOCR(use_angle_cls=False, lang="en")


# Function to map ArUco IDs to text
def aruco_map(index):
    match index:
        case 203:
            return "IF"
        case 23:
            return "ELSE"
        case 124:
            return "FOR"
        case 62:
            return "WHILE"
        case 40:
            return "PRINT"
        case 98:
            return "RETURN"
        case _:
            return "UNKNOWN"


# Function to create a mask for ArUco markers
def create_aruco_mask(image, bboxs, ids, buffer=10):
    mask = np.zeros(
        image.shape[:2], dtype=np.uint8
    )  # Create a blank mask of the same size as the image

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


# ArUco marker detection function
def detect_aruco_markers(image, dictionary=cv2.aruco.DICT_4X4_50):
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    key = getattr(aruco, f"DICT_{6}X{6}_{250}")
    aruco_dict = cv2.aruco.getPredefinedDictionary(key)
    aruco_params = cv2.aruco.DetectorParameters()
    corners, ids, _ = aruco.detectMarkers(gray, aruco_dict, parameters=aruco_params)
    if ids is not None:
        aruco.drawDetectedMarkers(image, corners, ids)
    return image, corners, ids


# Function to detect handwritten text using a text detection model
def detect_handwritten_text(image, aruco_mask):
    # Convert image to RGB (PaddleOCR expects RGB format)
    rgb_image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)

    # Apply the ArUco mask: Set the regions with ArUco markers to black
    masked_image = cv2.bitwise_and(rgb_image, rgb_image, mask=~aruco_mask)

    # Perform OCR detection and recognition on the masked image
    results = ocr.ocr(masked_image, cls=True)

    # Draw bounding boxes and text on the image
    for line in results[0]:
        box, text = (
            line  # Unpack the bounding box and text (no confidence in this version)
        )

        startX, startY = int(box[0][0]), int(box[0][1])
        endX, endY = int(box[2][0]), int(box[2][1])

        # Draw rectangle around detected text
        cv2.rectangle(image, (startX, startY), (endX, endY), (255, 0, 0), 2)

        # Put recognized text above the rectangle
        cv2.putText(
            image,
            f"{text}",
            (startX, startY - 10),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.5,
            (0, 255, 0),
            1,
            cv2.LINE_AA,
        )

    return image, results


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
        magnitude = np.sqrt(dir_x**2 + dir_y**2)
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
        text = aruco_map(ids[i][0])
        cv2.putText(
            image,
            text,
            (text_x, text_y),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.8,
            (0, 255, 0),
            2,
            cv2.LINE_AA,
        )

    return image


# Main function to process an image
def process_image(image_path):
    image = cv2.imread(image_path)
    if image is None:
        print(f"Error: Unable to load image at {image_path}")
        return

    # Detect ArUco markers
    image, bboxs, ids = detect_aruco_markers(image)

    # Create the ArUco mask to ignore marker regions during text detection (with buffer)
    aruco_mask = create_aruco_mask(image, bboxs, ids, buffer=10)

    # Detect handwritten text
    image, _ = detect_handwritten_text(image, aruco_mask)

    # Draw ArUco-associated keywords on the image after both detections
    image = draw_aruco_keywords(image, bboxs, ids)

    # Resize the window to fit on screen and make it adjustable
    screen_width = 800
    screen_height = 600
    aspect_ratio = image.shape[1] / image.shape[0]

    if image.shape[1] > screen_width or image.shape[0] > screen_height:
        new_width = screen_width
        new_height = int(new_width / aspect_ratio)
        if new_height > screen_height:
            new_height = screen_height
            new_width = int(new_height * aspect_ratio)
        image = cv2.resize(image, (new_width, new_height))

    cv2.namedWindow("ArUco and Text Detection", cv2.WINDOW_NORMAL)
    cv2.imshow("ArUco and Text Detection", image)
    cv2.resizeWindow("ArUco and Text Detection", screen_width, screen_height)
    cv2.waitKey(0)
    cv2.destroyAllWindows()


# Example usage
process_image("sample_images/Prints.png")

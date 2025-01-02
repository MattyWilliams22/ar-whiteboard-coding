import cv2
import cv2.aruco as aruco
import numpy as np
from pytesseract import pytesseract

# Function to map ArUco IDs to text
def aruco_map(index):
  match index:
    case 0:
      return "PRINT"
    case 203:
      return "IF"
    case 23:
      return "ELSE"
    case 124:
      return "FOR"
    case 62:
      return "WHILE"
    case 40:
      return "FUNCTION"
    case 98:
      return "RETURN"
    case default:
      return "UNKNOWN"
    
def draw_keywords(image, bboxs, ids):
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

        # Normalize the direction vector
        magnitude = np.sqrt(dir_x ** 2 + dir_y ** 2)
        dir_x /= magnitude
        dir_y /= magnitude

        # Calculate the position for the text (to the right of the marker)
        offset = 50  # Distance to place the text away from the marker
        text_x = int(center_x + dir_x * offset)
        text_y = int(center_y + dir_y * offset)

        # Draw the text
        cv2.putText(image, aruco_map(ids[i][0]), (text_x, text_y), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2, cv2.LINE_AA)

    return image

# ArUco marker detection function
def detect_aruco_markers(image, dictionary=cv2.aruco.DICT_4X4_50):
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

    key = getattr(aruco, f'DICT_{6}X{6}_{250}')
    aruco_dict = cv2.aruco.getPredefinedDictionary(key)
    aruco_params = cv2.aruco.DetectorParameters()

    corners, ids, _ = aruco.detectMarkers(gray, aruco_dict, parameters=aruco_params)

    if ids is not None:
        aruco.drawDetectedMarkers(image, corners, ids)
        image = draw_keywords(image, corners, ids)
    return image

# Function to detect handwritten text
def detect_handwritten_text(image):
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    blurred = cv2.GaussianBlur(gray, (5, 5), 0)
    _, binary = cv2.threshold(blurred, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)

    contours, _ = cv2.findContours(binary, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    for contour in contours:
        x, y, w, h = cv2.boundingRect(contour)
        if w < 20 or h < 20:  # Filter out small noise
            continue

        # Draw bounding box
        cv2.rectangle(image, (x, y), (x + w, y + h), (255, 0, 0), 2)

        # Extract text using OCR
        roi = gray[y:y + h, x:x + w]

        path_to_tesseract = r"C:\Program Files\Tesseract-OCR\tesseract.exe"
        pytesseract.tesseract_cmd = path_to_tesseract

        text = pytesseract.image_to_string(roi, config='--psm 6')
        cv2.putText(image, text.strip(), (x, y - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 1, cv2.LINE_AA)
    return image

# Main function to process an image
def process_image(image_path):
    image = cv2.imread(image_path)
    if image is None:
        print(f"Error: Unable to load image at {image_path}")
        return

    # Detect ArUco markers
    image = detect_aruco_markers(image)

    # Detect handwritten text
    image = detect_handwritten_text(image)

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

    cv2.namedWindow('ArUco and Text Detection', cv2.WINDOW_NORMAL)
    cv2.imshow('ArUco and Text Detection', image)
    cv2.resizeWindow('ArUco and Text Detection', screen_width, screen_height)
    cv2.waitKey(0)
    cv2.destroyAllWindows()


# Example usage
process_image('sample_images/Mixed.jpg')

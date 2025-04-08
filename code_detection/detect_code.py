import cv2
import cv2.aruco as aruco
import numpy as np
from code_detection.markers.aruco import detect_aruco_markers, create_aruco_mask, draw_aruco_keywords
from code_detection.markers.colours import detect_colored_rectangles, create_rectangle_mask, draw_rectangle_keywords
from code_detection.ocr.paddleocr import detect_paddleocr_text
from code_detection.markers.keywords import get_keyword, CODE_MAX

def combine_markers_and_text(handwritten_text, bboxs, ids):
    text_map = []

    # Draw bounding boxes and text on the image
    for line in handwritten_text[0]:
        box, prediction = line  # Unpack the bounding box and text
        text, _ = prediction

        startX, startY = int(box[0][0]), int(box[0][1])
        endX, endY = int(box[2][0]), int(box[2][1])

        corners = np.array([[startX, startY], [endX, startY], [endX, endY], [startX, endY]])

        text_map.append((corners, text))

    for i in range(len(bboxs)):
        box = bboxs[i][0]

        corners = np.array([[box[0][0], box[0][1]], [box[1][0], box[1][1]], 
                        [box[2][0], box[2][1]], [box[3][0], box[3][1]]])
        
        text = get_keyword(ids[i][0])

        text_map.append((corners, text))

    return text_map

def detect_markers(marker_type: str, image):
    match marker_type:
        case "aruco4x4_50":
            return detect_aruco_markers(image, cv2.aruco.DICT_4X4_50)
        case "aruco6x6_50":
            return detect_aruco_markers(image, cv2.aruco.DICT_6X6_50)
        case "aruco6x6_250":
            return detect_aruco_markers(image, cv2.aruco.DICT_6X6_250)
        case "colour":
            return detect_colored_rectangles(image)
        case _:
            return None, None, None

def create_mask(marker_type: str, image, bboxs):
    match marker_type:
        case "aruco4x4_50":
            return create_aruco_mask(image, bboxs)
        case "aruco6x6_50":
            return create_aruco_mask(image, bboxs)
        case "aruco6x6_250":
            return create_aruco_mask(image, bboxs)
        case "colour":
            return create_rectangle_mask(image, bboxs)
        case _:
            return None
        
def detect_text(ocr_type: str, image, mask):
    match ocr_type:
        case "paddleocr":
            return detect_paddleocr_text(image, mask)
        case _:
            return None, None
        
def draw_keywords(marker_type: str, image, bboxs, ids):
    match marker_type:
        case "aruco4x4_50":
            return draw_aruco_keywords(image, bboxs, ids)
        case "aruco6x6_50":
            return draw_aruco_keywords(image, bboxs, ids)
        case "aruco6x6_250":
            return draw_aruco_keywords(image, bboxs, ids)
        case "colour":
            result = draw_rectangle_keywords(image, bboxs, ids)
            print(result)
            return result
        case _:
            return None

def detect_code(marker_type: str, ocr_type: str, image):
    if image is None:
        return None, None
    
    image, bboxs, ids = detect_markers(marker_type, image)

    if image is None:
        print("Error: Marker detection failed")
        return None, None

    mask = create_mask(marker_type, image, bboxs)

    image, text = detect_text(ocr_type, image, mask)

    if image is None:
        print("Error: Text detection failed")
        return None, None

    boxes = combine_markers_and_text(text, bboxs, ids)

    return image, boxes
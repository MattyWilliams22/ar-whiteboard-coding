import cv2
from code_detection.markers.aruco import detect_aruco_markers, create_aruco_mask, draw_aruco_keywords
from code_detection.ocr.paddle_ocr import detect_paddleocr_text
# from code_detection.ocr.easy_ocr import detect_easyocr_text
# from code_detection.ocr.py_tesseract import detect_pytesseract_text
# from code_detection.ocr.kerasocr import detect_kerasocr_text
# from code_detection.ocr.trocr import detect_trocr_text
# from code_detection.assemble_code import assemble_code

def detect_markers(marker_type: str, image):
    match marker_type:
        case "aruco4x4_50":
            return detect_aruco_markers(image, cv2.aruco.DICT_4X4_50)
        case "aruco6x6_50":
            return detect_aruco_markers(image, cv2.aruco.DICT_6X6_50)
        case "aruco6x6_250":
            return detect_aruco_markers(image, cv2.aruco.DICT_6X6_250)
        case _:
            return None, None

def create_mask(marker_type: str, image, bboxs, ids):
    match marker_type:
        case "aruco4x4_50":
            return create_aruco_mask(image, bboxs, ids)
        case "aruco6x6_50":
            return create_aruco_mask(image, bboxs, ids)
        case "aruco6x6_250":
            return create_aruco_mask(image, bboxs, ids)
        case _:
            return None
        
def detect_text(ocr_type: str, image, mask):
    match ocr_type:
        case "paddleocr":
            return detect_paddleocr_text(image, mask)
        # case "easyocr":
        #     return detect_easyocr_text(image, mask)
        # case "pytesseract":
        #     return detect_pytesseract_text(image, mask)
        # case "kerasocr":
        #     return detect_kerasocr_text(image, mask)
        # case "trocr":
        #     return detect_trocr_text(image, mask)
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
        case _:
            return None

def detect_code(marker_type: str, ocr_type: str, image):
    if image is None:
        return None, None
    
    image, bboxs, ids = detect_markers(marker_type, image)

    if image is None:
        print("Error: Marker detection failed")
        return None, None

    mask = create_mask(marker_type, image, bboxs, ids)

    image, text = detect_text(ocr_type, image, mask)

    if image is None:
        print("Error: Text detection failed")
        return None, None

    image = draw_keywords(marker_type, image, bboxs, ids)

    if image is None:
        print("Error: Drawing keywords failed")
        return None, None

    code = assemble_code(text, bboxs, ids)

    return image, code
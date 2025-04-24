import cv2
import numpy as np
from collections import defaultdict
from code_detection.markers.aruco import detect_aruco_markers, create_aruco_mask
from code_detection.ocr.paddleocr import detect_paddleocr_text
from code_detection.markers.keywords import get_keyword

def compute_iou(box1, box2):
    # Compute bounding rectangles from polygon boxes
    rect1 = cv2.boundingRect(np.array(box1))
    rect2 = cv2.boundingRect(np.array(box2))

    x1, y1, w1, h1 = rect1
    x2, y2, w2, h2 = rect2

    xi1 = max(x1, x2)
    yi1 = max(y1, y2)
    xi2 = min(x1 + w1, x2 + w2)
    yi2 = min(y1 + h1, y2 + h2)

    inter_area = max(0, xi2 - xi1) * max(0, yi2 - yi1)
    box1_area = w1 * h1
    box2_area = w2 * h2

    union_area = box1_area + box2_area - inter_area
    if union_area == 0:
        return 0
    return inter_area / union_area

class Detector:
    def __init__(self, images, aruco_dict_type=cv2.aruco.DICT_6X6_50):
        self.images = images
        self.aruco_dict_type = aruco_dict_type
        self.all_boxes = []

    def detect_from_image(self, image):
        image, corners, ids = detect_aruco_markers(image, self.aruco_dict_type)
        if image is None:
            return [], []

        mask = create_aruco_mask(image, corners)
        image, text = detect_paddleocr_text(image, mask)

        boxes = []

        if text and text[0]:
            for line in text[0]:
                box, prediction = line
                text_val, _ = prediction
                if text_val == "PYTHON":
                    text_val = "PYTHON:"
                elif text_val == "OUTPUT":
                    text_val = "OUTPUT:"
                startX, startY = int(box[0][0]), int(box[0][1])
                endX, endY = int(box[2][0]), int(box[2][1])
                corners = np.array([[startX, startY], [endX, startY], [endX, endY], [startX, endY]])
                boxes.append((corners, text_val, 'ocr'))

        if ids is not None:
            for i in range(len(corners)):
                box = corners[i][0]
                corners = np.array([[box[0][0], box[0][1]], [box[1][0], box[1][1]], 
                                    [box[2][0], box[2][1]], [box[3][0], box[3][1]]])
                text_val = get_keyword(ids[i][0])
                boxes.append((corners, text_val, 'aruco'))

        return boxes

    def combine_boxes(self, all_detected_boxes, iou_threshold=0.5):
        combined = []

        while all_detected_boxes:
            ref_box = all_detected_boxes.pop(0)
            group = [ref_box]

            to_remove = []
            for i, box in enumerate(all_detected_boxes):
                if compute_iou(ref_box[0], box[0]) >= iou_threshold:
                    group.append(box)
                    to_remove.append(i)
            for i in reversed(to_remove):
                all_detected_boxes.pop(i)

            # Priority to aruco
            aruco_boxes = [b for b in group if b[2] == 'aruco']
            if aruco_boxes:
                combined.append((aruco_boxes[0][0], aruco_boxes[0][1]))  # use first ArUco box
            else:
                text_counts = defaultdict(int)
                for _, text, _ in group:
                    text_counts[text] += 1
                most_common = max(text_counts.items(), key=lambda x: x[1])[0]
                combined.append((ref_box[0], most_common))

        return combined

    def detect_code(self):
        if not self.images:
            print("Error: No images provided")
            return None, None

        all_detected_boxes = []
        for img in self.images:
            boxes = self.detect_from_image(img)
            all_detected_boxes.extend(boxes)

        final_boxes = self.combine_boxes(all_detected_boxes)
        return self.images[0], final_boxes  # Return one of the processed images and combined boxes

    def set_images(self, images):
        self.images = images

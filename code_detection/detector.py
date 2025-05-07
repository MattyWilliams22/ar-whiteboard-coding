import cv2
import numpy as np
from collections import defaultdict
from code_detection.markers.aruco import detect_aruco_markers, create_aruco_mask
from code_detection.ocr.paddleocr import detect_paddleocr_text
from code_detection.markers.keywords import get_keyword, ALL_KEYWORDS


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

    def text_box_to_card(self, box, aruco_boxes):
        if not aruco_boxes:
            raise ValueError("No ArUco boxes provided for scaling reference.")

        # Get the text box center (in image coordinates)
        text_center_x = (box[0][0] + box[2][0]) / 2
        text_center_y = (box[0][1] + box[2][1]) / 2

        # Check if the first ArUco box is transformed (card) or raw (marker)
        aruco_sample = aruco_boxes[0][0]  # Take the first box
        aruco_width = abs(aruco_sample[1][0] - aruco_sample[0][0])
        aruco_height = abs(aruco_sample[2][1] - aruco_sample[1][1])

        # Criteria to detect transformed boxes (cards are much wider than tall)
        is_transformed = (aruco_width / aruco_height) > 3.0

        if is_transformed:
            # If already a card box, use its dimensions directly
            card_width = aruco_width
            card_height = aruco_height
        else:
            # If raw ArUco box, scale it to card dimensions (10.0 × 2.6 units)
            card_width = aruco_width * (10.0 / 2.0) * 0.8  # Card is 10 units wide (8.7 - (-1.3))
            card_height = aruco_height * (2.6 / 2.0)  # Card is 2.6 units tall (1.3 - (-1.3))

        # Compute card position (accounting for text offset)
        # Text is at (4.8, 0) relative to card's (-1.3, -1.3) to (8.7, 1.3)
        # So, text is 6.1 units from the left edge (4.8 - (-1.3))
        # Card's left edge = text_center_x - (6.1 / 10.0) * card_width
        card_left = text_center_x - (6.1 / 10.0) * card_width
        card_top = text_center_y - (1.3 / 2.6) * card_height  # Text is vertically centered

        # Compute card corners
        top_left = (card_left, card_top)
        top_right = (card_left + card_width, card_top)
        bottom_left = (card_left, card_top + card_height)
        bottom_right = (card_left + card_width, card_top + card_height)

        new_box = np.array([
            [top_left[0], top_left[1]],
            [top_right[0], top_right[1]],
            [bottom_right[0], bottom_right[1]],
            [bottom_left[0], bottom_left[1]],
        ], dtype=np.float32)

        return new_box

    def detect_from_image(self, image):
        image, aruco_corners, ids = detect_aruco_markers(image, self.aruco_dict_type)
        if image is None:
            return [], []

        mask = create_aruco_mask(image, aruco_corners)
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
                corners = np.array(
                    [[startX, startY], [endX, startY], [endX, endY], [startX, endY]]
                )

                if text_val in ALL_KEYWORDS:
                    corners = self.text_box_to_card(corners, aruco_corners)
                    boxes.append((corners, text_val, "aruco"))
                else:
                    boxes.append((corners, text_val, "ocr"))

        if ids is not None:
            for i in range(len(aruco_corners)):
                marker_corners = aruco_corners[i][0]
                box_corners = np.array(
                    [
                        [marker_corners[0][0], marker_corners[0][1]],
                        [marker_corners[1][0], marker_corners[1][1]],
                        [marker_corners[2][0], marker_corners[2][1]],
                        [marker_corners[3][0], marker_corners[3][1]],
                    ]
                )
                text_val = get_keyword(ids[i][0])
                boxes.append((box_corners, text_val, "aruco"))

        return boxes

    def combine_boxes(
        self,
        all_detected_boxes,
        iou_threshold=0.5,
        containment_threshold=0.9,
        appearance_threshold=0.2,
    ):
        # First, count how many times each text box appears across images
        text_box_counts = defaultdict(int)
        text_box_map = defaultdict(list)

        for box in all_detected_boxes:
            if box[2] == "ocr":  # Only count text boxes
                # Convert box to a hashable format for counting
                box_key = (tuple(map(tuple, box[0])), box[1])
                text_box_counts[box_key] += 1
                text_box_map[box_key].append(box)

        # Filter out text boxes that appear in less than appearance_threshold of images
        total_images = len(self.images)
        min_appearances = appearance_threshold * total_images
        filtered_boxes = []

        for box in all_detected_boxes:
            if box[2] == "aruco":
                filtered_boxes.append(box)  # Always accept aruco boxes
            else:
                box_key = (tuple(map(tuple, box[0])), box[1])
                if text_box_counts[box_key] >= min_appearances:
                    filtered_boxes.append(box)

        # Now process the filtered boxes
        combined = []
        processed_boxes = set()  # To track boxes we've already processed

        # First pass: identify text boxes that are >90% contained within aruco boxes
        aruco_boxes = [box for box in filtered_boxes if box[2] == "aruco"]
        ocr_boxes = [box for box in filtered_boxes if box[2] == "ocr"]

        boxes_to_remove = set()

        for aruco_box in aruco_boxes:
            aruco_rect = cv2.boundingRect(np.array(aruco_box[0]))

            for ocr_box in ocr_boxes:
                ocr_rect = cv2.boundingRect(np.array(ocr_box[0]))

                # Calculate containment
                x1, y1, w1, h1 = aruco_rect
                x2, y2, w2, h2 = ocr_rect

                # Area of intersection
                xi1 = max(x1, x2)
                yi1 = max(y1, y2)
                xi2 = min(x1 + w1, x2 + w2)
                yi2 = min(y1 + h1, y2 + h2)
                inter_area = max(0, xi2 - xi1) * max(0, yi2 - yi1)

                # Area of OCR box
                ocr_area = w2 * h2

                if ocr_area > 0 and (inter_area / ocr_area) > containment_threshold:
                    # Mark this OCR box for removal
                    box_key = (tuple(map(tuple, ocr_box[0])), ocr_box[1])
                    boxes_to_remove.add(box_key)

        # Second pass: combine boxes with similar IoU
        remaining_boxes = [
            box
            for box in filtered_boxes
            if box[2] == "aruco"
            or (tuple(map(tuple, box[0])), box[1]) not in boxes_to_remove
        ]

        while remaining_boxes:
            ref_box = remaining_boxes.pop(0)
            ref_key = (tuple(map(tuple, ref_box[0])), ref_box[1])

            if ref_key in processed_boxes:
                continue

            group = [ref_box]
            processed_boxes.add(ref_key)

            to_remove = []
            for i, box in enumerate(remaining_boxes):
                box_key = (tuple(map(tuple, box[0])), box[1])

                if box_key in processed_boxes:
                    continue

                if compute_iou(ref_box[0], box[0]) >= iou_threshold:
                    group.append(box)
                    processed_boxes.add(box_key)
                    to_remove.append(i)

            for i in reversed(to_remove):
                remaining_boxes.pop(i)

            # Priority to aruco
            aruco_boxes_in_group = [b for b in group if b[2] == "aruco"]
            if aruco_boxes_in_group:
                # Use the first ArUco box and ensure it's only added once
                combined.append(
                    (aruco_boxes_in_group[0][0], aruco_boxes_in_group[0][1])
                )
            else:
                # For text boxes, use the most common one in the group
                text_counts = defaultdict(int)
                for _, text, _ in group:
                    text_counts[text] += 1
                most_common = max(text_counts.items(), key=lambda x: x[1])[0]
                combined.append((ref_box[0], most_common))

        # Remove any exact duplicates that might remain
        unique_combined = []
        seen = set()

        for box in combined:
            box_key = (tuple(map(tuple, box[0])), box[1])
            if box_key not in seen:
                seen.add(box_key)
                unique_combined.append(box)

        return unique_combined

    def detect_code(self):
        if not self.images:
            print("Error: No images provided")
            return None, None

        all_detected_boxes = []
        for img in self.images:
            boxes = self.detect_from_image(img)
            all_detected_boxes.extend(boxes)

        final_boxes = self.combine_boxes(all_detected_boxes)
        return (
            self.images[0],
            final_boxes,
        )  # Return one of the processed images and combined boxes

    def set_images(self, images):
        self.images = images

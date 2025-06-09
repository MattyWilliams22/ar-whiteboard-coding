from typing import List
import cv2
import numpy as np
from collections import defaultdict
from Levenshtein import distance as lev_dist
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


def compute_intersection_area(box1, box2):
    # Convert to numpy arrays
    poly1 = np.array(box1, dtype=np.float32).reshape(-1, 1, 2)
    poly2 = np.array(box2, dtype=np.float32).reshape(-1, 1, 2)

    # Calculate intersection
    intersection, _ = cv2.intersectConvexConvex(poly1, poly2)
    return intersection


class Detector:
    def __init__(self, images, aruco_dict_type=cv2.aruco.DICT_6X6_50):
        self.images = images
        self.aruco_dict_type = aruco_dict_type
        self.all_boxes = []

    def text_box_to_card(self, box, aruco_boxes):
        if not aruco_boxes:
            raise ValueError("No ArUco boxes provided for scaling reference.")

        # Get the text box centre (in image coordinates)
        text_centre_x = (box[0][0] + box[2][0]) / 2
        text_centre_y = (box[0][1] + box[2][1]) / 2

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
            card_width = (
                aruco_width * (10.0 / 2.0) * 0.8
            )  # Card is 10 units wide (8.7 - (-1.3))
            card_height = aruco_height * (
                2.6 / 2.0
            )  # Card is 2.6 units tall (1.3 - (-1.3))

        # Compute card position (accounting for text offset)
        # Text is at (4.8, 0) relative to card's (-1.3, -1.3) to (8.7, 1.3)
        # So, text is 6.1 units from the left edge (4.8 - (-1.3))
        # Card's left edge = text_centre_x - (6.1 / 10.0) * card_width
        card_left = text_centre_x - (6.1 / 10.0) * card_width
        card_top = (
            text_centre_y - (1.3 / 2.6) * card_height
        )  # Text is vertically centred

        # Compute card corners
        top_left = (card_left, card_top)
        top_right = (card_left + card_width, card_top)
        bottom_left = (card_left, card_top + card_height)
        bottom_right = (card_left + card_width, card_top + card_height)

        # Create new box with card corners
        new_box = np.array(
            [
                [top_left[0], top_left[1]],
                [top_right[0], top_right[1]],
                [bottom_right[0], bottom_right[1]],
                [bottom_left[0], bottom_left[1]],
            ],
            dtype=np.float32,
        )

        return new_box

    def detect_from_image(self, image, image_id):
        # Detect ArUco markers in the image
        image, aruco_corners, ids = detect_aruco_markers(image, self.aruco_dict_type)
        if image is None:
            return [], []

        # Create a mask for the detected ArUco markers
        mask = create_aruco_mask(image, aruco_corners)

        # Detect text using PaddleOCR
        image, text = detect_paddleocr_text(image, mask)

        boxes = []

        # Add detected text boxes to list of boxes
        if text and text[0]:
            for line in text[0]:
                box, prediction = line
                text_val, _ = prediction
                startX, startY = int(box[0][0]), int(box[0][1])
                endX, endY = int(box[2][0]), int(box[2][1])
                corners = np.array(
                    [[startX, startY], [endX, startY], [endX, endY], [startX, endY]]
                )

                text_val.replace('"', '\"').replace("'", "\'")  # Escape quotes in text

                # Check if the detected text is a keyword
                # and if it is, transform the box to card coordinates
                upper_text_val = text_val.upper()
                if upper_text_val in ALL_KEYWORDS or upper_text_val in ["PYTHON", "RESULTS"]:
                    corners = self.text_box_to_card(corners, aruco_corners)
                    if upper_text_val == "ELSEIF":
                        upper_text_val = "ELSE IF"
                    boxes.append((corners, str(upper_text_val), "aruco", image_id))
                else:
                    boxes.append((corners, str(text_val), "ocr", image_id))

        # Add detected ArUco boxes to list of boxes
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
                boxes.append((box_corners, str(text_val), "aruco", image_id))

        return boxes

    def group_boxes_by_overlap(self, boxes):
        # Initialize each box as its own group
        parents = [i for i in range(len(boxes))]
        
        def find(u):
            while parents[u] != u:
                parents[u] = parents[parents[u]]  # Path compression
                u = parents[u]
            return u
        
        # Union boxes that overlap
        for i in range(len(boxes)):
            for j in range(i+1, len(boxes)):
                box1 = boxes[i]
                box2 = boxes[j]
                
                inter_area = compute_intersection_area(box1[0], box2[0])
                box1_area = cv2.contourArea(np.array(box1[0]))
                box2_area = cv2.contourArea(np.array(box2[0]))
                
                if inter_area / box1_area > 0.8 or inter_area / box2_area > 0.8:
                    root_i = find(i)
                    root_j = find(j)
                    if root_i != root_j:
                        parents[root_j] = root_i
        
        # Group boxes by their root parent
        groups = {}
        for i in range(len(boxes)):
            root = find(i)
            if root not in groups:
                groups[root] = []
            groups[root].append(boxes[i])
        
        return list(groups.values())

    def filter_boxes(self, boxes):
        # Filter boxes based on their type and the number of images
        # they appear in

        if self.images is None or len(self.images) == 0:
            image_count = 1
        else:
            image_count = len(self.images)

        # If group contains ArUco boxes, keep them
        if any(box[2] == "aruco" for box in boxes):
            return [box for box in boxes if box[2] == "aruco"]
        # Otherwise, keep OCR boxes
        else:
            ocr_boxes = [box for box in boxes if box[2] == "ocr"]
            # Ensure text is detected in at least 40% of images
            images_with_text = len(set(box[3] for box in ocr_boxes))
            if images_with_text / image_count >= 0.4:
                return ocr_boxes
            else:
                return []

    def combine_aruco_group(self, group):
        # Mean bounding box of all aruco boxes in the group
        mean_box = np.mean([box[0] for box in group], axis=0)
        # Final box including label
        combined_box = (mean_box, group[0][1])
        return combined_box

    def get_overall_box(self, boxes):
        flat_bounds = []

        for box in boxes:
            flat_bounds.extend(box[0].flatten().tolist())
        flat_bounds = np.array(flat_bounds).reshape(-1, 2)

        xs, ys = zip(*flat_bounds)
        return [
            (min(xs), min(ys)),
            (max(xs), min(ys)),
            (max(xs), max(ys)),
            (min(xs), max(ys)),
        ]

    def merge_ocr_boxes(self, boxes):
        # Merge OCR boxes into a single box

        # Sort boxes by their x coordinate
        boxes = sorted(boxes, key=lambda x: x[0][0][0])
        # Merge box labels together into a single string
        merged_label = " ".join([box[1] for box in boxes])
        # Create a new box that encompasses all the boxes in the group
        merged_box = self.get_overall_box(boxes)
        # Create a new box with the merged label
        merged_box = (merged_box, str(merged_label), "ocr", boxes[0][3])
        return merged_box

    def merge_ocr_group(self, group):
        # Group boxes by image ID
        grouped_by_image = defaultdict(list)
        for box in group:
            image_id = box[3]
            grouped_by_image[image_id].append(box)

        # Merge OCR boxes that belong to the same image
        merged_boxes = []
        for image_id, boxes in grouped_by_image.items():
            if len(boxes) > 1:
                merged_box = self.merge_ocr_boxes(boxes)
                merged_boxes.append(merged_box)
            else:
                merged_boxes.append(boxes[0])

        return merged_boxes

    def find_consensus_label(self, labels: List[str], similarity_threshold=0.8):
        # Group similar labels
        label_groups = defaultdict(list)

        # First pass: group by exact matches
        exact_counts = defaultdict(int)
        for lbl in labels:
            exact_counts[lbl] += 1

        # Second pass: fuzzy match remaining
        for label in exact_counts.keys():
            matched = False
            for existing in label_groups:
                # Normalised similarity (0-1)
                similarity = 1 - (
                    lev_dist(label, existing) / max(len(label), len(existing))
                )
                if similarity >= similarity_threshold:
                    label_groups[existing].append(label)
                    matched = True
                    break
            if not matched:
                label_groups[label] = [label]

        # Find the group with highest total count
        best_group = max(
            label_groups.items(), key=lambda x: sum(exact_counts[lbl] for lbl in x[1])
        )

        # Return the most frequent version in the best group
        return max(best_group[1], key=lambda x: exact_counts[x])

    def combine_ocr_group(self, group):
        # Find most common label in the group
        labels = [box[1] for box in group]
        best_label = self.find_consensus_label(labels)

        # Filter boxes with the best label
        filtered_boxes = [box for box in group if box[1] == best_label]

        # Create a new box with the most common label
        mean_box = np.mean([box[0] for box in filtered_boxes], axis=0)
        combined_box = (mean_box, str(best_label))

        return combined_box

    def combine_boxes(self, all_detected_boxes):
        # Combine detected boxes from mutliple images into a single list
        if all_detected_boxes is None or len(all_detected_boxes) == 0:
            return []

        combined_boxes = []

        grouped_boxes = self.group_boxes_by_overlap(all_detected_boxes)

        for group in grouped_boxes:
            filtered_boxes = self.filter_boxes(group)
            if len(filtered_boxes) > 0:
                # Check if the group contains ArUco boxes
                if any(box[2] == "aruco" for box in filtered_boxes):
                    box = self.combine_aruco_group(filtered_boxes)
                    combined_boxes.append(box)
                else:
                    # Otherwise, keep the OCR boxes
                    self.all_boxes.extend(filtered_boxes)
                    merged_boxes = self.merge_ocr_group(filtered_boxes)
                    box = self.combine_ocr_group(merged_boxes)
                    combined_boxes.append(box)

        return combined_boxes
    
    def strip_boxes(self, boxes):
        # Strip boxes to only contain the coordinates and label
        stripped_boxes = []
        for box, label, _, _ in boxes:
            stripped_boxes.append((box, label))
        return stripped_boxes

    def detect_code(self):
        if not self.images:
            print("Error: No images provided")
            return None, None

        # Detect code in the images
        all_detected_boxes = []
        for i, img in enumerate(self.images):
            boxes = self.detect_from_image(img, i)
            all_detected_boxes.extend(boxes)

        if len(self.images) > 1:
            # If multiple images, combine boxes from all images
            final_boxes = self.combine_boxes(all_detected_boxes)
        else:
            # If only one image, use the detected boxes directly
            final_boxes = self.strip_boxes(all_detected_boxes)
        return (
            self.images[0],
            final_boxes,
        )  # Return one of the processed images and combined boxes

    def set_images(self, images):
        self.images = images

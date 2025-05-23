from collections import deque
import numpy as np


class Tokeniser:
    def __init__(self, boxes, scale_factor=0.5):
        self.boxes = boxes
        self.scale_factor = scale_factor
        self.tokens = None

    def convert_boxes_to_tokens(self):
        tokens = deque()
        lines = []  # List of lines, each line is a list of (text, coordinates)

        # Process each text box
        for item in self.boxes:
            coordinates = item[0]  # Bounding box (numpy array of shape (4,2))
            text = item[1]  # Extract the text directly (string)

            # Filter out unwanted labels
            if text in [
                "PYTHON",
                "RESULTS",
                "Bottom Left",
                "Bottom Right",
                "Top Right",
                "Top Left",
                "UNKNOWN",
            ]:
                continue

            # Calculate the height of the bounding box
            height = max(point[1] for point in coordinates) - min(
                point[1] for point in coordinates
            )

            # Calculate the vertical center of the bounding box
            top_y = min(point[1] for point in coordinates)
            bottom_y = max(point[1] for point in coordinates)
            center_y = (top_y + bottom_y) / 2  # Vertical center

            # Calculate the dynamic line threshold
            line_threshold = height * self.scale_factor

            # Find the most appropriate line for the current box
            best_line = None
            for i, line in enumerate(lines):
                line_center_y = np.mean(
                    [
                        (
                            (min(pt[1] for pt in box[1]) + max(pt[1] for pt in box[1]))
                            / 2
                        )
                        for box in line
                    ]
                )
                if abs(center_y - line_center_y) <= line_threshold:
                    best_line = line
                    break

            if best_line is not None:
                best_line.append((text, coordinates))
            else:
                lines.append([(text, coordinates)])

        # Merge lines if necessary (when lines are too close)
        merged_lines = []
        for line in lines:
            if (
                merged_lines
                and abs(
                    np.mean(
                        [
                            (
                                (
                                    min(pt[1] for pt in box[1])
                                    + max(pt[1] for pt in box[1])
                                )
                                / 2
                            )
                            for box in line
                        ]
                    )
                    - np.mean(
                        [
                            (
                                (
                                    min(pt[1] for pt in box[1])
                                    + max(pt[1] for pt in box[1])
                                )
                                / 2
                            )
                            for box in merged_lines[-1]
                        ]
                    )
                )
                <= line_threshold
            ):
                merged_lines[-1].extend(line)
            else:
                merged_lines.append(line)

        # Sort lines top-to-bottom
        merged_lines.sort(
            key=lambda line: np.mean(
                [
                    (min(pt[1] for pt in box[1]) + max(pt[1] for pt in box[1])) / 2
                    for box in line
                ]
            )
        )

        # Sort left-to-right and append to tokens
        for line in merged_lines:
            line.sort(key=lambda item: min(point[0] for point in item[1]))  # Sort by x
            for token in line:
                tokens.append(token)
            tokens.append(("LineBreak", []))  # Separate lines

        self.tokens = tokens

    def tokens_to_string(self):
        # Convert the tokens to a string representation

        if self.tokens is None:
            return ""

        result = []
        line_tokens = []

        for token in self.tokens:
            if token[0] == "LineBreak":
                # When we encounter the "LineBreak" token, we finalize the current line and add it to the result.
                if line_tokens:
                    result.append(" ".join(line_tokens))
                    line_tokens = []  # Reset for the next line
                result.append("\n")  # Add a line break in the string
            else:
                text, _ = token  # Extract the text from the token
                line_tokens.append(text)  # Append the token's text to the line

        # Add any remaining tokens in the final line
        if line_tokens:
            result.append(" ".join(line_tokens))

        return "".join(result)

    def tokenise(self):
        self.convert_boxes_to_tokens()
        return self.tokens

    def set_boxes(self, boxes):
        self.boxes = boxes

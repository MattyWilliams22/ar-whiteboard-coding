from collections import deque
import numpy as np

def convert_to_tokens(input_data, scale_factor=0.5):
    """
    Convert the input bounding boxes and text into a deque of tokens, detecting lines based on vertical position 
    and scaling the line threshold based on the text height.

    Args:
    input_data (list): The input data in the specified format.
    scale_factor (float): The factor to scale the height for the line threshold.

    Returns:
    deque: A deque containing the tokens and their coordinates.
    """
    tokens = deque()
    lines = []  # List of lines, each line is a list of (text, coordinates)

    # Process each text box
    for item in input_data:
        coordinates = item[0]  # Bounding box (numpy array of shape (4,2))
        text = item[1]         # Extract the text directly (string)

        if text in ["Python Code:", "Output:", "Bottom Left", "Bottom Right", "Top Right", "Top Left", "UNKNOWN"]:
            continue

        # Calculate the height of the bounding box
        height = max(point[1] for point in coordinates) - min(point[1] for point in coordinates)

        # Calculate the vertical center of the bounding box
        top_y = min(point[1] for point in coordinates)
        bottom_y = max(point[1] for point in coordinates)
        center_y = (top_y + bottom_y) / 2  # Vertical center

        # Calculate the dynamic line threshold
        line_threshold = height * scale_factor

        # Find the most appropriate line for the current box
        best_line = None
        best_index = -1
        for i, line in enumerate(lines):
            line_center_y = np.mean([((min(pt[1] for pt in box[1]) + max(pt[1] for pt in box[1])) / 2) for box in line])
            if abs(center_y - line_center_y) <= line_threshold:
                best_line = line
                best_index = i
                break

        if best_line is not None:
            best_line.append((text, coordinates))
        else:
            lines.append([(text, coordinates)])

    # Merge lines if necessary (when lines are too close)
    merged_lines = []
    for line in lines:
        if merged_lines and abs(np.mean([((min(pt[1] for pt in box[1]) + max(pt[1] for pt in box[1])) / 2) for box in line]) -
                                np.mean([((min(pt[1] for pt in box[1]) + max(pt[1] for pt in box[1])) / 2) for box in merged_lines[-1]])) <= line_threshold:
            merged_lines[-1].extend(line)
        else:
            merged_lines.append(line)

    # Sort and append tokens to deque
    for line in merged_lines:
        line.sort(key=lambda item: min(point[0] for point in item[1]))
        for token in line:
            tokens.append(token)
        tokens.append(("LineBreak", []))  # Add LineBreak token between lines

    return tokens

def queue_to_string(tokens):
    """
    Convert the deque of tokens into a human-readable string representation.

    Args:
    tokens (deque): The deque containing tokens and their coordinates.

    Returns:
    str: A formatted string representation of the queue of tokens.
    """
    result = []
    line_tokens = []

    for token in tokens:
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
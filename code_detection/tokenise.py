from collections import deque

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
    current_line = []
    previous_center = -float('inf')  # Initialize to negative infinity to start the first line

    # Process the input data
    for box in input_data:
        for item in box:
            # Extract the coordinates and text
            coordinates = item[0]  # This is the bounding box
            text = item[1][0]      # Extract the text from the tuple

            # Calculate the height of the bounding box
            height = max(point[1] for point in coordinates) - min(point[1] for point in coordinates)

            # Calculate the vertical center of the bounding box
            top_y = min(point[1] for point in coordinates)
            bottom_y = max(point[1] for point in coordinates)
            center_y = (top_y + bottom_y) / 2  # Vertical center

            # Calculate the dynamic line threshold
            line_threshold = height * scale_factor

            # Check if the current box's center is within the line threshold of the previous center
            if abs(center_y - previous_center) <= line_threshold:
                current_line.append((text, coordinates))
            else:
                # If the current line is not empty, sort by x position and add it to tokens
                if current_line:
                    # Sort the current line by the minimum x-coordinate of the bounding box
                    current_line.sort(key=lambda item: min(point[0] for point in item[1]))
                    for token in current_line:
                        tokens.append(token)  # Append all tokens from the current line
                    tokens.append(("LineBreak", []))  # Add LineBreak token

                # Start a new line
                current_line = [(text, coordinates)]
            
            # Update the previous center to the current box's center_y
            previous_center = center_y

        # If there's remaining text in the current line, sort and append it
        if current_line:
            # Sort the current line by the minimum x-coordinate of the bounding box
            current_line.sort(key=lambda item: min(point[0] for point in item[1]))
            for token in current_line:
                tokens.append(token)
            tokens.append(("LineBreak", []))  # Add LineBreak token for the last line

    return tokens

# Corrected input data
input_data = [[
    [[[1414.0, 1120.0], [1719.0, 1131.0], [1715.0, 1256.0], [1410.0, 1244.0]], ('X=4', 0.7917352318763733)],
    [[[1424.0, 1271.0], [1945.0, 1271.0], [1945.0, 1405.0], [1424.0, 1405.0]], ('IFx>5', 0.8555850982666016)],
    [[[1429.0, 1426.0], [2621.0, 1439.0], [2620.0, 1573.0], [1428.0, 1559.0]], ('THEN PRINTGrahaM)', 0.9120262265205383)]
]]

tokens = convert_to_tokens(input_data)

# Print the resulting tokens
for token in tokens:
    print(token)

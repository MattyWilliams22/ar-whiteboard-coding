import numpy as np
from code_detection.markers.keywords import get_keyword

def assemble_code(handwritten_text, bboxs, ids):
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
        
    code = ""
    for corners, text in text_map:
        code += f"{text}\n"

    return code
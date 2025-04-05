import cv2
from output.window import output_to_window
from output.file import output_to_file
from output.projector_app import run_editor
from output.boxes import display_bounding_boxes

def output(output_type: str, image, code, boxes=None):
    if image is None:
        print("No image detected")
        return
    if code is None:
        print("No code detected")
        return
    
    match output_type:
        case "window":
            output_to_window(image, code)
        case "file":
            output_to_file(image, code)
        case "console":
            print(code)
        case "project":
            run_editor(initial_code=code)
        case "projector":
            display_bounding_boxes(boxes, image_size=(1280, 790), aruco_dict_type=cv2.aruco.DICT_6X6_50, marker_size=35, image=image)
        case _:
            print("Invalid output type")
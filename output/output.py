import cv2
from output.window import output_to_window
from output.file import output_to_file
from output.projector_app import run_editor
from output.boxes import display_projection

def output(output_type: str, image, python_code, code_output, boxes=None, error_box=None):
    if image is None:
        print("No image detected")
        return
    if python_code is None:
        print("No code detected")
        return
    
    match output_type:
        # case "window":
        #     output_to_window(image, code)
        # case "file":
        #     output_to_file(image, code)
        # case "console":
        #     print(code)
        # case "project":
        #     run_editor(initial_code=code)
        case "projector":
            return display_projection(boxes, python_code, code_output, input_size=(image.shape[1], image.shape[0]), aruco_dict_type=cv2.aruco.DICT_6X6_50, marker_size=35, output_size=(1280,800), image=None, error_box=error_box)
        case _:
            print("Invalid output type")
            return None
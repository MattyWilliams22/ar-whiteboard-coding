from output.window import output_to_window
from output.file import output_to_file

def output(output_type: str, image, code):
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
        case _:
            print("Invalid output type")
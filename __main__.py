import cv2
from code_detection.detect_code import detect_code
from output.output import output

INPUT_TYPE = "file"

PREPROCESSING_STEPS = []

MARKER_TYPE = "aruco6x6_250"
OCR_TYPE = "paddleocr"

OUTPUT_TYPE = "console"

def get_input(input_type: str):
    if input_type == "file":
        image_path = input("Enter the path to the image: ")
        image = cv2.imread(image_path)
        return image
    elif input_type == "camera":
        cap = cv2.VideoCapture(0)
        _, image = cap.read()
        cap.release()
        return image

def main():
    image = get_input(INPUT_TYPE)

    if image is None:
        print("Error: Unable to load image")
        exit()

    for step in PREPROCESSING_STEPS:
        image = step(image)

    if image is None:
        print("Error: Preprocessing failed")
        exit()

    image, code = detect_code(MARKER_TYPE, OCR_TYPE, image)

    if image is None:
        print("Error: Code detection failed")
        exit()
    if code is None:
        print("Error: Code recognition failed")
        exit()

    output(OUTPUT_TYPE, image, code)

if __name__ == "__main__":
    main()


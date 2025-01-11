import cv2

def output_to_file(image, code):
    with open("output.txt", "w") as f:
        f.write(code)
    
    cv2.imwrite("output.jpg", image)
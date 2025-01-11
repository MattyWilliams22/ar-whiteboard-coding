import cv2

def output_to_window(image, code):
    # Resize the window to fit on screen and make it adjustable
    screen_width = 800
    screen_height = 600
    aspect_ratio = image.shape[1] / image.shape[0]

    if image.shape[1] > screen_width or image.shape[0] > screen_height:
        new_width = screen_width
        new_height = int(new_width / aspect_ratio)
        if new_height > screen_height:
            new_height = screen_height
            new_width = int(new_height * aspect_ratio)
        image = cv2.resize(image, (new_width, new_height))

    cv2.namedWindow('Output Window', cv2.WINDOW_NORMAL)
    cv2.imshow('Output Window', image)
    cv2.resizeWindow('Output Window', screen_width, screen_height)
    cv2.waitKey(0)
    cv2.destroyAllWindows()
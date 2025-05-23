import cv2
import numpy as np

COLOR_RANGES = {
    "dark red": (np.array([0, 150, 50]), np.array([10, 255, 150])),
    "red": (np.array([0, 150, 150]), np.array([10, 255, 255])),
    "orange": (np.array([10, 150, 150]), np.array([25, 255, 255])),
    "yellow": (np.array([25, 100, 100]), np.array([35, 255, 255])),
    "light green": (np.array([35, 100, 100]), np.array([50, 255, 255])),
    "green": (np.array([50, 100, 100]), np.array([70, 255, 255])),
    "light blue": (np.array([80, 100, 100]), np.array([100, 255, 255])),
    "blue": (np.array([100, 150, 50]), np.array([130, 255, 255])),
    "dark blue": (np.array([130, 150, 50]), np.array([150, 255, 255])),
    "purple": (np.array([150, 100, 100]), np.array([170, 255, 255])),
}


def closest_color(hsv_pixel):
    """
    Determines the closest color based on HSV distance.
    :param hsv_pixel: HSV pixel value
    :return: Closest color name
    """
    min_distance = float("inf")
    closest_color_name = None

    for color_name, (lower, upper) in COLOR_RANGES.items():
        mean_hsv = (lower + upper) / 2  # Get the mid HSV value of the color range
        distance = np.linalg.norm(hsv_pixel - mean_hsv)  # Compute Euclidean distance
        if distance < min_distance:
            min_distance = distance
            closest_color_name = color_name

    return closest_color_name


def detect_colored_rectangles(image):
    """
    Detects rectangles of multiple colors in an image and assigns unique IDs (color names).
    :param image: Input image (BGR format)
    :return: Image with detected rectangles outlined, dictionary of detected rectangles with their color names
    """
    hsv = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)
    detected_rectangles = []
    color_ids = []

    for color_name, (lower_color, upper_color) in COLOR_RANGES.items():
        mask = cv2.inRange(hsv, lower_color, upper_color)
        contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

        for contour in contours:
            epsilon = 0.02 * cv2.arcLength(contour, True)
            approx = cv2.approxPolyDP(contour, epsilon, True)

            if len(approx) == 4:  # Ensure it's a rectangle (4 corners)
                detected_rectangles.append(approx)
                color_ids.append(color_name)  # The color name is the ID
                cv2.drawContours(image, [approx], -1, (0, 255, 0), 3)  # Draw rectangle

    return (
        image,
        detected_rectangles,
        np.array(color_ids, dtype=object) if color_ids else np.array([], dtype=object),
    )


def create_rectangle_mask(image, rectangles, buffer=10):
    """
    Create a mask for the detected rectangles.
    :param image: Input image
    :param rectangles: List of detected rectangles (each a 4-point polygon)
    :param buffer: Buffer around the rectangle for the mask
    :return: Mask image
    """
    mask = np.zeros(image.shape[:2], dtype=np.uint8)

    for rect in rectangles:
        # Convert box points to integers
        rect = np.int32(rect)
        rect = np.squeeze(rect, axis=1)
        print(rect.shape)

        # Create a bounding rectangle around the marker (with buffer)
        x_min = np.min(rect[:, 0]) - buffer
        x_max = np.max(rect[:, 0]) + buffer
        y_min = np.min(rect[:, 1]) - buffer
        y_max = np.max(rect[:, 1]) + buffer

        # Ensure the coordinates are within the image bounds
        x_min = np.max(0, x_min)
        x_max = np.min(image.shape[1], x_max)
        y_min = np.max(0, y_min)
        y_max = np.min(image.shape[0], y_max)

        # Convert to integers to ensure proper indexing
        x_min = int(x_min)
        x_max = int(x_max)
        y_min = int(y_min)
        y_max = int(y_max)

        # Fill the region in the mask
        mask[y_min:y_max, x_min:x_max] = 255

    return mask


def draw_rectangle_keywords(image, rectangles, ids):
    """
    Draws color name keywords next to the detected rectangles.
    :param image: The image with detected rectangles
    :param rectangles: List of detected rectangles (each a 4-point polygon)
    :param ids: List of color names for the rectangles (IDs)
    :return: Image with keywords drawn
    """
    for i, rect in enumerate(rectangles):
        box = rect
        color_name = ids[i]

        # Calculate the center of the rectangle
        center_x = int((box[0][0][0] + box[2][0][0]) / 2)
        center_y = int((box[0][0][1] + box[2][0][1]) / 2)

        # Set the offset to place the text near the rectangle
        offset = 20  # Distance to place the text away from the marker
        text_x = center_x + offset
        text_y = center_y

        # Draw the corresponding keyword (color name) near the rectangle
        cv2.putText(
            image,
            color_name,
            (text_x, text_y),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.8,
            (0, 255, 0),
            2,
            cv2.LINE_AA,
        )

    return image


# Example usage
def main():
    image = cv2.imread("image.jpg")

    result_image, rectangles, ids = detect_colored_rectangles(image)

    cv2.imshow("Detected Rectangles", result_image)
    cv2.waitKey(0)
    cv2.destroyAllWindows()


if __name__ == "__main__":
    main()

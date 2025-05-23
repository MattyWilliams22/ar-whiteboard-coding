import cv2
import numpy as np

MARKER_TYPE = cv2.aruco.DICT_4X4_50


# Function to generate and display an ArUco marker for a given ID
def show_aruco_marker(marker_id, dictionary=cv2.aruco.DICT_6X6_250):
    # Define the ArUco dictionary (you can change the dictionary type if needed)
    aruco_dict = cv2.aruco.getPredefinedDictionary(dictionary)

    # Create the marker using the given ID and dictionary
    marker_image = np.zeros((500, 500), dtype=np.uint8)  # Create a blank 500x500 image
    marker_image = cv2.aruco.generateImageMarker(
        aruco_dict, marker_id, 500
    )  # Generate the marker

    # Display the marker
    cv2.imshow(f"ArUco Marker {marker_id}", marker_image)
    cv2.waitKey(0)
    cv2.destroyAllWindows()

    return marker_image


# Example usage
if __name__ == "__main__":
    while True:
        marker_id = input(
            "Enter the ArUco marker ID: "
        )  # Get the marker ID from the user

        if marker_id == "":
            break

        marker_image = show_aruco_marker(int(marker_id), MARKER_TYPE)
        cv2.imwrite(
            f"aruco_marker_{marker_id}.png", marker_image
        )  # Save the marker image to a file

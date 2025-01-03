import cv2
import numpy as np

# Function to generate and display an ArUco marker for a given ID
def show_aruco_marker(marker_id, dictionary=cv2.aruco.DICT_6X6_250):
    # Define the ArUco dictionary (you can change the dictionary type if needed)
    aruco_dict = cv2.aruco.getPredefinedDictionary(dictionary)

    # Create the marker using the given ID and dictionary
    marker_image = np.zeros((500, 500), dtype=np.uint8)  # Create a blank 500x500 image
    marker_image = cv2.aruco.generateImageMarker(aruco_dict, marker_id, 500)  # Generate the marker

    # Display the marker
    cv2.imshow(f'ArUco Marker {marker_id}', marker_image)
    cv2.waitKey(0)
    cv2.destroyAllWindows()

# Example usage
if __name__ == "__main__":
    marker_id = int(input("Enter the ArUco marker ID: "))  # Get the marker ID from the user
    show_aruco_marker(marker_id)

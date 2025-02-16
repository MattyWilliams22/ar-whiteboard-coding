import os
import cv2
from code_detection.detect_code import detect_markers

RESULTS_FILE = "marker_results.txt"

def detect_markers_in_directory(directory, marker_type):
    if not os.path.exists(directory):
        print(f"Error: Directory '{directory}' does not exist.")
        return

    # Clear previous results file
    with open(RESULTS_FILE, "w") as results_file:
        results_file.write("Marker Detection Results:\n")

    for filename in os.listdir(directory):
        if filename.lower().endswith(('.png', '.jpg', '.jpeg')):
            input_path = os.path.join(directory, filename)
            output_path = os.path.join(directory, f"processed_{filename}")
            
            # Load image
            image = cv2.imread(input_path)
            if image is None:
                print(f"Error: Unable to load {filename}")
                continue
            
            # Detect markers
            image, bboxs, ids = detect_markers(marker_type, image)
            if image is None:
                print(f"Error: Marker detection failed for {filename}")
                continue
            
            # Save processed image
            cv2.imwrite(output_path, image)
            
            # Log results
            marker_count = len(bboxs) if bboxs is not None else 0
            with open(RESULTS_FILE, "a") as results_file:
                results_file.write(f"{filename}: {marker_count} / 10 markers detected\n")
            print(f"Processed {filename}: {marker_count} / 10 markers detected")

def main():
    directory = input("Enter the directory containing images: ")
    marker_type = "aruco6x6_250"  # Change as needed
    detect_markers_in_directory(directory, marker_type)

if __name__ == "__main__":
    main()

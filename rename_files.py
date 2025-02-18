import os

# Hardcoded list of 25 names (adjust as needed)
FILE_NAMES = [
    "back_1_across_0", "back_1.5_across_0", "back_2_across_0", "back_2.5_across_0", "back_3_across_0",
    "back_1_across_0.5", "back_1.5_across_0.5", "back_2_across_0.5", "back_2.5_across_0.5", "back_3_across_0.5",
    "back_1_across_1", "back_1.5_across_1", "back_2_across_1", "back_2.5_across_1", "back_3_across_1",
    "back_1_across_1.5", "back_1.5_across_1.5", "back_2_across_1.5", "back_2.5_across_1.5", "back_3_across_1.5"
]

def rename_files_in_directory(directory):
    # Get a list of all files in the directory
    files = sorted(os.listdir(directory))  # Sort alphabetically
    files = [f for f in files if os.path.isfile(os.path.join(directory, f))]  # Exclude directories

    # Check if there are exactly 25 files
    if len(files) != 20:
        print(f"Error: Expected 20 files, but found {len(files)}.")
        return

    # Rename files using the predefined names
    for index, old_name in enumerate(files):
        # Get file extension
        _, ext = os.path.splitext(old_name)
        new_name = f"{FILE_NAMES[index]}{ext}"
        
        # Rename the file
        old_path = os.path.join(directory, old_name)
        new_path = os.path.join(directory, new_name)
        os.rename(old_path, new_path)
        print(f"Renamed: {old_name} → {new_name}")

    print("All files have been renamed successfully.")

if __name__ == "__main__":
    # Ask for directory input
    directory = input("Enter the directory path: ").strip()

    if os.path.exists(directory) and os.path.isdir(directory):
        rename_files_in_directory(directory)
    else:
        print("Error: Directory does not exist.")

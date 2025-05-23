import os
from pillow_heif import open_heif
from PIL import Image


def convert_heic_to_jpg(directory, output_format="JPEG"):
    """
    Recursively converts all .HEIC files in a directory (including subdirectories) to JPG or PNG.

    :param directory: Root folder containing .HEIC files.
    :param output_format: Output format ('JPEG' or 'PNG').
    """
    output_ext = "jpg" if output_format == "JPEG" else "png"

    for root, _, files in os.walk(directory):  # Recursively walk through directories
        for filename in files:
            if filename.lower().endswith(".heic"):
                input_path = os.path.join(root, filename)
                output_path = os.path.join(
                    root, f"{os.path.splitext(filename)[0]}.{output_ext}"
                )

                try:
                    # Open and convert HEIC image
                    heif_image = open_heif(input_path)
                    image = Image.frombytes(
                        heif_image.mode, heif_image.size, heif_image.data
                    )

                    # Save as JPG/PNG
                    image.save(output_path, output_format)
                    print(f"Converted: {input_path} → {output_path}")

                except Exception as e:
                    print(f"Error converting {input_path}: {e}")


if __name__ == "__main__":
    folder_path = input("Enter directory containing HEIC files: ").strip()
    convert_heic_to_jpg(folder_path, output_format="JPEG")  # Change to "PNG" if needed

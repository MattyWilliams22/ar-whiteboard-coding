import re
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.colors import ListedColormap

def parse_results(file_path):
    """
    Reads a file and extracts (back, across, percentage detected) from filenames.
    """
    data = []
    
    with open(file_path, "r") as file:
        for line in file:
            match = re.search(r"back_([\d\.]+)_across_([\d\.]+)\.jpg: (\d+) / 10 markers detected", line)
            if match:
                back = float(match.group(1))   # Distance back (y-axis)
                across = float(match.group(2))  # Distance across (x-axis)
                percentage = (int(match.group(3)) / 10) * 100  # Convert to percentage
                
                data.append((back, across, percentage))
    
    return data

def create_mirrored_grid(data):
    """
    Creates a mirrored grid of values by duplicating the data for both positive and negative across-values.
    """
    mirrored_data = []
    for back, across, percentage in data:
        mirrored_data.append((back, across, percentage))
        mirrored_data.append((back, -across, percentage))  # Mirror the across value
    
    return mirrored_data

def plot_grid(data, save_path=None):
    """
    Plots the heatmap of detected marker percentages with missing values shown as grey.
    The color scale always spans from 0 to 100%.
    If save_path is provided, the image is saved to that location.
    """
    mirrored_data = create_mirrored_grid(data)

    # Extract unique x (across) and y (back) values
    x_values = sorted(set(d[1] for d in mirrored_data))
    y_values = sorted(set(d[0] for d in mirrored_data), reverse=False)  # Keep 0 at the top

    # Create a grid initialized with NaN (so missing values are handled separately)
    grid = np.full((len(y_values), len(x_values)), np.nan)

    # Populate the grid with percentage values
    for back, across, percentage in mirrored_data:
        x_idx = x_values.index(across)
        y_idx = y_values.index(back)
        grid[y_idx, x_idx] = percentage

    # Define the colormap with grey for NaN values
    cmap = plt.cm.get_cmap("hot").copy()
    cmap.set_bad(color="grey")  # Set missing values to grey

    # Plot the heatmap
    plt.figure(figsize=(8, 6))
    plt.imshow(grid, cmap=cmap, interpolation="nearest", aspect="auto", origin="upper", vmin=0, vmax=100)

    # Add labels
    plt.xticks(ticks=np.arange(len(x_values)), labels=x_values, rotation=90)
    plt.yticks(ticks=np.arange(len(y_values)), labels=y_values)
    plt.xlabel("Distance from Centre")
    plt.ylabel("Distance from Whiteboard")
    plt.colorbar(label="Marker Detection Percentage")
    plt.title("Heatmap of Marker Detection")

    # Save to file if a path is specified
    if save_path:
        plt.savefig(save_path, dpi=300, bbox_inches="tight")
        print(f"Heatmap saved to {save_path}")

    # Show the plot
    plt.show()

if __name__ == "__main__":
    file_path = input("Enter the path to the results file: ").strip()
    save_path = input("Enter the path to save the heatmap image (or press Enter to skip saving): ").strip()

    data = parse_results(file_path)
    plot_grid(data, save_path if save_path else None)

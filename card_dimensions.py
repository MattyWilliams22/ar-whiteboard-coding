import numpy as np
import matplotlib.pyplot as plt
import matplotlib.patches as patches

def plot_marker_and_card():
    # Create figure with adjusted bounds
    fig, ax = plt.subplots(figsize=(12, 7))
    ax.set_aspect('equal')
    ax.grid(True, alpha=0.3)
    ax.set_title("ArUco Marker and Tile Geometry", pad=20, fontsize=14)
    ax.set_xlim(-3, 10)
    ax.set_ylim(-2.5, 2)
    ax.set_xlabel("Horizontal axis (units)", fontsize=12)
    ax.set_ylabel("Vertical axis (units)", fontsize=12)

    # -- Elements -- #
    # Marker (2x2 units)
    marker_corners = np.array([[-1, -1], [1, -1], [1, 1], [-1, 1]])
    marker = patches.Polygon(marker_corners, closed=True, fill=False, 
                           color='red', linewidth=3, label='ArUco Marker (2.0×2.0)')
    ax.add_patch(marker)

    # Card (10x2.6 units)
    card_corners = np.array([[-1.3, -1.3], [8.7, -1.3], [8.7, 1.3], [-1.3, 1.3]])
    card = patches.Polygon(card_corners, closed=True, fill=False, 
                         color='blue', linewidth=3, label='Tile (10.0×2.6)')
    ax.add_patch(card)

    # Text position
    ax.plot(4.8, 0, 'go', markersize=10, markeredgewidth=2, label='Text centre point (4.8, 0)')

    # -- Corrected Dimension Lines -- #
    def add_horizontal_dimension(ax, x1, x2, y, text, offset=0.4):
        """For horizontal measurements (width)"""
        y_pos = y - offset
        ax.plot([x1, x2], [y_pos, y_pos], 'k-', linewidth=0.8, alpha=0.7)
        ax.plot([x1, x1], [y_pos-0.1, y_pos+0.1], 'k-', linewidth=0.8, alpha=0.7)
        ax.plot([x2, x2], [y_pos-0.1, y_pos+0.1], 'k-', linewidth=0.8, alpha=0.7)
        ax.text((x1+x2)/2, y_pos-0.25, text, 
               ha='center', va='top', fontsize=10,
               bbox=dict(facecolor='white', alpha=0.8, edgecolor='none', pad=0.3))

    def add_vertical_dimension(ax, x, y1, y2, text, offset=0.4):
        """For vertical measurements (height)"""
        x_pos = x - offset
        ax.plot([x_pos, x_pos], [y1, y2], 'k-', linewidth=0.8, alpha=0.7)
        ax.plot([x_pos-0.1, x_pos+0.1], [y1, y1], 'k-', linewidth=0.8, alpha=0.7)
        ax.plot([x_pos-0.1, x_pos+0.1], [y2, y2], 'k-', linewidth=0.8, alpha=0.7)
        ax.text(x_pos-0.25, (y1+y2)/2, text, 
               ha='right', va='center', fontsize=10, rotation=90,
               bbox=dict(facecolor='white', alpha=0.8, edgecolor='none', pad=0.3))

    # Horizontal dimensions
    add_horizontal_dimension(ax, -1, 1, -1, '2.0', offset=0.6)  # Marker width
    add_horizontal_dimension(ax, -1.3, 8.7, -1.3, '10.0', offset=0.9)  # Card width

    # Vertical dimensions - placed at different x-positions
    add_vertical_dimension(ax, -1.5, -1, 1, '2.0', offset=0)  # Marker height (left)
    add_vertical_dimension(ax, 9.0, -1.3, 1.3, '2.6', offset=0)  # Card height (right)

    # -- Annotations -- #
    # Text position (with arrow)
    ax.annotate('Text Centre Point\n(4.8, 0)', xy=(4.8, 0), xytext=(5.5, 0.8),
               arrowprops=dict(arrowstyle="->", connectionstyle="arc3"),
               ha='left', va='center', fontsize=10,
               bbox=dict(boxstyle="round", facecolor='white', alpha=0.8))

    # Coordinate system
    # ax.arrow(0, 0, 0.5, 0, head_width=0.1, head_length=0.2, fc='k', ec='k', zorder=10)
    # ax.arrow(0, 0, 0, 0.5, head_width=0.1, head_length=0.2, fc='k', ec='k', zorder=10)
    # ax.text(0.55, -0.15, 'X', fontsize=12, weight='bold')
    # ax.text(-0.15, 0.55, 'Y', fontsize=12, weight='bold')

    # -- Legend -- #
    ax.legend(loc='upper left', bbox_to_anchor=(1.02, 1), 
             framealpha=0.9, borderpad=1)

    plt.tight_layout(rect=[0, 0, 0.85, 1])
    plt.savefig('corrected_marker_card_geometry.png', dpi=300, bbox_inches='tight')
    print("Saved as 'corrected_marker_card_geometry.png'")
    plt.close()

plot_marker_and_card()
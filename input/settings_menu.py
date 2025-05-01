import tkinter as tk
from tkinter import ttk
import sounddevice as sd
import cv2
from settings import settings, save_settings

class SettingsMenu:
    def __init__(self, master, camera_preview=None):
        self.master = master
        master.title("Settings")
        master.geometry("600x600")  # Increased size to accommodate more settings

        self.camera_preview = camera_preview
        self.create_widgets()

    def create_widgets(self):
        row = 0

        # Camera device dropdown
        tk.Label(self.master, text="Camera:").grid(row=row, column=0, sticky="w")
        self.cameras = self.get_cameras()
        self.camera_var = tk.IntVar(value=settings["CAMERA"])
        self.camera_dropdown = ttk.Combobox(self.master, 
                                          values=[f"{i}: {name}" for i, name in self.cameras], 
                                          width=50)
        self.camera_dropdown.current(settings["CAMERA"])
        self.camera_dropdown.grid(row=row, column=1, columnspan=4, sticky="ew")
        row += 1

        # Microphone dropdown
        tk.Label(self.master, text="Microphone:").grid(row=row, column=0, sticky="w")
        self.microphones = self.get_microphones()
        self.mic_var = tk.IntVar(value=settings["MICROPHONE"])
        self.mic_dropdown = ttk.Combobox(self.master, 
                                        values=[f"{i}: {name}" for i, name in self.microphones], 
                                        width=50)
        self.mic_dropdown.current(settings["MICROPHONE"])
        self.mic_dropdown.grid(row=row, column=1, columnspan=4, sticky="ew")
        row += 1

        # Camera resolution
        tk.Label(self.master, text="Camera Resolution (Width x Height):").grid(row=row, column=0, sticky="w")
        self.cam_res_width = tk.Entry(self.master, width=7)
        self.cam_res_height = tk.Entry(self.master, width=7)
        self.cam_res_width.insert(0, str(settings["CAMERA_RESOLUTION"][0]))
        self.cam_res_height.insert(0, str(settings["CAMERA_RESOLUTION"][1]))
        tk.Label(self.master, text="X:").grid(row=row, column=1, sticky="e")
        self.cam_res_width.grid(row=row, column=2)
        tk.Label(self.master, text="Y:").grid(row=row, column=3, sticky="e")
        self.cam_res_height.grid(row=row, column=4)
        row += 1

        # Camera FPS
        tk.Label(self.master, text="Camera FPS:").grid(row=row, column=0, sticky="w")
        self.cam_fps = tk.Entry(self.master, width=7)
        self.cam_fps.insert(0, str(settings["CAMERA_FPS"]))
        self.cam_fps.grid(row=row, column=1, sticky="w")
        row += 1

        # Projection resolution
        tk.Label(self.master, text="Projection Resolution (Width x Height):").grid(row=row, column=0, sticky="w")
        self.proj_res_width = tk.Entry(self.master, width=7)
        self.proj_res_height = tk.Entry(self.master, width=7)
        self.proj_res_width.insert(0, str(settings["PROJECTION_RESOLUTION"][0]))
        self.proj_res_height.insert(0, str(settings["PROJECTION_RESOLUTION"][1]))
        tk.Label(self.master, text="X:").grid(row=row, column=1, sticky="e")
        self.proj_res_width.grid(row=row, column=2)
        tk.Label(self.master, text="Y:").grid(row=row, column=3, sticky="e")
        self.proj_res_height.grid(row=row, column=4)
        row += 1

        # Project image checkbox
        self.project_image_var = tk.BooleanVar(value=settings["PROJECT_IMAGE"])
        tk.Checkbutton(self.master, text="Project Image", variable=self.project_image_var).grid(row=row, column=0, sticky="w")
        row += 1

        # Project corners checkbox
        self.project_corners_var = tk.BooleanVar(value=settings["PROJECT_CORNERS"])
        tk.Checkbutton(self.master, text="Project Corner Markers", variable=self.project_corners_var).grid(row=row, column=0, sticky="w")
        row += 1

        # Corner marker size
        tk.Label(self.master, text="Corner Marker Size (px):").grid(row=row, column=0, sticky="w")
        self.corner_marker_size = tk.Entry(self.master, width=7)
        self.corner_marker_size.insert(0, str(settings["CORNER_MARKER_SIZE"]))
        self.corner_marker_size.grid(row=row, column=1, sticky="w")
        row += 1

        # Voice commands checkbox
        self.voice_commands_var = tk.BooleanVar(value=settings["VOICE_COMMANDS"])
        tk.Checkbutton(self.master, text="Enable Voice Commands", variable=self.voice_commands_var).grid(row=row, column=0, sticky="w")
        row += 1

        # Slider for NUM_VALID_IMAGES
        tk.Label(self.master, text="Detection Confidence (Speed <--> Accuracy):").grid(row=row, column=0, sticky="w")
        self.num_valid_images = tk.Scale(self.master, from_=1, to=10, orient=tk.HORIZONTAL)
        self.num_valid_images.set(settings["NUM_VALID_IMAGES"])
        self.num_valid_images.grid(row=row, column=1, columnspan=4, sticky="ew")
        row += 1

        # Save and close button
        tk.Button(self.master, text="Save and Close", command=self.on_save).grid(row=row, column=0, columnspan=5, pady=10)

    def get_cameras(self):
        index = 0
        cameras = []
        while index < 10:
            cap = cv2.VideoCapture(index)
            if cap.read()[0]:
                cameras.append((index, f"Camera {index}"))
                cap.release()
            index += 1
        return cameras

    def get_microphones(self):
        return [(i, dev['name']) for i, dev in enumerate(sd.query_devices()) if dev['max_input_channels'] > 0]

    def on_save(self):
        settings["CAMERA"] = int(self.camera_dropdown.get().split(":")[0])
        settings["MICROPHONE"] = int(self.mic_dropdown.get().split(":")[0])
        settings["CAMERA_RESOLUTION"] = [int(self.cam_res_width.get()), int(self.cam_res_height.get())]
        settings["CAMERA_FPS"] = int(self.cam_fps.get())
        settings["PROJECTION_RESOLUTION"] = [int(self.proj_res_width.get()), int(self.proj_res_height.get())]
        settings["PROJECT_IMAGE"] = self.project_image_var.get()
        settings["PROJECT_CORNERS"] = self.project_corners_var.get()
        settings["CORNER_MARKER_SIZE"] = int(self.corner_marker_size.get())
        settings["VOICE_COMMANDS"] = self.voice_commands_var.get()
        settings["NUM_VALID_IMAGES"] = self.num_valid_images.get()

        save_settings()
        
        # Only update camera preview if it exists
        if self.camera_preview is not None:
            self.camera_preview.update_settings(
                source=settings["CAMERA"],
                resolution=settings["CAMERA_RESOLUTION"],
                fps=settings["CAMERA_FPS"]
            )

        self.master.destroy()

def open_settings_menu(camera_preview=None):
    root = tk.Tk()
    app = SettingsMenu(root, camera_preview)
    root.mainloop()
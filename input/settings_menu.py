import tkinter as tk
from tkinter import ttk
import sounddevice as sd
import cv2
from settings import settings, save_settings

class SettingsMenu:
    def __init__(self, master):
        self.master = master
        master.title("Settings")
        master.geometry("600x400")  # Larger size to accommodate device names

        self.create_widgets()

    def create_widgets(self):
        row = 0

        # Camera device dropdown
        tk.Label(self.master, text="Camera:").grid(row=row, column=0, sticky="w")
        self.cameras = self.get_cameras()
        self.camera_var = tk.IntVar(value=settings["CAMERA"])
        self.camera_dropdown = ttk.Combobox(self.master, values=[f"{i}: {name}" for i, name in self.cameras])
        self.camera_dropdown.current(settings["CAMERA"])
        self.camera_dropdown.grid(row=row, column=1, sticky="ew")
        row += 1

        # Microphone dropdown
        tk.Label(self.master, text="Microphone:").grid(row=row, column=0, sticky="w")
        self.microphones = self.get_microphones()
        self.mic_var = tk.IntVar(value=settings["MICROPHONE"])
        self.mic_dropdown = ttk.Combobox(self.master, values=[f"{i}: {name}" for i, name in self.microphones])
        self.mic_dropdown.current(settings["MICROPHONE"])
        self.mic_dropdown.grid(row=row, column=1, sticky="ew")
        row += 1

        # Camera resolution
        tk.Label(self.master, text="Camera Resolution:").grid(row=row, column=0, sticky="w")
        self.cam_res_width = tk.Entry(self.master)
        self.cam_res_height = tk.Entry(self.master)
        self.cam_res_width.insert(0, str(settings["CAMERA_RESOLUTION"][0]))
        self.cam_res_height.insert(0, str(settings["CAMERA_RESOLUTION"][1]))
        self.cam_res_width.grid(row=row, column=1)
        self.cam_res_height.grid(row=row, column=2)
        row += 1

        # Projection resolution
        tk.Label(self.master, text="Projection Resolution:").grid(row=row, column=0, sticky="w")
        self.proj_res_width = tk.Entry(self.master)
        self.proj_res_height = tk.Entry(self.master)
        self.proj_res_width.insert(0, str(settings["PROJECTION_RESOLUTION"][0]))
        self.proj_res_height.insert(0, str(settings["PROJECTION_RESOLUTION"][1]))
        self.proj_res_width.grid(row=row, column=1)
        self.proj_res_height.grid(row=row, column=2)
        row += 1

        # Slider for NUM_VALID_IMAGES
        tk.Label(self.master, text="Accuracy vs Speed (Images):").grid(row=row, column=0, sticky="w")
        self.num_valid_images = tk.Scale(self.master, from_=1, to=10, orient=tk.HORIZONTAL)
        self.num_valid_images.set(settings["NUM_VALID_IMAGES"])
        self.num_valid_images.grid(row=row, column=1, columnspan=2, sticky="ew")
        row += 1

        # Save and close button
        tk.Button(self.master, text="Save and Close", command=self.on_save).grid(row=row, column=0, columnspan=3, pady=10)

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
        settings["PROJECTION_RESOLUTION"] = [int(self.proj_res_width.get()), int(self.proj_res_height.get())]
        settings["NUM_VALID_IMAGES"] = self.num_valid_images.get()

        save_settings()
        self.master.destroy()


def open_settings_menu():
    root = tk.Tk()
    app = SettingsMenu(root)
    root.mainloop()

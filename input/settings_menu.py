import tkinter as tk
from tkinter import ttk, messagebox
import sounddevice as sd
import cv2
from settings import settings, save_settings

class SettingsMenu:
    def __init__(self, master, camera_preview=None, voice_thread=None):
        self.master = master
        master.title("Settings")

        self.camera_preview = camera_preview
        self.voice_thread = voice_thread
        
        # Create notebook for tabs
        self.notebook = ttk.Notebook(master)
        self.notebook.pack(fill="both", expand=True)
        
        # Create frames for each tab
        self.create_device_settings_tab()
        self.create_helper_code_tab()
        
        # Configure window sizing
        master.update_idletasks()
        master.minsize(600, 500)
        master.maxsize(800, 700)

    def create_device_settings_tab(self):
        """Tab for hardware and display settings"""
        self.device_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.device_frame, text="Device Settings")
        
        main_frame = ttk.Frame(self.device_frame, padding="10")
        main_frame.pack(fill="both", expand=True)
        
        row = 0
        
        # Camera device dropdown
        ttk.Label(main_frame, text="Camera:").grid(row=row, column=0, sticky="w", pady=2)
        self.cameras = self.get_cameras()
        self.camera_dropdown = ttk.Combobox(main_frame, 
                                          values=[f"{i}: {name}" for i, name, _, _ in self.cameras], 
                                          width=50)
        self.camera_dropdown.current(settings["CAMERA"])
        self.camera_dropdown.grid(row=row, column=1, columnspan=4, sticky="ew", pady=2)
        row += 1

        # Microphone dropdown
        ttk.Label(main_frame, text="Microphone:").grid(row=row, column=0, sticky="w", pady=2)
        self.microphones = self.get_microphones()
        self.mic_dropdown = ttk.Combobox(main_frame, 
                                        values=[f"{i}: {name}" for i, name in self.microphones], 
                                        width=50)
        self.mic_dropdown.current(settings["MICROPHONE"])
        self.mic_dropdown.grid(row=row, column=1, columnspan=4, sticky="ew", pady=2)
        row += 1

        # Camera resolution
        ttk.Label(main_frame, text="Camera Resolution:").grid(row=row, column=0, sticky="w", pady=2)
        self.cam_res_frame = ttk.Frame(main_frame)
        self.cam_res_frame.grid(row=row, column=1, columnspan=4, sticky="w", pady=2)
        
        vcmd = (self.master.register(self.validate_resolution), '%P', 'camera')
        
        self.cam_res_width = ttk.Entry(self.cam_res_frame, width=7, validate="key", validatecommand=vcmd)
        self.cam_res_width.insert(0, str(settings["CAMERA_RESOLUTION"][0]))
        self.cam_res_width.pack(side="left")
        
        ttk.Label(self.cam_res_frame, text="×").pack(side="left", padx=2)
        
        self.cam_res_height = ttk.Entry(self.cam_res_frame, width=7, validate="key", validatecommand=vcmd)
        self.cam_res_height.insert(0, str(settings["CAMERA_RESOLUTION"][1]))
        self.cam_res_height.pack(side="left")
        
        self.max_res_label = ttk.Label(main_frame, text="", foreground="gray")
        self.max_res_label.grid(row=row, column=2, sticky="e")
        row += 1

        # Camera FPS
        ttk.Label(main_frame, text="Camera FPS:").grid(row=row, column=0, sticky="w", pady=2)
        self.cam_fps = ttk.Entry(main_frame, width=7)
        self.cam_fps.insert(0, str(settings["CAMERA_FPS"]))
        self.cam_fps.grid(row=row, column=1, sticky="w", pady=2)
        row += 1

        # Projection resolution
        ttk.Label(main_frame, text="Projection Resolution:").grid(row=row, column=0, sticky="w", pady=2)
        self.proj_res_frame = ttk.Frame(main_frame)
        self.proj_res_frame.grid(row=row, column=1, columnspan=4, sticky="w", pady=2)
        
        self.proj_res_width = ttk.Entry(self.proj_res_frame, width=7)
        self.proj_res_width.insert(0, str(settings["PROJECTION_RESOLUTION"][0]))
        self.proj_res_width.pack(side="left")
        ttk.Label(self.proj_res_frame, text="×").pack(side="left", padx=2)
        self.proj_res_height = ttk.Entry(self.proj_res_frame, width=7)
        self.proj_res_height.insert(0, str(settings["PROJECTION_RESOLUTION"][1]))
        self.proj_res_height.pack(side="left")
        row += 1

        # Checkboxes
        self.project_image_var = tk.BooleanVar(value=settings["PROJECT_IMAGE"])
        ttk.Checkbutton(main_frame, text="Project Image", variable=self.project_image_var).grid(row=row, column=0, sticky="w", pady=2)
        row += 1

        self.project_corners_var = tk.BooleanVar(value=settings["PROJECT_CORNERS"])
        ttk.Checkbutton(main_frame, text="Project Corner Markers", variable=self.project_corners_var).grid(row=row, column=0, sticky="w", pady=2)
        row += 1

        self.voice_commands_var = tk.BooleanVar(value=settings["VOICE_COMMANDS"])
        ttk.Checkbutton(main_frame, text="Enable Voice Commands", variable=self.voice_commands_var).grid(row=row, column=0, sticky="w", pady=2)
        row += 1

        # Corner marker size
        ttk.Label(main_frame, text="Corner Marker Size:").grid(row=row, column=0, sticky="w", pady=2)
        self.corner_marker_size = ttk.Entry(main_frame, width=7)
        self.corner_marker_size.insert(0, str(settings["CORNER_MARKER_SIZE"]))
        self.corner_marker_size.grid(row=row, column=1, sticky="w", pady=2)
        row += 1

        # Slider
        ttk.Label(main_frame, text="Detection Confidence:").grid(row=row, column=0, sticky="w", pady=2)
        self.num_valid_images = tk.Scale(
            main_frame,
            from_=1,
            to=10,
            orient="horizontal",
            showvalue=1,
            tickinterval=1,
            resolution=1,
            length=400
        )
        self.num_valid_images.set(settings["NUM_VALID_IMAGES"])
        self.num_valid_images.grid(row=row, column=1, columnspan=4, sticky="ew", pady=2)
        row += 1

    def create_helper_code_tab(self):
        """Tab for helper code editing"""
        self.helper_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.helper_frame, text="Helper Code")
        
        # Instructions
        instructions = ttk.Label(
            self.helper_frame,
            text="Write helper functions/tests here. Use #INSERT to specify where whiteboard code should be placed.",
            wraplength=550,
            padding=10
        )
        instructions.pack()
        
        # Code editor
        self.helper_text = tk.Text(
            self.helper_frame,
            width=80,
            height=25,
            wrap="word",
            font=("Consolas", 10),
            padx=10,
            pady=10
        )
        self.helper_text.insert("1.0", settings["HELPER_CODE"])
        
        # Add scrollbar
        scrollbar = ttk.Scrollbar(self.helper_frame, command=self.helper_text.yview)
        self.helper_text.configure(yscrollcommand=scrollbar.set)
        
        # Pack widgets
        self.helper_text.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        
        # Save button at bottom
        save_btn = ttk.Button(
            self.helper_frame,
            text="Save All Settings",
            command=self.on_save
        )
        save_btn.pack(pady=10)

    def update_max_resolution_label(self):
        """Update the label showing max supported resolution"""
        cap = cv2.VideoCapture(settings["CAMERA"])
        if cap.isOpened():
            max_width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
            max_height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
            cap.release()
            self.max_res_label.config(text=f"Max: {max_width}x{max_height}")

    def get_cameras(self):
        """Returns list of available cameras with their max resolutions"""
        index = 0
        cameras = []
        
        while index < 10:  # Check first 10 camera indices
            cap = cv2.VideoCapture(index)
            if cap.isOpened():
                # Get max supported resolution
                max_res = self._get_max_camera_resolution(cap)
                cap.release()
                
                if max_res:
                    width, height = max_res
                    # Generate descriptive name
                    name = self._generate_camera_name(index, width, height)
                    cameras.append((index, name, width, height))  # Store with max res
            index += 1
    
        return cameras if cameras else [(0, "Default Camera", 640, 480)]  # Fallback

    def _get_max_camera_resolution(self, cap):
        """Determine maximum supported resolution for an opened camera"""
        test_resolutions = [
            (3840, 2160),  # 4K
            (2560, 1440),  # 1440p
            (1920, 1080),  # 1080p
            (1280, 720),   # 720p
            (640, 480)     # 480p
        ]
        
        for w, h in test_resolutions:
            cap.set(cv2.CAP_PROP_FRAME_WIDTH, w)
            cap.set(cv2.CAP_PROP_FRAME_HEIGHT, h)
            actual_w = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
            actual_h = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
            
            if actual_w >= w and actual_h >= h:
                return (actual_w, actual_h)
        return None

    def _generate_camera_name(self, index, width, height):
        """Generate human-readable camera name with resolution info"""
        res_map = {
            (3840, 2160): "4K",
            (2560, 1440): "1440p",
            (1920, 1080): "1080p",
            (1280, 720): "720p",
            (640, 480): "SD"
        }
        res_description = res_map.get((width, height), f"{width}x{height}")
        return f"Camera {index} ({res_description})"

    def get_microphones(self):
        return [(i, dev['name']) for i, dev in enumerate(sd.query_devices()) if dev['max_input_channels'] > 0]
    
    def validate_resolution(self, new_value, res_type):
        """Validate resolution entries and check against camera max"""
        if not new_value.isdigit():
            return False
        return True

    def on_save(self):
        """Save all settings including helper code"""
        try:
            # Validate resolution first
            req_width = int(self.cam_res_width.get())
            req_height = int(self.cam_res_height.get())
            
            cap = cv2.VideoCapture(settings["CAMERA"])
            if cap.isOpened():
                cap.set(cv2.CAP_PROP_FRAME_WIDTH, req_width)
                cap.set(cv2.CAP_PROP_FRAME_HEIGHT, req_height)
                actual_w = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
                actual_h = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
                cap.release()
                
                if (req_width, req_height) != (actual_w, actual_h):
                    messagebox.showwarning(
                        "Resolution Adjusted",
                        f"Camera adjusted to {actual_w}x{actual_h}\n"
                        f"(Requested {req_width}x{req_height})"
                    )
                    self.cam_res._width.set(actual_w)
                    self.cam_res._height.set(actual_h)

        except ValueError:
            messagebox.showerror("Error", "Please enter valid numbers for resolution")
            return
    
        # Save device settings
        settings.update({
            "CAMERA": int(self.camera_dropdown.get().split(":")[0]),
            "MICROPHONE": int(self.mic_dropdown.get().split(":")[0]),
            "CAMERA_RESOLUTION": [int(self.cam_res_width.get()), int(self.cam_res_height.get())],
            "CAMERA_FPS": int(self.cam_fps.get()),
            "PROJECTION_RESOLUTION": [int(self.proj_res_width.get()), int(self.proj_res_height.get())],
            "PROJECT_IMAGE": self.project_image_var.get(),
            "PROJECT_CORNERS": self.project_corners_var.get(),
            "CORNER_MARKER_SIZE": int(self.corner_marker_size.get()),
            "VOICE_COMMANDS": self.voice_commands_var.get(),
            "NUM_VALID_IMAGES": self.num_valid_images.get(),
            "HELPER_CODE": self.helper_text.get("1.0", "end-1c")
        })

        save_settings()
        
        if hasattr(self, 'camera_preview') and self.camera_preview is not None:
            self.camera_preview.update_settings(
                source=settings["CAMERA"],
                resolution=settings["CAMERA_RESOLUTION"],
                fps=settings["CAMERA_FPS"]
            )

        if hasattr(self, 'voice_thread') and self.voice_thread is not None:
            self.voice_thread.update_settings()

        self.master.destroy()

def open_settings_menu(camera_preview=None):
    root = tk.Tk()
    app = SettingsMenu(root, camera_preview)
    root.mainloop()
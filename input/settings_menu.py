import queue
from threading import Thread
import threading
import tkinter as tk
from tkinter import ttk, messagebox
import sounddevice as sd
import cv2
from settings import settings, save_settings
from input.voice_commands import VoiceCommandThread
import os
import json
import time

class SettingsMenu:
    def __init__(self, master, camera_preview=None, voice_thread=None):
        self.master = master
        master.title("Settings")
        self.camera_preview = camera_preview
        self.voice_thread = voice_thread
        self.camera_cache_file = "camera_cache.json"
        self.cache_valid_for = 86400  # 24 hours in seconds
        
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
        
        # Initialize device lists
        self.cameras = []
        self.microphones = []
        
        # Load cached cameras immediately
        cached_cameras = self.load_cached_cameras()
        if cached_cameras:
            self.cameras = cached_cameras
            self.update_camera_dropdown()
        
        # Start device detection in background
        self.device_queue = queue.Queue()
        self.start_device_detection()
        self.master.after(100, self.process_device_queue)

    def load_cached_cameras(self):
        """Load cameras from cache if valid"""
        try:
            if os.path.exists(self.camera_cache_file):
                mod_time = os.path.getmtime(self.camera_cache_file)
                if time.time() - mod_time < self.cache_valid_for:
                    with open(self.camera_cache_file, 'r') as f:
                        cameras = json.load(f)
                        if isinstance(cameras, list) and len(cameras) > 0:
                            # Convert cached tuples back to lists (JSON converts tuples to lists)
                            return [tuple(cam) for cam in cameras]
        except Exception as e:
            print(f"Error loading camera cache: {e}")
        return None

    def save_camera_cache(self, cameras):
        """Save detected cameras to cache"""
        try:
            with open(self.camera_cache_file, 'w') as f:
                json.dump(cameras, f)
        except Exception as e:
            print(f"Error saving camera cache: {e}")

    def start_device_detection(self):
        """Start camera and microphone detection in background threads"""
        # Only detect cameras if cache is empty or we need to verify
        if not self.cameras or self.should_verify_cache():
            threading.Thread(target=self.detect_cameras, daemon=True).start()
        
        # Always detect microphones (they can change more frequently)
        threading.Thread(target=self.detect_microphones, daemon=True).start()

    def should_verify_cache(self):
        """Check if we should verify cached cameras"""
        if not os.path.exists(self.camera_cache_file):
            return True
        
        cache_age = time.time() - os.path.getmtime(self.camera_cache_file)
        return cache_age > 3600  # Verify if cache is older than 1 hour

    def detect_cameras(self):
        """Detect available cameras with max resolution (using your original code)"""
        index = 0
        cameras = []
        consecutive_failures = 0
        max_consecutive_failures = 2
        
        while consecutive_failures < max_consecutive_failures:
            cap = cv2.VideoCapture(index)
            if cap.isOpened():
                consecutive_failures = 0
                max_res = self._get_max_camera_resolution(cap)
                cap.release()
                
                if max_res:
                    width, height = max_res
                    name = self._generate_camera_name(index, width, height)
                    cameras.append((index, name, width, height))
            else:
                consecutive_failures += 1
                
            index += 1
        
        if not cameras:
            cameras = [(0, "Default Camera", 640, 480)]
        
        # Save to cache
        self.save_camera_cache(cameras)
        
        # Update UI if different from cache
        if cameras != self.cameras:
            self.device_queue.put(("camera", cameras))

    def process_device_queue(self):
        """Process results from device detection threads"""
        try:
            while True:
                device_type, data = self.device_queue.get_nowait()
                if device_type == "camera":
                    self.cameras = data
                    self.update_camera_dropdown()
                elif device_type == "microphone":
                    self.microphones = data
                    self.update_microphone_dropdown()
        except queue.Empty:
            pass
        self.master.after(100, self.process_device_queue)

    def start_device_detection(self):
        """Start camera and microphone detection in background threads"""
        # Camera detection
        threading.Thread(target=self.detect_cameras, daemon=True).start()
        
        # Microphone detection
        threading.Thread(target=self.detect_microphones, daemon=True).start()

    def _get_max_camera_resolution(self, cap):
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
        res_map = {
            (3840, 2160): "4K",
            (2560, 1440): "1440p",
            (1920, 1080): "1080p",
            (1280, 720): "720p",
            (640, 480): "SD"
        }
        res_description = res_map.get((width, height), f"{width}x{height}")
        return f"Camera {index} ({res_description})"

    def detect_microphones(self):
        """Detect available microphones in background thread"""
        mics = []
        try:
            mics = [(i, dev['name']) for i, dev in enumerate(sd.query_devices()) 
                   if dev['max_input_channels'] > 0]
        except:
            mics = [(0, "Default Microphone")]
        
        self.device_queue.put(("microphone", mics))

    def update_camera_dropdown(self):
        """Update camera dropdown with detected cameras"""
        if not self.cameras:
            return
            
        self.camera_dropdown['values'] = [f"{i}: {name}" for i, name, _, _ in self.cameras]
        
        # Set current selection from settings
        current_cam = settings.get("CAMERA", 0)
        valid_indices = [i for i, _, _, _ in self.cameras]
        
        if current_cam in valid_indices:
            idx = valid_indices.index(current_cam)
            self.camera_dropdown.current(idx)
        else:
            self.camera_dropdown.current(0)
        
        # Update resolution fields with current camera's max resolution
        self.update_resolution_fields()

    def update_resolution_fields(self):
        """Update resolution fields based on selected camera"""
        if not self.cameras:
            return
            
        selected_idx = self.camera_dropdown.current()
        if selected_idx < 0 or selected_idx >= len(self.cameras):
            return
            
        _, _, max_width, max_height = self.cameras[selected_idx]
        
        # Get current settings or use max resolution
        current_width = settings.get("CAMERA_RESOLUTION", [max_width, max_height])[0]
        current_height = settings.get("CAMERA_RESOLUTION", [max_width, max_height])[1]
        
        # Update UI field
        self.max_res_label.config(text=f"Max: {max_width}x{max_height}")

    def update_microphone_dropdown(self):
        """Update microphone dropdown with detected devices"""
        if not self.microphones:
            return
            
        self.mic_dropdown['values'] = [f"{i}: {name}" for i, name in self.microphones]
        
        # Set current selection from settings
        current_mic = settings.get("MICROPHONE", 0)
        valid_indices = [i for i, _ in self.microphones]
        
        if current_mic in valid_indices:
            idx = valid_indices.index(current_mic)
            self.mic_dropdown.current(idx)
        else:
            self.mic_dropdown.current(0)

    def create_device_settings_tab(self):
        """Tab for hardware and display settings"""
        self.device_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.device_frame, text="Device Settings")
        
        main_frame = ttk.Frame(self.device_frame, padding="10")
        main_frame.pack(fill="both", expand=True)
        
        row = 0
        
        # Camera device dropdown (initialize empty)
        ttk.Label(main_frame, text="Camera:").grid(row=row, column=0, sticky="w", pady=2)
        self.camera_dropdown = ttk.Combobox(main_frame, values=["Detecting cameras..."], width=50)
        self.camera_dropdown.grid(row=row, column=1, columnspan=4, sticky="ew", pady=2)
        self.camera_dropdown.bind("<<ComboboxSelected>>", lambda e: self.update_resolution_fields())
        row += 1

        # Camera resolution (initialize empty)
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
        
        self.max_res_label = ttk.Label(main_frame, text="Max: Detecting...", foreground="gray")
        self.max_res_label.grid(row=row, column=2, sticky="e")
        row += 1

        # Camera FPS
        ttk.Label(main_frame, text="Camera FPS:").grid(row=row, column=0, sticky="w", pady=2)
        self.cam_fps = ttk.Entry(main_frame, width=7)
        self.cam_fps.insert(0, str(settings["CAMERA_FPS"]))
        self.cam_fps.grid(row=row, column=1, sticky="w", pady=2)
        row += 1

        # Voice commands checkbox
        self.voice_commands_var = tk.BooleanVar(value=settings["VOICE_COMMANDS"])
        ttk.Checkbutton(main_frame, text="Enable Voice Commands", variable=self.voice_commands_var).grid(row=row, column=0, sticky="w", pady=2)
        row += 1

        # Microphone dropdown
        ttk.Label(main_frame, text="Microphone:").grid(row=row, column=0, sticky="w", pady=2)
        self.microphones = self.get_microphones()
        self.mic_dropdown = ttk.Combobox(main_frame, 
                                        values=[f"{i}: {name}" for i, name in self.microphones], 
                                        width=50)
        if settings["MICROPHONE"] < len(self.microphones):
            self.mic_dropdown.current(settings["MICROPHONE"])
        else:
            self.mic_dropdown.current(0)
        self.mic_dropdown.grid(row=row, column=1, columnspan=4, sticky="ew", pady=2)
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

        # Project image checkbox
        self.project_image_var = tk.BooleanVar(value=settings["PROJECT_IMAGE"])
        ttk.Checkbutton(main_frame, text="Project Image", variable=self.project_image_var).grid(row=row, column=0, sticky="w", pady=2)
        row += 1

        # Project corners checkbox
        self.project_corners_var = tk.BooleanVar(value=settings["PROJECT_CORNERS"])
        ttk.Checkbutton(main_frame, text="Project Corner Markers", variable=self.project_corners_var).grid(row=row, column=0, sticky="w", pady=2)
        row += 1

        # Corner marker size
        ttk.Label(main_frame, text="Corner Marker Size:").grid(row=row, column=0, sticky="w", pady=2)
        self.corner_marker_size = ttk.Entry(main_frame, width=7)
        self.corner_marker_size.insert(0, str(settings["CORNER_MARKER_SIZE"]))
        self.corner_marker_size.grid(row=row, column=1, sticky="w", pady=2)
        row += 1

        # Detection Confidence Slider
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

        # Code Save Path
        ttk.Label(main_frame, text="Code Save Path:").grid(row=row, column=0, sticky="w", pady=2)
        self.code_save_path = ttk.Entry(main_frame, width=50)
        self.code_save_path.insert(0, settings["CODE_SAVE_PATH"])
        self.code_save_path.grid(row=row, column=1, columnspan=4, sticky="ew", pady=2)
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

    def on_camera_selected(self, event):
        """When camera is selected, update resolution fields"""
        if hasattr(self, 'cameras') and self.cameras:
            selected_idx = self.camera_dropdown.current()
            if 0 <= selected_idx < len(self.cameras):
                _, _, width, height = self.cameras[selected_idx]
                self.max_res_label.config(text=f"Max: {width}x{height}")

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
            # Store previous voice commands state
            was_voice_enabled = settings["VOICE_COMMANDS"]
            new_voice_enabled = self.voice_commands_var.get()

            # Get requested resolution
            req_width = int(self.cam_res_width.get())
            req_height = int(self.cam_res_height.get())
            
            # Get selected camera's max resolution
            cam_idx = self.camera_dropdown.current()
            if cam_idx >= 0 and len(self.cameras) > cam_idx:
                _, _, max_w, max_h = self.cameras[cam_idx]
                
                # Check and cap if needed
                capped = False
                if req_width > max_w:
                    req_width = max_w
                    capped = True
                if req_height > max_h:
                    req_height = max_h
                    capped = True
                    
                # Notify user if values were capped
                if capped:
                    messagebox.showinfo(
                        "Resolution Capped",
                        f"Resolution was capped to {req_width}x{req_height}\n"
                        f"to match camera's maximum supported resolution"
                    )
                    
                    # Update the UI fields to show capped values
                    self.cam_res_width.delete(0, tk.END)
                    self.cam_res_width.insert(0, str(req_width))
                    self.cam_res_height.delete(0, tk.END)
                    self.cam_res_height.insert(0, str(req_height))

            # Save device settings
            settings.update({
                "CAMERA": int(self.camera_dropdown.get().split(":")[0]),
                "MICROPHONE": int(self.mic_dropdown.get().split(":")[0]),
                "CAMERA_RESOLUTION": [req_width, req_height],
                "CAMERA_FPS": int(self.cam_fps.get()),
                "PROJECTION_RESOLUTION": [int(self.proj_res_width.get()), int(self.proj_res_height.get())],
                "PROJECT_IMAGE": self.project_image_var.get(),
                "PROJECT_CORNERS": self.project_corners_var.get(),
                "CORNER_MARKER_SIZE": int(self.corner_marker_size.get()),
                "VOICE_COMMANDS": self.voice_commands_var.get(),
                "NUM_VALID_IMAGES": self.num_valid_images.get(),
                "HELPER_CODE": self.helper_text.get("1.0", "end-1c"),
                "CODE_SAVE_PATH": self.code_save_path.get()
            })

            save_settings()
            
            if hasattr(self, 'camera_preview') and self.camera_preview is not None:
                self.camera_preview.update_settings(
                    source=settings["CAMERA"],
                    resolution=settings["CAMERA_RESOLUTION"],
                    fps=settings["CAMERA_FPS"]
                )

            if hasattr(self, 'voice_thread') and self.voice_thread is not None:
                if new_voice_enabled != was_voice_enabled:
                    if new_voice_enabled:
                        self.voice_thread.set_active()
                    else:
                        self.voice_thread.set_inactive()
                    self.voice_thread.update_settings()
                else:
                    self.voice_thread.update_settings()

            self.master.destroy()

        except ValueError:
            messagebox.showerror("Error", "Please enter valid numbers for resolution")
            return

def open_settings_menu(camera_preview=None):
    root = tk.Tk()
    app = SettingsMenu(root, camera_preview)
    root.mainloop()
import json
import os

SETTINGS_FILE = "settings.json"

# Default settings
default_settings = {
    "PROJECT_IMAGE": False,
    "NUM_VALID_IMAGES": 3,
    "CAMERA": 0,
    "CAMERA_RESOLUTION": [1920, 1080],
    "CAMERA_FPS": 10,
    "VOICE_COMMANDS": False,
    "HAND_GESTURES": True,
    "MICROPHONE": 0,
    "PROJECTION_RESOLUTION": [1280, 790],
    "PROJECT_CORNERS": True,
    "CORNER_MARKER_SIZE": 35,
    "HELPER_CODE": "# Write helper functions here\n# Whiteboard code will be inserted at #INSERT\n#INSERT"
}

settings = default_settings.copy()

def load_settings():
    if os.path.exists(SETTINGS_FILE):
        with open(SETTINGS_FILE, "r") as f:
            loaded = json.load(f)
            settings.update(loaded)

def save_settings():
    with open(SETTINGS_FILE, "w") as f:
        json.dump(settings, f, indent=4)

# Load settings on import
load_settings()

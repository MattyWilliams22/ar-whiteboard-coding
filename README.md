# Augmented Reality Whiteboard Coding

> This is the code repository for my BEng Individual Project at Imperial College London.

---

## Overview

Code is often written on a whiteboard during school lessons, lectures or job interviews. However, every time you want to run the code, you have to manually copy the code onto a computer, which is very time-consuming.

This system provides a way to detect code written on a whiteboard using computer vision, and use a projector to overlay code output back onto the whiteboard. Also, the system can be controlled remotely using voice commands.

---

## My Contributions

- Perspective Transformation (/preprocessing/preprocessor.py)
- Fiducial markers to represent keywords (/code_detection/markers/)
- Minimalistic Language Parsing (/code_detection/parse_code.py)
- Consensus Box Aggregation (/code_detection/detector.py)
- Projector Overlay (/output/projector.py)

---

## Project Structure

```text
ar-whiteboard-coding/
|
├── code_detection/        # Detection, Tokenisation and Parsing of whiteboard code
├── execution/             # Execution in a Docker Sandbox
├── fsm/                   # Finite State Machine
├── input/                 # Input Methods and Settings Menu
├── output/                # Projector Overlay
├── preprocessing/         # Perspective Transformation
├── __main__.py            # Main Program Loop
├── README.md
├── requirements.txt
└── settings.py            # Loading and Saving Settings
```

## Installation

To run this project, you’ll need:

- **Python 3.10+**
- **Docker Desktop** installed and running
- A **camera or webcam** connected to your computer
- A **projector** connected to your computer

Steps to install and set up:

```bash
# Clone this repository
git clone https://github.com/MattyWilliams22/ar-whiteboard-coding.git

# Navigate into the project directory
cd ar-whiteboard-coding

# Install Python dependencies
pip install -r requirements.txt
```

## Usage
Make sure you have completed the Installation steps and Docker Desktop is running before proceeding.

```bash
# Run the program
python __main__.py
```

After launching:

1. Adjust the settings in the settings menu, then press save.
2. Make the projection window full screen on the projector's display, and direct the projector at the whiteboard.
3. Use the camera preview window to ensure the camera clearly captures the illuminated region of the whiteboard.
4. Write code on the whiteboard.
5. Trigger code execution by speaking "Jarvis Execute" with a microphone enabled, or pressing the 'R' key on the keyboard.

## Author

Matty Williams - https://github.com/MattyWilliams22
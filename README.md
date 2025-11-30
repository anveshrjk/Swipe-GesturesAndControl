# Swipe – Gesture-Based Desktop Control System

Swipe is a Python-based gesture recognition system that enables hands-free control of desktop functions using real-time hand tracking. It uses MediaPipe for hand landmark detection, OpenCV for frame processing, and a modular action layer for executing system-level operations. Swipe is designed to provide an efficient, extensible, and configurable gesture automation environment.

---

## Overview

Swipe captures webcam input, identifies predefined hand gestures, and maps them to user actions such as media control, volume adjustment, window management, screen capture, and application launching. The system is modular, configurable, and intended for future expansion with additional gestures and customizable behavior.

---

## Features

### Gesture Actions
- **OK gesture**: Play/Pause multimedia.
- **Two-finger V gesture**: Close the currently active application.
- **Shaka gesture**: Capture a fullscreen screenshot.
- **All fingers upward**: Increase system volume.
- **All fingers downward**: Decrease system volume.
- **"Yo" gesture**: Launch a user-defined application.

### System Capabilities
- Real-time hand tracking using MediaPipe.
- Configurable gesture-to-action mapping.
- Modular architecture for adding new gestures or actions.
- Automatic logging and screenshot storage.
- Quick-launch application configuration.

---

## Project Structure

swipe/  
│── src/  
│ ├── main.py # Application entry point  
│ ├── camera.py # Webcam management  
│ ├── gestures.py # Gesture definitions  
│ ├── processing.py # Gesture classifier and processing pipeline  
│ ├── actions.py # System actions (volume, close app, play/pause, launch app, screenshot)  
│ ├── ui.py # UI and settings management  
│ ├── utils.py # Utilities and helpers  
│ ├── config.json # Application configuration  
│ ├── settings.json # User settings  
│ ├── app_launcher.json # List of user-defined quick-launch apps  
│ ├── logs/ # Log files  
│ └── screenshots/ # Saved screenshots  
│  
├── requirements.txt  
├── README.md  
└── .gitignore  

---

## Installation

### 1. Clone the repository
```bash
git clone https://github.com/anveshrjk/Swipe-GesturesAndControl.git

cd Swipe-GesturesAndControl

```

### 2. Install requirements

Python 3.10 or later is recommended.
```
pip install -r requirements.txt
```

### 3. Start Swipe
```python src/main.py```

---

## Configuration

### Quick-Launch Applications

Swipe allows the user to assign applications that can be opened via the "yo" gesture.
Edit app_launcher.json:
```
{
    "apps": [
        {
            "title": "Chrome",
            "path": "C:/Program Files/Google/Chrome/Application/chrome.exe"
        }
    ]
}
```
---

## Settings and Behavior
- settings.json controls user preferences and runtime behavior.

- config.json stores core configuration values (thresholds, detection parameters, etc.).

---

## Extending Swipe
Swipe is designed to support new gestures and actions without modifying the entire system.

### To add a new gesture:

- Define the gesture in gestures.py.

- Add its classification logic in processing.py.

- Map the gesture to a function in actions.py.

- Add an optional user setting if needed.

The modular structure ensures isolated updates and maintainable scalability.

--- 

## Logs and Diagnostics

- Gesture logs are stored under src/logs/.

- Screenshots captured through gestures are saved in src/screenshots/.

- These resources assist with debugging, behavior tracking, and feature development.

---

## Roadmap

- Planned improvements include:

- Custom gesture training using collected samples.

- Additional system integrations.

- Multi-hand gesture recognition.

- Expanded UI with advanced configuration options.

- Support for Linux and macOS actions.

---

## Contribution

- Contributions are welcome.

---
## Guidelines:

- Follow PEP 8 coding standards.

- Avoid hard-coded system paths.

- Document new gestures or actions.

- Include screenshots or logs when reporting issues.

---

## License

- This project is available under the MIT License.
- Users may modify and redistribute the software with appropriate attribution.
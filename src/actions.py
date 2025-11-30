# actions.py
"""
Simple actions for gesture control
"""

import time
import pyautogui
import subprocess
import os
from pathlib import Path
import json

# Windows API for closing window
try:
    import win32gui
    import win32con
    import win32api
    WIN32_AVAILABLE = True
except Exception:
    WIN32_AVAILABLE = False

# Volume control
try:
    from pycaw.pycaw import AudioUtilities, IAudioEndpointVolume
    from ctypes import POINTER, cast
    import comtypes
    PYCAW_AVAILABLE = True
except Exception:
    PYCAW_AVAILABLE = False

# Screenshot folder
SS_FOLDER = Path.cwd() / "screenshots"
SS_FOLDER.mkdir(parents=True, exist_ok=True)

# Application launcher config
APP_CONFIG_FILE = Path.cwd() / "app_launcher.json"

def load_app_config():
    """Load application launcher configuration"""
    if APP_CONFIG_FILE.exists():
        try:
            with open(APP_CONFIG_FILE, 'r') as f:
                return json.load(f)
        except Exception:
            return {"app_path": ""}
    return {"app_path": ""}

def save_app_config(app_path):
    """Save application launcher configuration"""
    try:
        with open(APP_CONFIG_FILE, 'w') as f:
            json.dump({"app_path": app_path}, f, indent=2)
    except Exception:
        pass

def play_pause():
    """Play/pause multimedia"""
    try:
        pyautogui.press("playpause")
    except Exception:
        pyautogui.press("space")

def close_window():
    """Close active window by clicking X button"""
    try:
        if WIN32_AVAILABLE:
            hwnd = win32gui.GetForegroundWindow()
            if hwnd:
                rect = win32gui.GetWindowRect(hwnd)
                x, y, x2, y2 = rect
                # Close button is typically 20px from right edge, 15px from top
                close_x = x2 - 20
                close_y = y + 15
                win32api.SetCursorPos((close_x, close_y))
                time.sleep(0.05)
                win32api.mouse_event(win32con.MOUSEEVENTF_LEFTDOWN, 0, 0, 0, 0)
                time.sleep(0.02)
                win32api.mouse_event(win32con.MOUSEEVENTF_LEFTUP, 0, 0, 0, 0)
        else:
            pyautogui.hotkey("alt", "f4")
    except Exception:
        try:
            pyautogui.hotkey("alt", "f4")
        except Exception:
            pass

def take_screenshot():
    """Take fullscreen screenshot and return filepath for notification"""
    try:
        timestamp = time.strftime("%Y%m%d_%H%M%S")
        filepath = SS_FOLDER / f"screenshot_{timestamp}.png"
        screenshot = pyautogui.screenshot()
        screenshot.save(filepath)
        return str(filepath)
    except Exception as e:
        print(f"Screenshot failed: {e}")
        return None

# Cache volume interface for better performance
_volume_interface = None

def _get_volume_interface():
    """Get or create volume interface"""
    global _volume_interface
    if _volume_interface is None and PYCAW_AVAILABLE:
        try:
            devices = AudioUtilities.GetSpeakers()
            # GetSpeakers() returns a list, get the first device
            if devices:
                device = devices[0]
                interface = device.Activate(IAudioEndpointVolume._iid_, comtypes.CLSCTX_ALL, None)
                _volume_interface = cast(interface, POINTER(IAudioEndpointVolume))
            else:
                _volume_interface = False
        except Exception as e:
            print(f"Failed to initialize volume interface: {e}")
            _volume_interface = False  # Mark as failed
    return _volume_interface

def volume_up():
    """Increase volume by 10%"""
    try:
        volume = _get_volume_interface()
        if volume:
            current = volume.GetMasterVolumeLevelScalar()
            new_volume = min(1.0, current + 0.1)
            volume.SetMasterVolumeLevelScalar(new_volume, None)
        else:
            # Fallback: press volume up 5 times (each press is ~2%)
            for _ in range(5):
                pyautogui.press("volumeup")
    except Exception as e:
        print(f"Volume up failed: {e}")
        # Try fallback
        try:
            for _ in range(5):
                pyautogui.press("volumeup")
        except Exception:
            pass

def volume_down():
    """Decrease volume by 10%"""
    try:
        volume = _get_volume_interface()
        if volume:
            current = volume.GetMasterVolumeLevelScalar()
            new_volume = max(0.0, current - 0.1)
            volume.SetMasterVolumeLevelScalar(new_volume, None)
        else:
            # Fallback: press volume down 5 times
            for _ in range(5):
                pyautogui.press("volumedown")
    except Exception as e:
        print(f"Volume down failed: {e}")
        # Try fallback
        try:
            for _ in range(5):
                pyautogui.press("volumedown")
        except Exception:
            pass

def launch_app():
    """Launch the configured application"""
    try:
        config = load_app_config()
        app_path = config.get("app_path", "")
        
        if not app_path or not os.path.exists(app_path):
            print(f"Application not configured or path invalid: {app_path}")
            return False
        
        # Launch application
        if os.name == 'nt':  # Windows
            subprocess.Popen([app_path], shell=True)
        else:  # Linux/Mac
            subprocess.Popen([app_path])
        
        return True
    except Exception as e:
        print(f"Failed to launch app: {e}")
        return False

def set_app_path(app_path):
    """Set the application path for Yo gesture"""
    save_app_config(app_path)
    return os.path.exists(app_path) if app_path else False

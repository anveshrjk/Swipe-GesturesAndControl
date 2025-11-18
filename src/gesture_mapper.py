# File: src/gesture_mapper.py
# load/save mapping; execute mapped actions.
import json
import os
import keyboard
import pyautogui
from typing import Dict

CONFIG_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), "config.json")

DEFAULT_MAP = {
    "open_palm": "media_play_pause",
    "swipe_down": "win+d",
    "swipe_up": "win+tab",
    "palm_closing": "left_click",
    "fist": "noop",
    "swipe_left": "media_previous",
    "swipe_right": "media_next",
    "palm_up": "volume up",
    "palm_down": "volume down"
}

class GestureMapper:
    """manages gesture->action mapping and executes actions."""
    def __init__(self, config_path=CONFIG_PATH):
        self.config_path = config_path
        self.map = DEFAULT_MAP.copy()
        self.load()

    def load(self):
        """load mappings from config.json if present."""
        try:
            with open(self.config_path, "r", encoding="utf-8") as f:
                data = json.load(f)
                if isinstance(data, dict):
                    self.map.update(data)
        except FileNotFoundError:
            self.save()  # create default
        except Exception:
            pass

    def save(self):
        """save current mapping to config.json."""
        try:
            with open(self.config_path, "w", encoding="utf-8") as f:
                json.dump(self.map, f, indent=2)
        except Exception:
            pass

    def set_mapping(self, gesture: str, action: str):
        """set and persist mapping."""
        self.map[gesture] = action
        self.save()

    def get_action(self, gesture: str):
        """return action string for gesture."""
        return self.map.get(gesture, "noop")

    def execute_action(self, gesture: str):
        """execute mapped action using keyboard/pyautogui."""
        action = self.get_action(gesture)
        if not action or action.lower() == "noop":
            return
        # left click special-case
        if action == "left_click" or action == "click":
            pyautogui.click()
            return
        # map common phrase -> keyboard key names, else pass through
        # keyboard.press_and_release expects strings like "ctrl+alt+t" or "media_next"
        try:
            keyboard.press_and_release(action)
        except Exception:
            # fallback for pyautogui if keyboard fails
            try:
                if action.lower().startswith("volume") or "media" in action.lower():
                    keyboard.press_and_release(action)
            except Exception:
                pass

    def simulate_action(self, gesture: str):
        """helper for editor to test actions without cooldown logic."""
        self.execute_action(gesture)

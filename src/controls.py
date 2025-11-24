# controls.py  – Windows 11 real system control
import keyboard
from ctypes import POINTER, cast
from comtypes import CLSCTX_ALL
from pycaw.pycaw import AudioUtilities, IAudioEndpointVolume


class MediaController:
    def __init__(self):
        devices = AudioUtilities.GetSpeakers()
        interface = devices.Activate(IAudioEndpointVolume._iid_, CLSCTX_ALL, None)
        self.volume = cast(interface, POINTER(IAudioEndpointVolume))
        print("✅ Using Pycaw + keyboard for real Windows control")

    # ---------- Volume ----------
    def get_volume(self):
        try:
            return round(self.volume.GetMasterVolumeLevelScalar(), 2)
        except Exception:
            return 0.5

    def set_volume(self, value):
        value = max(0.0, min(1.0, value))
        try:
            self.volume.SetMasterVolumeLevelScalar(value, None)
        except Exception as e:
            print("⚠️ Volume set failed:", e)

    def volume_up(self, step=0.05):
        v = min(1.0, self.get_volume() + step)
        self.set_volume(v)
        print(f"🔊 System Volume: {int(v * 100)}%")

    def volume_down(self, step=0.05):
        v = max(0.0, self.get_volume() - step)
        self.set_volume(v)
        print(f"🔉 System Volume: {int(v * 100)}%")

    # ---------- Media ----------
    def toggle_play_pause(self):
        """Send real global Play/Pause event"""
        try:
            keyboard.send("play/pause media")
            print("⏯️ Play/Pause executed")
        except Exception as e:
            print("⚠️ Play/Pause failed:", e)

# camera.py
# High-res camera capture (HD 1280x720) with frame throttling to ~30 FPS.

import threading
import cv2
import time
from queue import Full

class CameraThread(threading.Thread):
    def __init__(self, frame_q, stop_event, cfg):
        super().__init__(daemon=True)
        self.frame_q = frame_q
        self.stop_event = stop_event
        self.cfg = cfg or {}
        # Force HD
        self.width = int(self.cfg.get("hd", {}).get("width", 1280))
        self.height = int(self.cfg.get("hd", {}).get("height", 720))
        self.target_fps = int(self.cfg.get("target_fps", 30))
        self.mirror = bool(self.cfg.get("mirror_preview", True))
        self.cap = None

    def run(self):
        # Prefer DirectShow on Windows for stability:
        try:
            self.cap = cv2.VideoCapture(self.cfg.get("device_index", 0), cv2.CAP_DSHOW)
        except Exception:
            self.cap = cv2.VideoCapture(self.cfg.get("device_index", 0))

        # Request HD and target fps (some cameras accept)
        try:
            self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, self.width)
            self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, self.height)
            self.cap.set(cv2.CAP_PROP_FPS, float(self.target_fps))
        except Exception:
            pass

        target_interval = 1.0 / max(1, self.target_fps)

        while not self.stop_event.is_set():
            t0 = time.time()
            ret, frame = self.cap.read()
            if not ret or frame is None:
                # small sleep instead of tight spinning
                time.sleep(0.01)
                continue

            # Mirror for natural interaction
            if self.mirror:
                frame = cv2.flip(frame, 1)

            # Ensure correct resolution
            try:
                h, w = frame.shape[:2]
                if (w != self.width) or (h != self.height):
                    frame = cv2.resize(frame, (self.width, self.height), interpolation=cv2.INTER_AREA)
            except Exception:
                pass

            # keep only latest frame in queue
            try:
                while True:
                    self.frame_q.get_nowait()
            except Exception:
                pass

            try:
                self.frame_q.put_nowait(frame)
            except Full:
                pass

            elapsed = time.time() - t0
            sleep_for = target_interval - elapsed
            if sleep_for > 0:
                time.sleep(sleep_for)

        try:
            self.cap.release()
        except Exception:
            pass

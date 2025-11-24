import threading
import time
import cv2
from queue import Queue, Empty


class CameraThread(threading.Thread):
    def __init__(self, frame_queue: Queue, stop_event: threading.Event, cfg: dict):
        super().__init__(daemon=True)
        self.frame_queue = frame_queue
        self.stop_event = stop_event

        self.device_index = cfg.get("device_index", 0)
        self.width = cfg.get("width", 1280)
        self.height = cfg.get("height", 720)
        self.mirror = cfg.get("mirror_preview", True)

        self.cap = None

    def run(self):
        self.cap = cv2.VideoCapture(self.device_index, cv2.CAP_DSHOW)

        try:
            self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, self.width)
            self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, self.height)
        except Exception:
            pass

        while not self.stop_event.is_set():
            ok, frame = self.cap.read()

            if not ok:
                time.sleep(0.05)
                continue

            if self.mirror:
                frame = cv2.flip(frame, 1)

            try:
                if self.frame_queue.full():
                    try:
                        _ = self.frame_queue.get_nowait()
                    except Exception:
                        pass

                self.frame_queue.put_nowait(frame)
            except Exception:
                pass

        try:
            self.cap.release()
        except Exception:
            pass

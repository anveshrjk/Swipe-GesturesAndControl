# File: src/camera.py
# simple camera thread, small, fast.
import cv2
import threading
import queue
import time

class CameraThread(threading.Thread):
    """captures frames in background quickly."""
    def __init__(self, frame_queue: queue.Queue, camera_index=0, width=1280, height=720):
        super().__init__(daemon=True)
        self.frame_queue = frame_queue
        self.camera_index = camera_index
        self._stop = threading.Event()
        self.cap = cv2.VideoCapture(self.camera_index)
        if not self.cap.isOpened():
            raise RuntimeError("Could not open webcam")
        # set capture resolution (increase as requested)
        self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, width)
        self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, height)
        self.frame_count = 0
        self.fps = 0
        self.last_fps_time = time.time()

    def run(self):
        while not self._stop.is_set():
            ret, frame = self.cap.read()
            if not ret:
                time.sleep(0.01)
                continue
            # stable FPS counter per second
            self.frame_count += 1
            now = time.time()
            if now - self.last_fps_time >= 1.0:
                self.fps = self.frame_count
                self.frame_count = 0
                self.last_fps_time = now
            # keep latest only
            if self.frame_queue.qsize() > 1:
                try:
                    self.frame_queue.get_nowait()
                except queue.Empty:
                    pass
            self.frame_queue.put((frame, self.fps))

    def stop(self):
        self._stop.set()
        time.sleep(0.05)
        self.cap.release()

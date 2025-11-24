# utils.py
import time


class FPSCounter:
    """Utility class to calculate real-time FPS."""
    def __init__(self):
        self.prev_time = time.time()
        self.frame_count = 0
        self.fps = 0

    def update(self):
        """Update FPS calculation."""
        self.frame_count += 1
        if time.time() - self.prev_time >= 1.0:
            self.fps = self.frame_count
            self.frame_count = 0
            self.prev_time = time.time()
        return self.fps


def current_millis():
    """Return current time in milliseconds."""
    return int(round(time.time() * 1000))


def elapsed_since(start_ms):
    """Return elapsed time in milliseconds since 'start_ms'."""
    return current_millis() - start_ms


def clamp(value, min_val, max_val):
    """Clamp numeric value between min and max."""
    return max(min_val, min(value, max_val))

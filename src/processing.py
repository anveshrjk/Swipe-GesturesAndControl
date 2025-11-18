# File: src/processing.py
# mediaPipe processing, gestures detection, and triggering actions via mapper.
import threading
import queue
import cv2
import time
import numpy as np
import sys
import os
import contextlib
from collections import deque

# silence C++ stderr for mediapipe imports
@contextlib.contextmanager
def suppress_stderr():
    with open(os.devnull, "w") as devnull:
        old = sys.stderr
        sys.stderr = devnull
        try:
            yield
        finally:
            sys.stderr = old

with suppress_stderr():
    import mediapipe as mp

class ProcessingThread(threading.Thread):
    """runs MediaPipe hands, classifies gestures, calls mapper."""
    def __init__(self, frame_queue: queue.Queue, results_queue: queue.Queue, mapper, preview_size=(960,540)):
        super().__init__(daemon=True)
        self.frame_queue = frame_queue
        self.results_queue = results_queue
        self.mapper = mapper
        self._stop = False

        # settings adjustable from UI
        self.gesture_enabled = True
        self.swipe_sensitivity = 60  # px threshold for horizontal swipe
        self.swipe_vertical_sensitivity = 40  # px for vertical swipe
        self.swipe_history_len = 6
        self.cooldown_sec = 0.7

        # centroid history for velocity
        self.centroids = deque(maxlen=self.swipe_history_len)
        self.last_action_time = 0

        # palm_closing params
        self.close_threshold = 40  # distance threshold in px

        # mediapipe init
        with suppress_stderr():
            self.mp_hands = mp.solutions.hands
            self.hands = self.mp_hands.Hands(
                max_num_hands=1,
                min_detection_confidence=0.6,
                min_tracking_confidence=0.5
            )
            self.mp_draw = mp.solutions.drawing_utils

        self.preview_w, self.preview_h = preview_size

    def stop(self):
        self._stop = True

    # finger classification simple
    def classify_fingers(self, lm):
        fingers = []
        # thumb: compare x of tip and ip (index 3)
        fingers.append(1 if lm[4][0] > lm[3][0] else 0)
        for t in (8,12,16,20):
            fingers.append(1 if lm[t][1] < lm[t-2][1] else 0)
        s = sum(fingers)
        if s >= 4: return "open_palm"
        if s <= 1: return "fist"
        return "unknown"

    # palm up/down by comparing middle tip y to wrist y
    def palm_orientation(self, lm):
        wrist_y = lm[0][1]
        middle_tip_y = lm[12][1]
        return "palm_up" if middle_tip_y < wrist_y else "palm_down"

    # palm_closing: average fingertip distance to wrist small -> closing
    def palm_closing(self, lm):
        wrist = lm[0]
        tips = [lm[i] for i in (4,8,12,16,20)]
        dists = [np.hypot(t[0]-wrist[0], t[1]-wrist[1]) for t in tips]
        avg = sum(dists)/len(dists)
        return avg < self.close_threshold

    # detect horizontal/vertical swipes
    def detect_swipe(self, cx, cy):
        self.centroids.append((cx, cy))
        if len(self.centroids) < self.centroids.maxlen:
            return None
        dx = self.centroids[-1][0] - self.centroids[0][0]
        dy = self.centroids[-1][1] - self.centroids[0][1]
        if abs(dx) > self.swipe_sensitivity and abs(dx) > abs(dy):
            return "swipe_right" if dx > 0 else "swipe_left"
        if abs(dy) > self.swipe_vertical_sensitivity and abs(dy) > abs(dx):
            return "swipe_down" if dy > 0 else "swipe_up"
        return None

    def trigger_action(self, gesture):
        if not self.gesture_enabled:
            return
        now = time.time()
        if now - self.last_action_time < self.cooldown_sec:
            return
        # use mapper to execute action
        try:
            self.mapper.execute_action(gesture)
        except Exception:
            pass
        self.last_action_time = now

    def run(self):
        while not self._stop:
            try:
                frame, fps = self.frame_queue.get(timeout=0.02)
            except queue.Empty:
                continue

            # flip first to draw text correctly
            frame = cv2.flip(frame, 1)
            h, w = frame.shape[:2]
            rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            with suppress_stderr():
                results = self.hands.process(rgb)

            annotated = frame.copy()
            gesture = "none"

            if results.multi_hand_landmarks:
                for handLms in results.multi_hand_landmarks:
                    self.mp_draw.draw_landmarks(annotated, handLms, self.mp_hands.HAND_CONNECTIONS)
                    # landmarks to absolute px
                    lm = [(int(l.x * w), int(l.y * h)) for l in handLms.landmark]
                    # centroid
                    xs = [p[0] for p in lm]
                    ys = [p[1] for p in lm]
                    cx, cy = int(sum(xs)/len(xs)), int(sum(ys)/len(ys))

                    # detection steps
                    base = self.classify_fingers(lm)
                    orient = self.palm_orientation(lm)
                    closing = self.palm_closing(lm)
                    swipe = self.detect_swipe(cx, cy)

                    if swipe:
                        gesture = swipe
                    elif closing:
                        gesture = "palm_closing"
                    elif base in ("open_palm","fist"):
                        gesture = base
                    else:
                        gesture = orient

                    # draw bbox + gesture text (top-left) for debugging
                    x1, y1, x2, y2 = min(xs), min(ys), max(xs), max(ys)
                    cv2.rectangle(annotated, (x1,y1), (x2,y2), (255,0,0), 2)
                    cv2.putText(annotated, f"{gesture}", (10,30),
                                cv2.FONT_HERSHEY_SIMPLEX, 0.9, (0,255,255), 2)

                    # trigger mapped action
                    self.trigger_action(gesture)

            # push latest result only
            if self.results_queue.qsize() > 1:
                try:
                    self.results_queue.get_nowait()
                except queue.Empty:
                    pass
            self.results_queue.put((annotated, fps, gesture))

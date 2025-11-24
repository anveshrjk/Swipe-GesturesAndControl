# gestures.py
import cv2
import mediapipe as mp
import time
from controls import MediaController

class GestureController:
    def __init__(self, activation_time=1.0):
        self.mp_hands = mp.solutions.hands
        self.hands = self.mp_hands.Hands(
            max_num_hands=1,
            min_detection_confidence=0.7,
            min_tracking_confidence=0.7
        )
        self.mp_draw = mp.solutions.drawing_utils

        # States
        self.mode = "idle"
        self.last_palm_time = 0
        self.last_action_time = 0
        self.activation_time = activation_time
        self.controller = MediaController()

    def detect(self, frame):
        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        results = self.hands.process(rgb)
        h, w, _ = frame.shape

        if results.multi_hand_landmarks:
            for hand_landmarks in results.multi_hand_landmarks:
                lm = hand_landmarks.landmark

                # Finger coordinates
                index_tip = lm[8]
                thumb_tip = lm[4]
                middle_tip = lm[12]
                wrist = lm[0]

                # Gesture detection logic
                fingers_up = self.get_finger_states(lm)

                # 1️⃣ Palm hold -> Volume mode activation
                if all(fingers_up):  # All fingers up = palm open
                    if time.time() - self.last_palm_time > self.activation_time:
                        self.mode = "volume_active"
                    else:
                        if self.mode != "volume_active":
                            self.last_palm_time = time.time()

                # 2️⃣ OK gesture -> Play/Pause
                elif self.is_ok_gesture(lm):
                    if time.time() - self.last_action_time > 1:
                        self.controller.toggle_play_pause()
                        self.last_action_time = time.time()
                        self.mode = "idle"

                # 3️⃣ Volume control (index up/down)
                elif self.mode == "volume_active":
                    if fingers_up[1] and not any(fingers_up[2:]):  # Only index finger up
                        self.controller.volume_up()
                        self.mode = "volume_active"
                        self.last_action_time = time.time()
                    elif not fingers_up[1] and any(fingers_up[2:]):  # Index down
                        self.controller.volume_down()
                        self.mode = "volume_active"
                        self.last_action_time = time.time()

                # Reset mode after inactivity
                if time.time() - self.last_action_time > 3:
                    self.mode = "idle"

                self.mp_draw.draw_landmarks(frame, hand_landmarks, self.mp_hands.HAND_CONNECTIONS)

        return frame, self.mode

    def get_finger_states(self, lm):
        """Return True/False list for [Thumb, Index, Middle, Ring, Pinky]."""
        return [
            lm[4].x < lm[3].x,           # Thumb
            lm[8].y < lm[6].y,           # Index
            lm[12].y < lm[10].y,         # Middle
            lm[16].y < lm[14].y,         # Ring
            lm[20].y < lm[18].y          # Pinky
        ]

    def is_ok_gesture(self, lm):
        """Detect OK sign by distance between thumb tip and index tip."""
        thumb = lm[4]
        index = lm[8]
        dist = ((thumb.x - index.x) ** 2 + (thumb.y - index.y) ** 2) ** 0.5
        return dist < 0.05  # Adjust threshold if needed

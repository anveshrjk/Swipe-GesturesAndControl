# processing.py
"""
Simple processing thread: detects gestures and performs actions
"""

import threading
import time
import cv2
from queue import Empty
import utils
import gestures
import actions

logger = utils.get_logger("processing")

try:
    import mediapipe as mp
    MP_AVAILABLE = True
except Exception:
    MP_AVAILABLE = False
    logger.warning("MediaPipe not available")

class ProcessingThread(threading.Thread):
    def __init__(self, frame_q, preview_q, event_q, stop_event, cfg):
        super().__init__(daemon=True)
        self.frame_q = frame_q
        self.preview_q = preview_q
        self.event_q = event_q
        self.stop_event = stop_event
        self.cfg = cfg or {}
        
        # Gesture detection settings
        self.gesture_hold_time = 0.25  # Hold time for most gestures
        self.ok_hold_time = 0.2  # Slightly shorter for OK gesture
        self.v_hold_time = 0.2  # Short for V gesture
        self.action_cooldown = 0.6  # Cooldown between actions
        self.volume_interval = 0.3  # Volume adjustment interval
        self.volume_hold_time = 0.3  # Hold time before volume starts adjusting
        
        # State tracking
        self.current_gesture = None
        self.displayed_gesture = None  # Gesture to display (immediate)
        self.gesture_start_time = None
        self.last_action_time = {}
        self.last_volume_action_time = 0
        self.gesture_stability_count = 0  # Count consecutive detections for stability
        
        # MediaPipe setup
        if MP_AVAILABLE:
            self.mp_hands = mp.solutions.hands
            self.hands = self.mp_hands.Hands(
                static_image_mode=False,
                max_num_hands=1,
                min_detection_confidence=0.7,
                min_tracking_confidence=0.7
            )
            self.drawer = mp.solutions.drawing_utils
            self.drawing_styles = mp.solutions.drawing_styles
        else:
            self.hands = None
            self.drawer = None
            self.mp_hands = None
            self.drawing_styles = None
    
    def run(self):
        while not self.stop_event.is_set():
            try:
                frame = self.frame_q.get(timeout=0.5)
            except Empty:
                continue
            
            annotated = frame.copy()
            detected_gesture = None
            
            # Process frame with MediaPipe
            if self.hands:
                rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                results = self.hands.process(rgb)
                
                if results.multi_hand_landmarks:
                    hand_landmarks = results.multi_hand_landmarks[0]
                    
                    # Draw hand landmarks
                    self.drawer.draw_landmarks(
                        annotated,
                        hand_landmarks,
                        self.mp_hands.HAND_CONNECTIONS,
                        self.drawing_styles.get_default_hand_landmarks_style(),
                        self.drawing_styles.get_default_hand_connections_style()
                    )
                    
                    # Detect gesture
                    detected_gesture = gestures.detect_gesture(hand_landmarks.landmark)
            
            # Handle gesture state and actions
            now = time.time()
            self._handle_gesture(detected_gesture, now)
            
            # Draw detected gesture on frame immediately (don't wait for hold time)
            gesture_to_display = self.displayed_gesture or detected_gesture
            if gesture_to_display:
                text = gesture_to_display.upper().replace('_', ' ')
                # Show gesture text prominently
                cv2.putText(annotated, text, (30, 90), 
                           cv2.FONT_HERSHEY_SIMPLEX, 1.8, (0, 255, 0), 4, cv2.LINE_AA)
            
            # Send annotated frame to UI
            try:
                self.preview_q.get_nowait()
            except Exception:
                pass
            try:
                self.preview_q.put_nowait(annotated)
            except Exception:
                pass
    
    def _handle_gesture(self, gesture, now):
        """Handle gesture detection and trigger actions"""
        
        # Update displayed gesture immediately for visual feedback
        if gesture:
            self.displayed_gesture = gesture
            
            # Track gesture stability
            if gesture == self.current_gesture:
                self.gesture_stability_count += 1
            else:
                # New gesture detected
                self.gesture_stability_count = 1
                self.current_gesture = gesture
                self.gesture_start_time = now
        else:
            # No gesture detected - clear after brief delay
            if self.displayed_gesture:
                if self.gesture_start_time is not None and (now - self.gesture_start_time) > 0.15:
                    self.displayed_gesture = None
                elif self.gesture_start_time is None:
                    self.displayed_gesture = None
            self.current_gesture = None
            self.gesture_start_time = None
            self.gesture_stability_count = 0
            return
        
        # Only process actions if gesture is stable (detected at least 2 frames)
        if self.gesture_stability_count < 2:
            return
        
        # If same gesture continues, check if we should trigger action
        if gesture == self.current_gesture and self.gesture_start_time is not None:
            hold_duration = now - self.gesture_start_time
            
            # Use appropriate hold time for each gesture
            if gesture == 'ok':
                required_hold = self.ok_hold_time
            elif gesture == 'v':
                required_hold = self.v_hold_time
            elif gesture in ['fingers_up', 'fingers_down']:
                required_hold = self.volume_hold_time
            else:
                required_hold = self.gesture_hold_time
            
            if hold_duration >= required_hold:
                # Gesture held long enough, perform action
                self._perform_action(gesture, now)
    
    def _perform_action(self, gesture, now):
        """Perform the action for the detected gesture"""
        
        # Check cooldown for one-time actions
        if gesture in ['ok', 'v', 'shaka', 'yo']:
            last_time = self.last_action_time.get(gesture, 0)
            if now - last_time < self.action_cooldown:
                return  # Still in cooldown
            
            if gesture == 'ok':
                actions.play_pause()
                self._push_event('play_pause')
            elif gesture == 'v':
                actions.close_window()
                self._push_event('close_window')
            elif gesture == 'shaka':
                filepath = actions.take_screenshot()
                self._push_event('screenshot', filepath)
            elif gesture == 'yo':
                actions.launch_app()
                self._push_event('launch_app')
            
            self.last_action_time[gesture] = now
            self.gesture_start_time = None  # Reset to require new hold
        
        # Volume controls work continuously while gesture is held
        elif gesture in ['fingers_up', 'fingers_down']:
            # Only adjust if gesture has been held for required time
            hold_duration = now - self.gesture_start_time if self.gesture_start_time else 0
            if hold_duration >= self.volume_hold_time:
                # Adjust volume at intervals
                if now - self.last_volume_action_time >= self.volume_interval:
                    if gesture == 'fingers_up':
                        actions.volume_up()
                        self._push_event('volume_up')
                    elif gesture == 'fingers_down':
                        actions.volume_down()
                        self._push_event('volume_down')
                    self.last_volume_action_time = now
    
    def _push_event(self, name, data=None):
        """Push event to event queue"""
        try:
            event = {"name": name, "time": time.time()}
            if data is not None:
                event["data"] = data
            self.event_q.put_nowait(event)
        except Exception:
            pass

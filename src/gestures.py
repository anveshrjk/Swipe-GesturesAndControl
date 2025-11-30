# gestures.py
"""
Improved gesture detection using MediaPipe hand landmarks.
Detects: OK, V, Shaka, Thumbs Up, Thumbs Down, Yo
"""

import math

# MediaPipe hand landmark indices
WRIST = 0
THUMB_CMC = 1
THUMB_MCP = 2
THUMB_IP = 3
THUMB_TIP = 4
INDEX_MCP = 5
INDEX_PIP = 6
INDEX_DIP = 7
INDEX_TIP = 8
MIDDLE_MCP = 9
MIDDLE_PIP = 10
MIDDLE_DIP = 11
MIDDLE_TIP = 12
RING_MCP = 13
RING_PIP = 14
RING_DIP = 15
RING_TIP = 16
PINKY_MCP = 17
PINKY_PIP = 18
PINKY_DIP = 19
PINKY_TIP = 20

def distance(p1, p2):
    """Calculate Euclidean distance between two points"""
    return math.sqrt((p1[0] - p2[0])**2 + (p1[1] - p2[1])**2)

def is_finger_extended(landmarks, tip_idx, pip_idx, mcp_idx):
    """Check if finger is extended upward (tip above PIP)"""
    tip = landmarks[tip_idx]
    pip = landmarks[pip_idx]
    # Finger is extended if tip is above PIP
    return tip[1] < pip[1] - 0.01

def is_finger_closed(landmarks, tip_idx, pip_idx):
    """Check if finger is closed (tip below PIP)"""
    tip = landmarks[tip_idx]
    pip = landmarks[pip_idx]
    # Finger is closed if tip is below PIP
    return tip[1] > pip[1] + 0.01

def is_ok(landmarks):
    """OK gesture: thumb and index finger tips close together forming circle, other fingers extended"""
    thumb_tip = landmarks[THUMB_TIP]
    index_tip = landmarks[INDEX_TIP]
    
    # Check if thumb and index tips are close (forming circle)
    dist = distance(thumb_tip, index_tip)
    palm_size = distance(landmarks[WRIST], landmarks[MIDDLE_MCP])
    
    if palm_size < 0.01:
        return False
    
    # Tips should be close (normalized by palm size)
    if dist / palm_size > 0.15:  # Too far apart
        return False
    
    # Check thumb is NOT pointing up (to avoid confusion with thumbs up)
    thumb_mcp = landmarks[THUMB_MCP]
    if thumb_tip[1] < thumb_mcp[1] - 0.05:  # Thumb pointing up
        return False
    
    # Check other fingers (middle, ring, pinky) are extended
    middle_extended = is_finger_extended(landmarks, MIDDLE_TIP, MIDDLE_PIP, MIDDLE_MCP)
    ring_extended = is_finger_extended(landmarks, RING_TIP, RING_PIP, RING_MCP)
    pinky_extended = is_finger_extended(landmarks, PINKY_TIP, PINKY_PIP, PINKY_MCP)
    
    # At least 2 of 3 should be extended
    extended_count = sum([middle_extended, ring_extended, pinky_extended])
    return extended_count >= 2

def is_v(landmarks):
    """V gesture: index and middle fingers extended, others closed"""
    # Index and middle must be extended
    index_extended = is_finger_extended(landmarks, INDEX_TIP, INDEX_PIP, INDEX_MCP)
    middle_extended = is_finger_extended(landmarks, MIDDLE_TIP, MIDDLE_PIP, MIDDLE_MCP)
    
    if not (index_extended and middle_extended):
        return False
    
    # Check fingers are separated (V shape)
    index_tip = landmarks[INDEX_TIP]
    middle_tip = landmarks[MIDDLE_TIP]
    palm_size = distance(landmarks[WRIST], landmarks[MIDDLE_MCP])
    
    if palm_size < 0.01:
        return False
    
    separation = distance(index_tip, middle_tip) / palm_size
    if separation < 0.08:  # Fingers too close together
        return False
    
    # IMPORTANT: Thumb must NOT be pointing down (to avoid confusion with thumbs down)
    thumb_tip = landmarks[THUMB_TIP]
    thumb_mcp = landmarks[THUMB_MCP]
    thumb_ip = landmarks[THUMB_IP]
    # If thumb is pointing down, it's likely thumbs down, not V
    if thumb_tip[1] > thumb_mcp[1] + 0.05 and thumb_tip[1] > thumb_ip[1] + 0.05:
        return False
    
    # Ring and pinky should be closed
    ring_closed = is_finger_closed(landmarks, RING_TIP, RING_PIP)
    pinky_closed = is_finger_closed(landmarks, PINKY_TIP, PINKY_PIP)
    
    # At least one should be closed (both preferred)
    return ring_closed or pinky_closed

def is_shaka(landmarks):
    """Shaka gesture: thumb and pinky extended horizontally, other fingers closed"""
    # Thumb extended horizontally (to the right)
    thumb_tip = landmarks[THUMB_TIP]
    thumb_ip = landmarks[THUMB_IP]
    if thumb_tip[0] <= thumb_ip[0] + 0.02:  # Not extended enough
        return False
    
    # Pinky extended
    pinky_extended = is_finger_extended(landmarks, PINKY_TIP, PINKY_PIP, PINKY_MCP)
    if not pinky_extended:
        return False
    
    # Index, middle, ring closed
    index_closed = is_finger_closed(landmarks, INDEX_TIP, INDEX_PIP)
    middle_closed = is_finger_closed(landmarks, MIDDLE_TIP, MIDDLE_PIP)
    ring_closed = is_finger_closed(landmarks, RING_TIP, RING_PIP)
    
    return index_closed and middle_closed and ring_closed

def is_finger_pointing_down(landmarks, tip_idx, pip_idx, mcp_idx):
    """Check if finger is pointing down (tip below PIP and MCP)"""
    tip = landmarks[tip_idx]
    pip = landmarks[pip_idx]
    mcp = landmarks[mcp_idx]
    # Finger is pointing down if tip is below PIP and MCP
    return tip[1] > pip[1] + 0.01 and tip[1] > mcp[1] + 0.01

def is_all_fingers_up(landmarks):
    """All 5 fingers pointing up - Volume Up gesture"""
    # Thumb pointing up
    thumb_tip = landmarks[THUMB_TIP]
    thumb_mcp = landmarks[THUMB_MCP]
    thumb_ip = landmarks[THUMB_IP]
    if thumb_tip[1] >= thumb_mcp[1] - 0.02 or thumb_tip[1] >= thumb_ip[1] - 0.02:
        return False
    
    # All 4 fingers (index, middle, ring, pinky) pointing up
    index_up = is_finger_extended(landmarks, INDEX_TIP, INDEX_PIP, INDEX_MCP)
    middle_up = is_finger_extended(landmarks, MIDDLE_TIP, MIDDLE_PIP, MIDDLE_MCP)
    ring_up = is_finger_extended(landmarks, RING_TIP, RING_PIP, RING_MCP)
    pinky_up = is_finger_extended(landmarks, PINKY_TIP, PINKY_PIP, PINKY_MCP)
    
    # All 4 fingers must be extended upward
    return index_up and middle_up and ring_up and pinky_up

def is_all_fingers_down(landmarks):
    """All 4 fingers (excluding thumb) pointing down - Volume Down gesture"""
    # Index, middle, ring, pinky all pointing down
    index_down = is_finger_pointing_down(landmarks, INDEX_TIP, INDEX_PIP, INDEX_MCP)
    middle_down = is_finger_pointing_down(landmarks, MIDDLE_TIP, MIDDLE_PIP, MIDDLE_MCP)
    ring_down = is_finger_pointing_down(landmarks, RING_TIP, RING_PIP, RING_MCP)
    pinky_down = is_finger_pointing_down(landmarks, PINKY_TIP, PINKY_PIP, PINKY_MCP)
    
    # All 4 fingers must be pointing down
    return index_down and middle_down and ring_down and pinky_down

def is_yo(landmarks):
    """Yo gesture: index and pinky extended, middle and ring closed"""
    # Index and pinky extended
    index_extended = is_finger_extended(landmarks, INDEX_TIP, INDEX_PIP, INDEX_MCP)
    pinky_extended = is_finger_extended(landmarks, PINKY_TIP, PINKY_PIP, PINKY_MCP)
    
    if not (index_extended and pinky_extended):
        return False
    
    # Middle and ring closed
    middle_closed = is_finger_closed(landmarks, MIDDLE_TIP, MIDDLE_PIP)
    ring_closed = is_finger_closed(landmarks, RING_TIP, RING_PIP)
    
    return middle_closed and ring_closed

def detect_gesture(landmarks):
    """
    Detect which gesture is being shown.
    Returns: 'ok', 'v', 'shaka', 'fingers_up', 'fingers_down', 'yo', or None
    
    Priority: Check specific gestures first to avoid false positives
    """
    if not landmarks or len(landmarks) < 21:
        return None
    
    # Convert to list of (x, y) tuples
    points = [(lm.x, lm.y) for lm in landmarks]
    
    # Check gestures in priority order (specific gestures first)
    # OK and V are checked first as they're most common
    if is_ok(points):
        return 'ok'
    elif is_v(points):
        return 'v'
    elif is_shaka(points):
        return 'shaka'
    elif is_yo(points):
        return 'yo'
    # Volume gestures checked after specific gestures
    elif is_all_fingers_up(points):
        return 'fingers_up'
    elif is_all_fingers_down(points):
        return 'fingers_down'
    
    return None

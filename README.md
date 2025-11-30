SWIPE — Gesture Control
=======================

A small Python tool to control media and take screenshots using hand gestures (MediaPipe + OpenCV + CustomTkinter UI).

Quick features
- Play/Pause (OK gesture)
- Volume up/down (index up/down)
- Take full-window screenshot (Shaka)
- Enter "Command Mode" by holding an open palm for 1s — command mode stays active for 5s
- Minimize to system tray with V gesture (then Quit via tray menu)

Installation (Windows, recommended inside a virtualenv)

Requirements are pinned in `requirements.txt`. Example:

```powershell
python -m venv .venv ; .\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

Run

```powershell
python -m src.main
```

Notes and fixes applied
- Improved camera capture to prefer grab()/retrieve() and requested 30 FPS.
- Increased frame/preview queue sizes to reduce dropped frames.
- Command mode now lasts 5 seconds (configurable via `src/config.json`).
- V gesture no longer forces Alt+F4; it requests minimize-to-tray (safer). Use tray Quit to exit.
- Robust pycaw initialization with graceful fallback to keyboard volume keys.
- UI legend wired to small PNG icons in `resources/icons/`.
- Reduced CTkImage churn in the UI to lower CPU usage.

If you want further UI polish or a different command hold/timeout behavior, tell me which parts to refine next.


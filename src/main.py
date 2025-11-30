# main.py
import logging
import threading
from queue import Queue
from pathlib import Path
import sys
import time

# make sure src is importable when running from project root
sys.path.insert(0, str(Path(__file__).resolve().parent))

from camera import CameraThread
from processing import ProcessingThread
from ui import UIApp
import utils, settings

logger = utils.get_logger("__main__")

def main():
    logger.info("Starting Swipe application (adaptive-mode)")
    cfg = {
        "device_index": 0,
        "hd": {"width": 1280, "height": 720},
        "sd": {"width": 640, "height": 480},
        "target_fps": 30,
        "mirror_preview": True,
        "screenshots_folder": str(Path.cwd() / "screenshots"),
        # adaptive flags (shared)
        "use_sd": False,
        "adaptive": True,
        "fps_low_threshold": 22,   # if processing fps falls below -> switch to SD
        "fps_high_threshold": 26,  # switch back to HD
    }

    stop_event = threading.Event()

    frame_q = Queue(maxsize=2)      # raw frames (camera -> processing)
    preview_q = Queue(maxsize=1)    # annotated preview (processing -> ui)
    event_q = Queue(maxsize=64)     # small telemetry / events

    cam = CameraThread(frame_q, stop_event, cfg)
    proc = ProcessingThread(frame_q, preview_q, event_q, stop_event, cfg)

    cam.start()
    proc.start()

    try:
        ui = UIApp(preview_q=preview_q, frame_q=frame_q, event_q=event_q, stop_event=stop_event, cfg=cfg)
        ui.run()
    except Exception:
        logger.exception("UI loop crashed")
    finally:
        stop_event.set()
        cam.join(timeout=2)
        proc.join(timeout=2)
        logger.info("Shutdown complete")

if __name__ == "__main__":
    main()

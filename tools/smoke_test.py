"""Lightweight smoke test: start CameraThread + ProcessingThread and stop them after a short run.
This avoids launching the GUI and simulates a safe startup/shutdown.
"""
import time
import threading
import sys
from queue import Queue

sys.path.insert(0, r"src")
from camera import CameraThread
from processing import ProcessingThread


def run_smoke():
    frame_q = Queue(maxsize=3)
    preview_q = Queue(maxsize=2)
    event_q = Queue(maxsize=10)
    stop_event = threading.Event()

    cam = CameraThread(frame_q=frame_q, stop_event=stop_event, cfg={})
    proc = ProcessingThread(frame_q=frame_q, preview_q=preview_q, event_q=event_q, stop_event=stop_event, cfg={})

    cam.start()
    proc.start()

    print("Threads started. Sleeping 1s...")
    time.sleep(1.0)

    stop_event.set()
    cam.join(timeout=2)
    proc.join(timeout=2)

    print("Shutdown complete")

if __name__ == '__main__':
    run_smoke()


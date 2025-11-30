# utils.py
import logging
from logging.handlers import RotatingFileHandler
import time
from pathlib import Path
import json

LOG_DIR = Path.cwd() / "logs"
LOG_DIR.mkdir(exist_ok=True)
SETTINGS_FILE = Path.cwd() / "settings.json"

def get_logger(name=__name__, level=logging.INFO):
    fmt = "%(asctime)s %(levelname)s %(name)s: %(message)s"
    logger = logging.getLogger(name)
    if not logger.handlers:
        logger.setLevel(level)
        ch = logging.StreamHandler()
        ch.setFormatter(logging.Formatter(fmt))
        logger.addHandler(ch)
        fh = RotatingFileHandler(LOG_DIR / "swipe.log", maxBytes=2_000_000, backupCount=3)
        fh.setFormatter(logging.Formatter(fmt))
        logger.addHandler(fh)
    return logger

def now():
    return time.time()

# simple settings persistence helpers
def load_settings():
    if SETTINGS_FILE.exists():
        try:
            return json.loads(SETTINGS_FILE.read_text(encoding="utf-8"))
        except Exception:
            return {}
    return {}

def save_settings(d):
    try:
        SETTINGS_FILE.write_text(json.dumps(d, indent=2), encoding="utf-8")
    except Exception:
        pass

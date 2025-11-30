# settings.py
"""
Runtime settings and thresholds used by gestures.py. UI updates these values via this module.
Values are persisted via utils.save_settings.
"""

import utils

_default = {
    "gestures": {
        "ok_tip_dist": 0.06,
        "folded_thresh": 0.12,
        "v_tip_sep": 0.20,
        "v_ext_thresh": 0.16,
        "fist_folded": 0.07,
        "index_vert_delta": 0.03,
        "shaka_thumb_pinky": 0.14,
    }
}

_store = _default.copy()
_store.update(utils.load_settings() or {})

def get():
    return _store

def get_g(key, fallback=None):
    return _store.get("gestures", {}).get(key, fallback if fallback is not None else _default["gestures"].get(key))

def set_g(key, value):
    _store.setdefault("gestures", {})[key] = value
    utils.save_settings(_store)

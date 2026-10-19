import json
import os
import tempfile

STATE_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "session_state.json")


def load_state():
    try:
        with open(STATE_FILE, "r", encoding="utf-8") as f:
            state = json.load(f)
    except (OSError, ValueError):
        return {}
    return state if isinstance(state, dict) else {}


def save_state(state):
    directory = os.path.dirname(STATE_FILE)
    fd, tmp_path = tempfile.mkstemp(dir=directory, prefix="session_state.", suffix=".tmp")
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            json.dump(state, f, indent=2)
            f.flush()
            os.fsync(f.fileno())
        os.replace(tmp_path, STATE_FILE)
    except BaseException:
        try:
            os.remove(tmp_path)
        except OSError:
            pass
        raise

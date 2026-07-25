import json
from pathlib import Path

HISTORY_FILE = Path("frontend/history.json")


def load_history():
    if HISTORY_FILE.exists():
        try:
            return json.loads(HISTORY_FILE.read_text())
        except Exception:
            return []
    return []


def save_history(history):
    HISTORY_FILE.write_text(json.dumps(history[-20:], indent=2))
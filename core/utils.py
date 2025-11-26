# core/utils.py

import json
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data"
DATA_DIR.mkdir(exist_ok=True)


def load_json(filename: str, default=None):
    """Load JSON safely; return default if missing."""
    file_path = DATA_DIR / filename
    if not file_path.exists():
        return default
    with file_path.open("r", encoding="utf-8") as f:
        return json.load(f)


def save_json(filename: str, data):
    """Save JSON to the core/data/ directory."""
    file_path = DATA_DIR / filename
    with file_path.open("w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

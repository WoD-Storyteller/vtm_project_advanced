from __future__ import annotations

import json
import os
from typing import Dict, Any


DEFAULT_STATE: Dict[str, Any] = {
    "awareness": 1,  # how aware the city is something is wrong
    "masquerade_pressure": 0,
    "violence_pressure": 0,
    "occult_pressure": 0,
    "si_pressure": 0,         # Second Inquisition heat
    "political_pressure": 0,  # faction tensions

    "themes": {
        "violence": 5,
        "occult": 5,
        "masquerade": 5,
        "politics": 5,
        "mystery": 5,
    },

    "prophecy_threads": [],
}


class DirectorState:
    """
    Thin manager around a city-scale director_state JSON blob.
    """

    def __init__(self, path: str):
        self.path = path
        self.data: Dict[str, Any] = {}
        self.load()

    # -------------------------------------------------
    # IO
    # -------------------------------------------------
    def load(self):
        if os.path.exists(self.path):
            try:
                with open(self.path, "r", encoding="utf-8") as f:
                    self.data = json.load(f)
            except Exception:
                self.data = DEFAULT_STATE.copy()
        else:
            self.data = DEFAULT_STATE.copy()

        # Ensure required keys
        for k, v in DEFAULT_STATE.items():
            if k not in self.data:
                # dicts should be shallow copies
                self.data[k] = v.copy() if isinstance(v, dict) else v

        if "themes" not in self.data:
            self.data["themes"] = DEFAULT_STATE["themes"].copy()

    def save(self):
        os.makedirs(os.path.dirname(self.path), exist_ok=True)
        with open(self.path, "w", encoding="utf-8") as f:
            json.dump(self.data, f, indent=2, ensure_ascii=False)

    # -------------------------------------------------
    # Simple helpers
    # -------------------------------------------------
    def clamp(self, key: str, lo: int = 0, hi: int = 20):
        v = int(self.data.get(key, 0))
        self.data[key] = max(lo, min(hi, v))

    def adjust(self, key: str, delta: int, lo: int = 0, hi: int = 20):
        self.data[key] = int(self.data.get(key, 0)) + delta
        self.clamp(key, lo=lo, hi=hi)

    def theme_weight(self, theme: str) -> int:
        return int(self.data.get("themes", {}).get(theme, 5))

    def adjust_theme(self, theme: str, delta: int):
        themes = self.data.setdefault("themes", {})
        themes[theme] = max(0, min(10, int(themes.get(theme, 5)) + delta))

    # -------------------------------------------------
    # Derived severity for scenes
    # -------------------------------------------------
    def global_threat_level(self) -> int:
        """
        Rough city threat band, 1–5.
        """
        total = (
            self.data.get("masquerade_pressure", 0)
            + self.data.get("violence_pressure", 0)
            + self.data.get("occult_pressure", 0)
            + self.data.get("si_pressure", 0)
            + self.data.get("political_pressure", 0)
        )
        if total <= 10:
            return 1
        elif total <= 20:
            return 2
        elif total <= 30:
            return 3
        elif total <= 40:
            return 4
        else:
            return 5

    def summarize(self) -> Dict[str, Any]:
        return {
            "awareness": self.data.get("awareness", 1),
            "masquerade_pressure": self.data.get("masquerade_pressure", 0),
            "violence_pressure": self.data.get("violence_pressure", 0),
            "occult_pressure": self.data.get("occult_pressure", 0),
            "si_pressure": self.data.get("si_pressure", 0),
            "political_pressure": self.data.get("political_pressure", 0),
            "themes": self.data.get("themes", {}),
            "global_threat": self.global_threat_level(),
        }
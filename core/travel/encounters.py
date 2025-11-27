from __future__ import annotations

import json
import os
import random
from typing import Dict, Any, Optional

ENCOUNTERS_PATH = "data/encounters.json"


# Fallback tables in case encounters.json is missing
DEFAULT_TABLES: Dict[str, Any] = {
    "urban_camarilla": [
        {"text": "A watchful Camarilla coterie tailing the PCs.", "severity": 2},
        {"text": "A ghoul courier rushing through the streets.", "severity": 1},
        {"text": "A primogen agent testing your loyalty.", "severity": 3},
    ],
    "anarch_cult": [
        {"text": "A screaming revel of the Dreaming Shore.", "severity": 3},
        {"text": "A lost soul begging for salvation.", "severity": 1},
        {"text": "A cult prophet whispering doom.", "severity": 4},
    ],
}


def _load_tables() -> Dict[str, Any]:
    if not os.path.exists(ENCOUNTERS_PATH):
        return DEFAULT_TABLES

    with open(ENCOUNTERS_PATH, "r", encoding="utf-8") as f:
        data = json.load(f)

    if isinstance(data, dict):
        return data

    # If someone puts a list instead of dict, just fall back
    return DEFAULT_TABLES


ENCOUNTER_TABLES: Dict[str, Any] = _load_tables()


def roll_encounter(enc_table: str) -> Optional[Dict[str, Any]]:
    """
    Returns a random encounter dict: {"text": str, "severity": int}
    """
    table = ENCOUNTER_TABLES.get(enc_table)
    if not table:
        return None
    return random.choice(table)


def is_encounter_triggered(base_risk: Dict[str, int]) -> bool:
    """
    Very simple risk check:
    - Sum violence, masquerade, SI
    - Each point ~10% chance, capped at 90%
    """
    risk_pool = (
        base_risk.get("violence", 1)
        + base_risk.get("masquerade", 1)
        + base_risk.get("si", 1)
    )
    chance = min(90, risk_pool * 10)
    return random.randint(1, 100) <= chance
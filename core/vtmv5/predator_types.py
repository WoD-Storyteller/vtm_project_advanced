from __future__ import annotations

from typing import Dict, Any

PREDATOR_TYPES: Dict[str, Dict[str, Any]] = {
    "Alleycat": {
        "description": "Violent ambush predator, hunting through direct attacks.",
        "feeding_bonus": "Bonuses to hunting in high-violence zones.",
    },
    "Sandman": {
        "description": "Feeds on sleeping victims.",
        "feeding_bonus": "Safer hunting but often time-consuming.",
    },
    "Farmer": {
        "description": "Feeds only from specific herds or consenting mortals.",
        "feeding_bonus": "Reduces stains but risky to sustain.",
    },
    "Bagger": {
        "description": "Steals or buys blood bags.",
        "feeding_bonus": "Safer but limited potency.",
    },
}
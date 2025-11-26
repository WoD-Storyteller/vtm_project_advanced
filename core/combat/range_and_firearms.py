from __future__ import annotations

from enum import Enum
from typing import Dict, Any


class RangeBand(str, Enum):
    CLOSE = "close"
    SHORT = "short"
    MEDIUM = "medium"
    LONG = "long"


class CoverLevel(str, Enum):
    NONE = "none"
    LIGHT = "light"
    HEAVY = "heavy"


def get_range_dice_modifier(weapon: Dict[str, Any], range_band: str) -> int:
    """
    Return dice modifier based on weapon traits and range band.
    """
    traits = weapon.get("traits", [])
    w_type = weapon.get("type")

    # Normalize
    rb = range_band.lower()
    if rb not in ("close", "short", "medium", "long"):
        rb = "close"

    mod = 0

    # Shotgun scatter behaviour
    if "scatter" in traits:
        if rb == "close":
            mod += 2
        elif rb == "short":
            mod += 0
        elif rb == "medium":
            mod -= 2
        elif rb == "long":
            mod -= 5

    # Rifles better at long range, worse up close
    if "rifle" in traits:
        if rb == "close":
            mod -= 2
        elif rb == "medium":
            mod += 0
        elif rb == "long":
            mod += 1

    # Handguns worse at long
    if "handgun" in traits:
        if rb == "long":
            mod -= 2

    # Fire-based weapons no special dice, but you can hook fear later if needed
    if "fire" in traits:
        # Optional: could boost dice at close due to terror/chaos
        if rb == "close":
            mod += 1

    # Default ranged penalties by type if you want them:
    if w_type == "ranged" and "rifle" not in traits and "scatter" not in traits:
        if rb == "long":
            mod -= 1

    return mod


def get_cover_success_penalty(cover: str) -> int:
    """
    Returns how many successes should be removed for cover.
    """
    cv = (cover or "").lower()
    if cv == CoverLevel.LIGHT.value:
        return 1
    if cv == CoverLevel.HEAVY.value:
        return 2
    return 0
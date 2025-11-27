from __future__ import annotations

from typing import Dict, Any

from .character_model import get_blood_potency


def blood_surge_bonus(player: Dict[str, Any]) -> int:
    """
    Approximate Blood Surge bonus dice by Blood Potency.
    V5 core has a table; we compress it:

      BP 0–1: +1
      BP 2–3: +2
      BP 4–5: +3
      BP 6+:  +4
    """
    bp = get_blood_potency(player)
    if bp <= 1:
        return 1
    if bp <= 3:
        return 2
    if bp <= 5:
        return 3
    return 4
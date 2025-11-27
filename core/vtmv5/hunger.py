from __future__ import annotations

import random
from typing import Dict, Any

from .character_model import get_hunger, set_hunger


def rouse_check(player: Dict[str, Any]) -> Dict[str, Any]:
    """
    Perform a Rouse Check (one d10, 6+ = success, else hunger+1).

    Returns:
    {
      "roll": int,
      "success": bool,
      "old_hunger": int,
      "new_hunger": int,
    }
    """
    old = get_hunger(player)
    roll = random.randint(1, 10)
    success = roll >= 6

    if not success:
        set_hunger(player, old + 1)

    return {
        "roll": roll,
        "success": success,
        "old_hunger": old,
        "new_hunger": get_hunger(player),
    }
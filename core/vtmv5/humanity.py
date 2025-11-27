from __future__ import annotations

import random
from typing import Dict, Any

from .character_model import (
    ensure_character_state,
    get_humanity,
    set_humanity,
    get_stains,
    set_stains,
)


def apply_stain(player: Dict[str, Any], amount: int = 1):
    ensure_character_state(player)
    set_stains(player, get_stains(player) + amount)


def remorse_roll(player: Dict[str, Any]) -> Dict[str, Any]:
    """
    V5-style remorse:
      - Pool roughly = (10 - Humanity)
      - If any success, you feel remorse: keep Humanity, clear stains.
      - Else: lose 1 Humanity, clear stains.

    This is a simplified implementation that hits the right beats.
    """
    humanity = get_humanity(player)
    stains = get_stains(player)

    pool = max(1, 10 - humanity)
    rolls = [random.randint(1, 10) for _ in range(pool)]
    successes = sum(1 for r in rolls if r >= 6)

    remorse = successes > 0

    if remorse:
        # You keep Humanity; stains are cleared.
        set_stains(player, 0)
    else:
        # Lose 1 Humanity, clear stains.
        set_humanity(player, humanity - 1)
        set_stains(player, 0)

    return {
        "rolled": rolls,
        "successes": successes,
        "remorse": remorse,
        "final_humanity": get_humanity(player),
        "final_stains": get_stains(player),
        "previous_humanity": humanity,
        "previous_stains": stains,
    }
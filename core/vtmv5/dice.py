from __future__ import annotations

import random
from typing import Dict, Any, List, Tuple


def roll_pool(
    dice_pool: int,
    hunger: int = 0,
    difficulty: int = 1,
) -> Dict[str, Any]:
    """
    Core V5 dice roller.

    dice_pool: total dice (attributes+skills+mods).
    hunger: number of hunger dice (0–5).
    difficulty: successes required to 'succeed'.

    Returns:
    {
      "dice": [int],
      "hunger_dice": [int],
      "successes": int,
      "critical_pairs": int,
      "messy_critical": bool,
      "bestial_failure": bool,
      "total_success": bool,
      "difficulty": int
    }
    """
    dice_pool = max(0, dice_pool)
    hunger = max(0, min(5, hunger))

    normal_dice_count = max(0, dice_pool - hunger)
    hunger_dice_count = min(dice_pool, hunger)

    dice: List[int] = [random.randint(1, 10) for _ in range(normal_dice_count)]
    hunger_dice: List[int] = [random.randint(1, 10) for _ in range(hunger_dice_count)]

    # Count successes
    successes = sum(1 for d in dice if d >= 6) + sum(1 for d in hunger_dice if d >= 6)

    # Critical 10s
    crit_normal = sum(1 for d in dice if d == 10)
    crit_hunger = sum(1 for d in hunger_dice if d == 10)
    total_crit = crit_normal + crit_hunger
    critical_pairs = total_crit // 2
    # Each pair adds +2 successes
    successes += critical_pairs * 2

    # Messy crit: at least one hunger 10 and at least one normal/hunger 10 pair
    messy_critical = critical_pairs > 0 and crit_hunger > 0

    # Bestial failure: total failure (no successes) AND at least one hunger die is 1
    total_failure = successes == 0
    has_hunger_one = any(d == 1 for d in hunger_dice)
    bestial_failure = total_failure and has_hunger_one

    total_success = successes >= difficulty

    return {
        "dice": dice,
        "hunger_dice": hunger_dice,
        "successes": successes,
        "critical_pairs": critical_pairs,
        "messy_critical": messy_critical,
        "bestial_failure": bestial_failure,
        "total_success": total_success,
        "difficulty": difficulty,
    }
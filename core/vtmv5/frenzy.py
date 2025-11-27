from __future__ import annotations

from typing import Dict, Any

from .dice import roll_pool
from .character_model import ensure_character_state


def frenzy_test(
    player: Dict[str, Any],
    dice_pool: int,
    difficulty: int,
    source: str = "frenzy",
) -> Dict[str, Any]:
    """
    General frenzy / Rötschreck test.

    dice_pool: e.g. Resolve + Composure
    difficulty: ST-set based on threat
    source: "frenzy" or "rotschreck" (flavor only)

    Returns:
    {
      "result": {... from roll_pool},
      "failed": bool,
      "source": str,
    }
    """
    ensure_character_state(player)
    hunger = player.get("hunger", 1)
    res = roll_pool(dice_pool=dice_pool, hunger=hunger, difficulty=difficulty)

    failed = not res["total_success"]

    if failed:
        player["frenzy_state"] = True

    return {
        "result": res,
        "failed": failed,
        "source": source,
    }


def clear_frenzy(player: Dict[str, Any]):
    ensure_character_state(player)
    player["frenzy_state"] = False
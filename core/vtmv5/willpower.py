from __future__ import annotations

from typing import Dict, Any, List

from .character_model import ensure_character_state, current_willpower, set_willpower_damage


def can_reroll(player: Dict[str, Any]) -> bool:
    ensure_character_state(player)
    return current_willpower(player) > 0


def apply_willpower_reroll(
    player: Dict[str, Any],
    rerolled_dice_count: int,
):
    """
    Apply superficial WP damage for a reroll.

    Player can reroll up to as many dice as their current WP (rules are flexible – ST can override).
    We simply mark 1 superficial WP damage per reroll action (not per die), which is a simpler
    abstraction while still feeling V5.
    """
    if rerolled_dice_count <= 0:
        return

    set_willpower_damage(player, superficial_delta=1)
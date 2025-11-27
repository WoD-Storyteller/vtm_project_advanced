from __future__ import annotations

import random
from typing import Dict, Any, Literal, List

from .character_model import get_hunger, set_hunger, ensure_character_state, get_predator_key
from . import predator_types

FeedSource = Literal["human", "animal", "bagged", "vampire"]


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


def apply_feeding(
    player: Dict[str, Any],
    source: FeedSource,
    amount: int = 1,
) -> Dict[str, Any]:
    """
    Apply feeding to a character, respecting predator type quirks.

    source: "human", "animal", "bagged", or "vampire"
    amount: how many 'steps' of Hunger to potentially slake (1–5)

    This is an abstraction: exact details are still ST-facing, but
    predator-type lore is enforced here.
    """
    ensure_character_state(player)
    old = get_hunger(player)
    amount = max(1, min(5, int(amount)))
    pred_key = get_predator_key(player)
    pt = predator_types.PREDATOR_TYPES.get(pred_key) if pred_key else None

    notes: List[str] = []

    # base hunger reduction
    new_hunger = max(0, old - amount)

    # Predator-type constraints
    if pred_key == "bagger":
        if source == "bagged":
            # bagged blood can't slake beyond 2
            new_hunger = max(new_hunger, 2)
            notes.append("Bagger: Bagged blood cannot reduce Hunger below 2.")
    if pred_key == "farmer":
        if source == "animal":
            # animals can't slake beyond 2
            new_hunger = max(new_hunger, 2)
            notes.append("Farmer: Animal blood cannot reduce Hunger below 2.")
    if pred_key == "blood_leech":
        if source == "vampire":
            # feeding from Kindred is potent: allow strong reduction
            new_hunger = max(0, old - max(amount, 2))
            notes.append("Blood Leech: Kindred vitae slakes Hunger more effectively.")
        elif source == "human":
            # mortal blood is less satisfying
            new_hunger = max(old - 1, new_hunger)
            notes.append("Blood Leech: Mortal blood is less satisfying (limited slaking).")
    if pred_key == "graverobber":
        if source != "human" and source != "vampire":
            # corpse feeding can't go below 3
            new_hunger = max(new_hunger, 3)
            notes.append("Graverobber: Corpse blood cannot reduce Hunger below 3.")

    set_hunger(player, new_hunger)

    return {
        "source": source,
        "amount": amount,
        "old_hunger": old,
        "new_hunger": new_hunger,
        "predator_type": pt["name"] if pt else None,
        "notes": notes,
    }
from __future__ import annotations

from typing import Dict, Any


DEFAULT_CHARACTER_STATE = {
    "hunger": 1,
    "willpower": {
        "max": 5,
        "superficial": 0,
        "aggravated": 0,
    },
    "humanity": 7,
    "stains": 0,
    "blood_potency": 1,
    "predator_type": None,
    "frenzy_state": False,
    # optional:
    # "convictions": [ ... ],
    # "touchstones": [ ... ],
}


def ensure_character_state(player: Dict[str, Any]) -> Dict[str, Any]:
    """
    Ensures the V5 fields exist on a player dict.
    Mutates the player dict in place.
    """
    for k, v in DEFAULT_CHARACTER_STATE.items():
        if k not in player:
            player[k] = v if not isinstance(v, dict) else v.copy()

    # ensure nested willpower keys
    wp = player["willpower"]
    wp.setdefault("max", 5)
    wp.setdefault("superficial", 0)
    wp.setdefault("aggravated", 0)

    return player


def current_willpower(player: Dict[str, Any]) -> int:
    ensure_character_state(player)
    wp = player["willpower"]
    max_wp = wp["max"]
    sup = wp["superficial"]
    agg = wp["aggravated"]
    return max(0, max_wp - sup - (agg * 2))


def set_willpower_damage(
    player: Dict[str, Any],
    superficial_delta: int = 0,
    aggravated_delta: int = 0,
):
    ensure_character_state(player)
    wp = player["willpower"]
    wp["superficial"] = max(0, wp["superficial"] + superficial_delta)
    wp["aggravated"] = max(0, wp["aggravated"] + aggravated_delta)


def get_hunger(player: Dict[str, Any]) -> int:
    ensure_character_state(player)
    return int(player.get("hunger", 1))


def set_hunger(player: Dict[str, Any], value: int):
    ensure_character_state(player)
    player["hunger"] = max(0, min(5, int(value)))


def get_humanity(player: Dict[str, Any]) -> int:
    ensure_character_state(player)
    return int(player.get("humanity", 7))


def set_humanity(player: Dict[str, Any], value: int):
    ensure_character_state(player)
    player["humanity"] = max(0, min(10, int(value)))


def get_stains(player: Dict[str, Any]) -> int:
    ensure_character_state(player)
    return int(player.get("stains", 0))


def set_stains(player: Dict[str, Any], value: int):
    ensure_character_state(player)
    player["stains"] = max(0, min(5, int(value)))


def adjust_stains(player: Dict[str, Any], delta: int):
    set_stains(player, get_stains(player) + delta)


def get_blood_potency(player: Dict[str, Any]) -> int:
    ensure_character_state(player)
    return int(player.get("blood_potency", 1))


def set_blood_potency(player: Dict[str, Any], value: int):
    ensure_character_state(player)
    player["blood_potency"] = max(0, min(10, int(value)))
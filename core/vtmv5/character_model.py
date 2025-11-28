from __future__ import annotations

from copy import deepcopy
from typing import Dict, Any, List, Optional


# -------------------------------------------------------------------
# Default character V5 state
# -------------------------------------------------------------------

DEFAULT_CHARACTER_STATE: Dict[str, Any] = {
    # Core tracks
    "hunger": 1,
    "willpower": {
        "max": 5,
        "superficial": 0,
        "aggravated": 0,
    },
    "humanity": 7,
    "stains": 0,
    "blood_potency": 1,

    # Predator type
    # "predator_key" is the canonical key (alleycat, bagger, etc.)
    # "predator_type" is the display name ("Alleycat")
    "predator_key": None,
    "predator_type": None,

    # Merits & flaws: list of dicts with at least
    # { "name": str, "dots": int, "type": "merit"/"flaw" or category, "tags": [], "note": str }
    "merits": [],
    "flaws": [],

    # Touchstones:
    # { "name": str, "description": str, "alive": bool, "tags": [..], "note": str }
    "touchstones": [],

    # Havens:
    # { "name": str, "zone_key": str, "address": str, "security": int, "tags": [..], "note": str }
    "havens": [],
}


# -------------------------------------------------------------------
# Core helpers
# -------------------------------------------------------------------

def ensure_character_state(player: Dict[str, Any]) -> None:
    """
    Make sure all V5 fields exist on the character dict.
    Does not overwrite existing values.
    """
    if player is None:
        return

    # Shallow defaults
    for key, default in DEFAULT_CHARACTER_STATE.items():
        if key not in player:
            player[key] = deepcopy(default)

    # Normalise nested structures if they exist but are wrong type
    if not isinstance(player.get("willpower"), dict):
        player["willpower"] = deepcopy(DEFAULT_CHARACTER_STATE["willpower"])

    for list_key in ("merits", "flaws", "touchstones", "havens"):
        if not isinstance(player.get(list_key), list):
            player[list_key] = []


# -------------------------------------------------------------------
# Hunger
# -------------------------------------------------------------------

def get_hunger(player: Dict[str, Any]) -> int:
    ensure_character_state(player)
    return int(player.get("hunger", 1))


def set_hunger(player: Dict[str, Any], value: int) -> None:
    """
    Clamp hunger 0–5.
    """
    ensure_character_state(player)
    player["hunger"] = max(0, min(5, int(value)))


# -------------------------------------------------------------------
# Humanity / Stains
# -------------------------------------------------------------------

def get_humanity(player: Dict[str, Any]) -> int:
    ensure_character_state(player)
    return int(player.get("humanity", 7))


def set_humanity(player: Dict[str, Any], value: int) -> None:
    ensure_character_state(player)
    player["humanity"] = max(0, min(10, int(value)))


def get_stains(player: Dict[str, Any]) -> int:
    ensure_character_state(player)
    return int(player.get("stains", 0))


def set_stains(player: Dict[str, Any], value: int) -> None:
    ensure_character_state(player)
    player["stains"] = max(0, int(value))


# -------------------------------------------------------------------
# Blood Potency
# -------------------------------------------------------------------

def get_blood_potency(player: Dict[str, Any]) -> int:
    ensure_character_state(player)
    return int(player.get("blood_potency", 1))


def set_blood_potency(player: Dict[str, Any], value: int) -> None:
    ensure_character_state(player)
    player["blood_potency"] = max(0, min(10, int(value)))


# -------------------------------------------------------------------
# Willpower
# -------------------------------------------------------------------

def get_willpower_block(player: Dict[str, Any]) -> Dict[str, Any]:
    ensure_character_state(player)
    wp = player["willpower"]
    # normalise keys
    wp.setdefault("max", 5)
    wp.setdefault("superficial", 0)
    wp.setdefault("aggravated", 0)
    return wp


def current_willpower(player: Dict[str, Any]) -> int:
    """
    Effective current WP: max - superficial - aggravated.
    (You can tweak this if you want aggravated to count double.)
    """
    wp = get_willpower_block(player)
    max_wp = int(wp.get("max", 5))
    sup = int(wp.get("superficial", 0))
    agg = int(wp.get("aggravated", 0))
    cur = max_wp - sup - agg
    return max(0, cur)


def set_willpower_max(player: Dict[str, Any], value: int) -> None:
    wp = get_willpower_block(player)
    wp["max"] = max(1, int(value))


def set_willpower_damage(
    player: Dict[str, Any],
    superficial_delta: int = 0,
    aggravated_delta: int = 0,
) -> None:
    """
    Apply WP damage; delta can be negative (healing).
    """
    wp = get_willpower_block(player)
    wp["superficial"] = max(0, wp.get("superficial", 0) + int(superficial_delta))
    wp["aggravated"] = max(0, wp.get("aggravated", 0) + int(aggravated_delta))


# -------------------------------------------------------------------
# Predator Type
# -------------------------------------------------------------------

def set_predator_info(player: Dict[str, Any], key: Optional[str], display_name: Optional[str]) -> None:
    ensure_character_state(player)
    player["predator_key"] = key
    player["predator_type"] = display_name


def get_predator_key(player: Dict[str, Any]) -> Optional[str]:
    ensure_character_state(player)
    return player.get("predator_key")


def get_predator_type_name(player: Dict[str, Any]) -> Optional[str]:
    ensure_character_state(player)
    return player.get("predator_type")


# -------------------------------------------------------------------
# Merits & Flaws (on the sheet)
# -------------------------------------------------------------------

def _norm_name(name: str) -> str:
    return name.strip().lower()


def list_merits(player: Dict[str, Any]) -> List[Dict[str, Any]]:
    ensure_character_state(player)
    return list(player.get("merits", []))


def list_flaws(player: Dict[str, Any]) -> List[Dict[str, Any]]:
    ensure_character_state(player)
    return list(player.get("flaws", []))


def add_merit(
    player: Dict[str, Any],
    name: str,
    dots: int,
    m_type: str = "general",
    tags: Optional[List[str]] = None,
    note: str = "",
) -> None:
    ensure_character_state(player)
    tags = tags or []
    n = _norm_name(name)

    merits = [m for m in player["merits"] if _norm_name(m.get("name", "")) != n]
    merits.append(
        {
            "name": name,
            "dots": int(dots),
            "type": m_type,
            "tags": list(tags),
            "note": note,
        }
    )
    player["merits"] = merits


def remove_merit(player: Dict[str, Any], name: str) -> None:
    ensure_character_state(player)
    n = _norm_name(name)
    player["merits"] = [
        m for m in player.get("merits", [])
        if _norm_name(m.get("name", "")) != n
    ]


def add_flaw(
    player: Dict[str, Any],
    name: str,
    dots: int,
    f_type: str = "general",
    tags: Optional[List[str]] = None,
    note: str = "",
) -> None:
    ensure_character_state(player)
    tags = tags or []
    n = _norm_name(name)

    flaws = [f for f in player["flaws"] if _norm_name(f.get("name", "")) != n]
    flaws.append(
        {
            "name": name,
            "dots": int(dots),
            "type": f_type,
            "tags": list(tags),
            "note": note,
        }
    )
    player["flaws"] = flaws


def remove_flaw(player: Dict[str, Any], name: str) -> None:
    ensure_character_state(player)
    n = _norm_name(name)
    player["flaws"] = [
        f for f in player.get("flaws", [])
        if _norm_name(f.get("name", "")) != n
    ]


# -------------------------------------------------------------------
# Touchstones
# -------------------------------------------------------------------

def list_touchstones(player: Dict[str, Any]) -> List[Dict[str, Any]]:
    ensure_character_state(player)
    return list(player.get("touchstones", []))


def add_touchstone(
    player: Dict[str, Any],
    name: str,
    description: str = "",
    tags: Optional[List[str]] = None,
    alive: bool = True,
    note: str = "",
) -> None:
    ensure_character_state(player)
    tags = tags or []
    n = _norm_name(name)

    touchstones = [
        ts for ts in player["touchstones"]
        if _norm_name(ts.get("name", "")) != n
    ]
    touchstones.append(
        {
            "name": name,
            "description": description,
            "alive": bool(alive),
            "tags": list(tags),
            "note": note,
        }
    )
    player["touchstones"] = touchstones


def mark_touchstone_dead(player: Dict[str, Any], name: str) -> None:
    ensure_character_state(player)
    n = _norm_name(name)
    for ts in player["touchstones"]:
        if _norm_name(ts.get("name", "")) == n:
            ts["alive"] = False


def remove_touchstone(player: Dict[str, Any], name: str) -> None:
    ensure_character_state(player)
    n = _norm_name(name)
    player["touchstones"] = [
        ts for ts in player.get("touchstones", [])
        if _norm_name(ts.get("name", "")) != n
    ]


# -------------------------------------------------------------------
# Havens
# -------------------------------------------------------------------

def list_havens(player: Dict[str, Any]) -> List[Dict[str, Any]]:
    ensure_character_state(player)
    return list(player.get("havens", []))


def add_or_update_haven(
    player: Dict[str, Any],
    name: str,
    zone_key: str = "",
    address: str = "",
    security: int = 1,
    tags: Optional[List[str]] = None,
    note: str = "",
) -> None:
    """
    Add or replace a Haven entry for this character.
    `zone_key` should match your travel zone keys (data/zones.json).
    """
    ensure_character_state(player)
    tags = tags or []
    n = _norm_name(name)

    havens = [
        h for h in player["havens"]
        if _norm_name(h.get("name", "")) != n
    ]
    havens.append(
        {
            "name": name,
            "zone_key": zone_key,
            "address": address,
            "security": int(security),
            "tags": list(tags),
            "note": note,
        }
    )
    player["havens"] = havens


def remove_haven(player: Dict[str, Any], name: str) -> None:
    ensure_character_state(player)
    n = _norm_name(name)
    player["havens"] = [
        h for h in player.get("havens", [])
        if _norm_name(h.get("name", "")) != n
    ]


# -------------------------------------------------------------------
# Bootstrap helper for new sheets
# -------------------------------------------------------------------

def bootstrap_v5_character(
    player: Dict[str, Any],
    name: Optional[str] = None,
    clan: Optional[str] = None,
    predator_key: Optional[str] = None,
    predator_name: Optional[str] = None,
    humanity: int = 7,
    blood_potency: int = 1,
    willpower_max: int = 5,
) -> Dict[str, Any]:
    """
    Upgrade / initialise a dict into a valid V5 sheet. This is what the
    Discord cog should call when you do !v5create.
    """
    if name:
        player["name"] = name
    if clan:
        player["clan"] = clan

    ensure_character_state(player)
    set_humanity(player, humanity)
    set_blood_potency(player, blood_potency)
    set_willpower_max(player, willpower_max)

    if predator_key or predator_name:
        set_predator_info(player, predator_key, predator_name)

    return player
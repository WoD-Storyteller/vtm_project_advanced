from __future__ import annotations

from typing import Dict, Any, List, Optional


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
    "predator_type": None,   # Display name, e.g. "Alleycat"
    "predator_key": None,    # Normalized key, e.g. "alleycat"
    "frenzy_state": False,

    # Havens / Domain
    "primary_haven_id": None,

    # Merits / Flaws / Convictions / Touchstones
    "merits": [],
    "flaws": [],
    "convictions": [],
    "touchstones": [],
}


def ensure_character_state(player: Dict[str, Any]) -> Dict[str, Any]:
    for k, v in DEFAULT_CHARACTER_STATE.items():
        if k not in player:
            player[k] = v if not isinstance(v, dict) else v.copy()

    wp = player["willpower"]
    wp.setdefault("max", 5)
    wp.setdefault("superficial", 0)
    wp.setdefault("aggravated", 0)

    if not isinstance(player.get("merits"), list):
        player["merits"] = []
    if not isinstance(player.get("flaws"), list):
        player["flaws"] = []
    if not isinstance(player.get("convictions"), list):
        player["convictions"] = []
    if not isinstance(player.get("touchstones"), list):
        player["touchstones"] = []

    return player


# --- Willpower ---------------------------------------------------

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


# --- Hunger ------------------------------------------------------

def get_hunger(player: Dict[str, Any]) -> int:
    ensure_character_state(player)
    return int(player.get("hunger", 1))


def set_hunger(player: Dict[str, Any], value: int):
    ensure_character_state(player)
    player["hunger"] = max(0, min(5, int(value)))


# --- Humanity / Stains -------------------------------------------

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


# --- Blood Potency -----------------------------------------------

def get_blood_potency(player: Dict[str, Any]) -> int:
    ensure_character_state(player)
    return int(player.get("blood_potency", 1))


def set_blood_potency(player: Dict[str, Any], value: int):
    ensure_character_state(player)
    player["blood_potency"] = max(0, min(10, int(value)))


# --- Predator Type -----------------------------------------------

def get_predator_key(player: Dict[str, Any]) -> Optional[str]:
    ensure_character_state(player)
    return player.get("predator_key")


def get_predator_type_name(player: Dict[str, Any]) -> Optional[str]:
    ensure_character_state(player)
    return player.get("predator_type")


def set_predator_info(player: Dict[str, Any], key: Optional[str], display_name: Optional[str]):
    ensure_character_state(player)
    player["predator_key"] = key
    player["predator_type"] = display_name


# --- Havens / Domain ---------------------------------------------

def get_primary_haven_id(player: Dict[str, Any]) -> Optional[str]:
    ensure_character_state(player)
    return player.get("primary_haven_id")


def set_primary_haven_id(player: Dict[str, Any], haven_id: Optional[str]):
    ensure_character_state(player)
    player["primary_haven_id"] = haven_id


# --- Merits & Flaws ----------------------------------------------

def _norm_name(name: str) -> str:
    return name.strip().lower()


def list_merits(player: Dict[str, Any]) -> List[Dict[str, Any]]:
    ensure_character_state(player)
    return player["merits"]


def list_flaws(player: Dict[str, Any]) -> List[Dict[str, Any]]:
    ensure_character_state(player)
    return player["flaws"]


def add_merit(player: Dict[str, Any], name: str, dots: int, m_type: str = "general", tags=None, note: str = ""):
    ensure_character_state(player)
    tags = tags or []
    merits = player["merits"]
    n = _norm_name(name)
    merits = [m for m in merits if _norm_name(m.get("name", "")) != n]
    merits.append({
        "name": name,
        "dots": int(dots),
        "type": m_type,
        "tags": list(tags),
        "note": note,
    })
    player["merits"] = merits


def remove_merit(player: Dict[str, Any], name: str):
    ensure_character_state(player)
    n = _norm_name(name)
    player["merits"] = [m for m in player["merits"] if _norm_name(m.get("name", "")) != n]


def add_flaw(player: Dict[str, Any], name: str, dots: int, f_type: str = "general", tags=None, note: str = ""):
    ensure_character_state(player)
    tags = tags or []
    flaws = player["flaws"]
    n = _norm_name(name)
    flaws = [f for f in flaws if _norm_name(f.get("name", "")) != n]
    flaws.append({
        "name": name,
        "dots": int(dots),
        "type": f_type,
        "tags": list(tags),
        "note": note,
    })
    player["flaws"] = flaws


def remove_flaw(player: Dict[str, Any], name: str):
    ensure_character_state(player)
    n = _norm_name(name)
    player["flaws"] = [f for f in player["flaws"] if _norm_name(f.get("name", "")) != n]


# --- Convictions -------------------------------------------------

def list_convictions(player: Dict[str, Any]) -> List[Dict[str, Any]]:
    ensure_character_state(player)
    return player["convictions"]


def add_conviction(player: Dict[str, Any], text: str):
    ensure_character_state(player)
    player["convictions"].append({"text": text})


def remove_conviction(player: Dict[str, Any], index: int):
    ensure_character_state(player)
    if 0 <= index < len(player["convictions"]):
        del player["convictions"][index]


# --- Touchstones -------------------------------------------------

def list_touchstones(player: Dict[str, Any]) -> List[Dict[str, Any]]:
    ensure_character_state(player)
    return player["touchstones"]


def add_touchstone(player: Dict[str, Any], name: str, role: str):
    ensure_character_state(player)
    player["touchstones"].append({
        "name": name,
        "role": role,
        "alive": True,
    })


def mark_touchstone_dead(player: Dict[str, Any], name: str):
    ensure_character_state(player)
    n = _norm_name(name)
    for ts in player["touchstones"]:
        if _norm_name(ts.get("name", "")) == n:
            ts["alive"] = False


def remove_touchstone(player: Dict[str, Any], name: str):
    ensure_character_state(player)
    n = _norm_name(name)
    player["touchstones"] = [
        ts for ts in player["touchstones"]
        if _norm_name(ts.get("name", "")) != n
    ]
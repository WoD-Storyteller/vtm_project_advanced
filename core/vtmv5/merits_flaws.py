from __future__ import annotations

from typing import Dict, Any, List, Optional


def _norm(name: str) -> str:
    return name.strip().lower()


# Minimal, representative set of merits & flaws with tags that affect mechanics.
# You can expand this list as you like.

MERITS: Dict[str, Dict[str, Any]] = {
    "iron_will": {
        "key": "iron_will",
        "name": "Iron Will",
        "dots": 2,
        "category": "mental",
        "description": "You are difficult to sway or break mentally.",
        "tags": ["remorse_bonus", "frenzy_resist_bonus"],
    },
    "unswayable_mind": {
        "key": "unswayable_mind",
        "name": "Unswayable Mind",
        "dots": 3,
        "category": "mental",
        "description": "Extra resilience against fear, coercion, and terror.",
        "tags": ["frenzy_resist_bonus"],
    },
    "stoic": {
        "key": "stoic",
        "name": "Stoic",
        "dots": 1,
        "category": "mental",
        "description": "You keep your cool under moral pressure.",
        "tags": ["remorse_bonus"],
    },
    "empathetic": {
        "key": "empathetic",
        "name": "Empathetic",
        "dots": 1,
        "category": "social",
        "description": "You feel the pain of others more acutely.",
        "tags": ["stain_sensitivity"],
    },
}

FLAWS: Dict[str, Dict[str, Any]] = {
    "remorseless": {
        "key": "remorseless",
        "name": "Remorseless",
        "dots": 2,
        "category": "mental",
        "description": "You rarely feel guilt for your actions.",
        "tags": ["remorse_penalty"],
    },
    "short_fuse": {
        "key": "short_fuse",
        "name": "Short Fuse",
        "dots": 1,
        "category": "mental",
        "description": "You are quick to anger and to give in to the Beast.",
        "tags": ["frenzy_prone"],
    },
    "cold_blooded": {
        "key": "cold_blooded",
        "name": "Cold-Blooded",
        "dots": 1,
        "category": "social",
        "description": "Lack of empathy makes it harder to feel true remorse.",
        "tags": ["remorse_penalty"],
    },
}


def list_merits() -> List[Dict[str, Any]]:
    return sorted(MERITS.values(), key=lambda m: m["name"])


def list_flaws() -> List[Dict[str, Any]]:
    return sorted(FLAWS.values(), key=lambda f: f["dots"])


def get_merit(name: str) -> Optional[Dict[str, Any]]:
    key = _norm(name)
    # direct key
    if key in MERITS:
        return MERITS[key]
    # match by display name
    for m in MERITS.values():
        if _norm(m["name"]) == key:
            return m
    return None


def get_flaw(name: str) -> Optional[Dict[str, Any]]:
    key = _norm(name)
    if key in FLAWS:
        return FLAWS[key]
    for f in FLAWS.values():
        if _norm(f["name"]) == key:
            return f
    return None


def merit_tags_for_player(player: Dict[str, Any]) -> List[str]:
    """
    Collects all merit tags for a player.
    """
    from . import character_model  # local import to avoid circular

    character_model.ensure_character_state(player)
    tags: List[str] = []
    for m in player.get("merits", []):
        # if this merit is one of our registry, merge tags
        reg = get_merit(m.get("name", ""))
        if reg:
            tags.extend(reg.get("tags", []))
        else:
            tags.extend(m.get("tags", []))
    return tags


def flaw_tags_for_player(player: Dict[str, Any]) -> List[str]:
    """
    Collects all flaw tags for a player.
    """
    from . import character_model

    character_model.ensure_character_state(player)
    tags: List[str] = []
    for f in player.get("flaws", []):
        reg = get_flaw(f.get("name", ""))
        if reg:
            tags.extend(reg.get("tags", []))
        else:
            tags.extend(f.get("tags", []))
    return tags
from __future__ import annotations

import json
from pathlib import Path
from typing import Dict, Any, List, Optional

_BASE_PATH = Path(__file__).resolve().parent

_DISCIPLINES_CACHE: Optional[Dict[str, Any]] = None
_RITUALS_CACHE: Optional[List[Dict[str, Any]]] = None


def _disciplines_path() -> Path:
    return _BASE_PATH / "disciplines.json"


def _rituals_path() -> Path:
    return _BASE_PATH / "blood_rituals.json"


def load_disciplines() -> Dict[str, Any]:
    """
    Returns:
        {
          "disciplines": {
             "potence": { ... },
             "celerity": { ... },
             ...
          }
        }
    """
    global _DISCIPLINES_CACHE
    if _DISCIPLINES_CACHE is not None:
        return _DISCIPLINES_CACHE
    data = json.loads(_disciplines_path().read_text(encoding="utf-8"))
    _DISCIPLINES_CACHE = data
    return data


def get_discipline(name: str) -> Optional[Dict[str, Any]]:
    """
    Get a single discipline block by id (lowercase key like 'potence').
    """
    data = load_disciplines()
    disc_map = data.get("disciplines", {})
    return disc_map.get(name.lower())


def list_discipline_names() -> List[str]:
    data = load_disciplines()
    return sorted(data.get("disciplines", {}).keys())


def load_blood_rituals() -> List[Dict[str, Any]]:
    """
    Returns a list of ritual definitions.
    """
    global _RITUALS_CACHE
    if _RITUALS_CACHE is not None:
        return _RITUALS_CACHE
    data = json.loads(_rituals_path().read_text(encoding="utf-8"))
    _RITUALS_CACHE = data.get("rituals", [])
    return _RITUALS_CACHE


def find_ritual_by_name(name: str) -> Optional[Dict[str, Any]]:
    name_lower = name.strip().lower()
    for r in load_blood_rituals():
        if r.get("name", "").lower() == name_lower:
            return r
    return None


def list_rituals_for_level(level: int) -> List[Dict[str, Any]]:
    return [r for r in load_blood_rituals() if int(r.get("level", 0)) == int(level)]
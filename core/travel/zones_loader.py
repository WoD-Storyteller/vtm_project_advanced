from __future__ import annotations

import json
from typing import Dict, List, Optional

ZONES_JSON_PATH = "data/zones.json"


class Zone:
    """
    Represents a world zone with everything needed by:
      - Travel engine
      - Map system
      - Director hooks
      - Encounter system
    """

    def __init__(self, data: dict):
        self.key = data.get("key")
        self.name = data.get("name", "")
        self.description = data.get("description", "")
        self.tags = data.get("tags", [])

        self.encounter_table = data.get("encounter_table", "")
        self.base_risk = data.get("base_risk", {})

        # World metadata
        self.region = data.get("region", "")
        self.lat = float(data.get("lat", 0.0))
        self.lng = float(data.get("lng", 0.0))

        # Faction + SI / Hunting risks
        self.faction = data.get("faction", "")
        self.hunting_risk = int(data.get("hunting_risk", 0))
        self.si_risk = int(data.get("si_risk", 0))

        # Multi-map support
        self.mymaps = data.get("mymaps", [])


class ZoneRegistry:
    """
    Manages all world zones.
    """

    def __init__(self):
        self._zones: Dict[str, Zone] = {}

    def load(self, path: str = ZONES_JSON_PATH):
        """
        Loads all zones from the JSON file.
        """
        with open(path, "r", encoding="utf-8") as f:
            raw = json.load(f)

        self._zones = {z["key"]: Zone(z) for z in raw}

    def get(self, key: str) -> Optional[Zone]:
        return self._zones.get(key)

    def list(self) -> List[Zone]:
        return list(self._zones.values())

    def find(self, partial: str) -> Optional[Zone]:
        """
        Fuzzy matching by name.
        """
        p = partial.lower()
        # Direct key match
        if p in self._zones:
            return self._zones[p]
        # Fuzzy name match
        for z in self._zones.values():
            if p in z.name.lower():
                return z
        return None

    def default_zone_key(self) -> str:
        """
        Global fallback if a player has no saved location.
        You can change this after world expansion.
        """
        return "canterbury_domain"
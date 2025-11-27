from __future__ import annotations

import json
from typing import Dict, List, Optional

ZONES_JSON_PATH = "data/zones.json"


class Zone:
    """
    Represents a world zone:
      - Location (lat/lng)
      - Faction & region
      - Travel difficulty / time
      - Risk profiles
      - Map links (MyMaps, KML, etc.)
    """

    def __init__(self, data: dict):
        self.key = data.get("key")
        self.name = data.get("name")
        self.description = data.get("description", "")
        self.tags = data.get("tags", [])

        self.encounter_table = data.get("encounter_table", "")
        self.base_risk = data.get("base_risk", {})

        self.region = data.get("region", "")
        self.lat = data.get("lat", 0.0)
        self.lng = data.get("lng", 0.0)

        self.faction = data.get("faction", "")
        self.hunting_risk = data.get("hunting_risk", 0)
        self.si_risk = data.get("si_risk", 0)

        # How long it takes to move through / to this zone (in abstract "hours")
        # Higher = slower / more dangerous movement.
        self.travel_difficulty = data.get("travel_difficulty", 1)

        # list of dicts: { map_name, layer, label, url }
        self.mymaps = data.get("mymaps", [])


class ZoneRegistry:
    """
    Loads and provides access to all world zones.
    """

    def __init__(self):
        self._zones: Dict[str, Zone] = {}

    def load(self, path: str = ZONES_JSON_PATH):
        """
        Loads all zones from zones.json
        """
        with open(path, "r", encoding="utf-8") as f:
            raw = json.load(f)

        self._zones = {z["key"]: Zone(z) for z in raw}

    def get(self, key: str) -> Optional[Zone]:
        """
        Returns exact zone match by key
        """
        return self._zones.get(key)

    def list(self) -> List[Zone]:
        return list(self._zones.values())

    def find(self, partial: str) -> Optional[Zone]:
        """
        Fuzzy search by name or partial key
        """
        p = partial.lower()

        # Direct key match
        if p in self._zones:
            return self._zones[p]

        # Name fuzzy match
        for z in self._zones.values():
            if p in z.name.lower():
                return z

        return None

    def default_zone_key(self) -> str:
        """
        Global fallback zone.
        Change this if you want a different “starting point”.
        """
        return "canterbury_domain"
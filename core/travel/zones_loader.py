from __future__ import annotations

import json
from typing import Dict, List, Optional

ZONES_JSON_PATH = "data/zones.json"


class Zone:
    def __init__(self, data: dict):
        self.key = data.get("key")
        self.name = data.get("name")
        self.description = data.get("description")
        self.tags = data.get("tags", [])
        self.encounter_table = data.get("encounter_table")
        self.base_risk = data.get("base_risk", {})

        self.region = data.get("region", "")
        self.lat = data.get("lat", 0.0)
        self.lng = data.get("lng", 0.0)
        self.faction = data.get("faction", "")
        self.hunting_risk = data.get("hunting_risk", 0)
        self.si_risk = data.get("si_risk", 0)

        self.mymaps = data.get("mymaps", [])


class ZoneRegistry:
    def __init__(self):
        self._zones: Dict[str, Zone] = {}

    def load(self, path: str = ZONES_JSON_PATH):
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        self._zones = {z["key"]: Zone(z) for z in data}

    def get(self, key: str) -> Optional[Zone]:
        return self._zones.get(key)

    def list(self) -> List[Zone]:
        return list(self._zones.values())

    def find(self, partial: str) -> Optional[Zone]:
        p = partial.lower()
        if p in self._zones:
            return self._zones[p]
        for z in self._zones.values():
            if p in z.name.lower():
                return z
        return None

    def default_zone_key(self) -> str:
        # global default hub (you can change this later)
        return "canterbury_domain"
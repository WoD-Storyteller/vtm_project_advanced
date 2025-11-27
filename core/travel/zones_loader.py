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

    def __init__(
        self,
        key: str,
        name: str,
        region: str = "",
        country: str = "",
        faction: str = "",
        danger: int = 2,
        latitude: Optional[float] = None,
        longitude: Optional[float] = None,
        base_travel_hours: int = 1,
        base_risk: Optional[Dict[str, int]] = None,
        tags: Optional[List[str]] = None,
        neighbours: Optional[List[str]] = None,
        mymaps: Optional[List[Dict[str, str]]] = None,
        encounter_table: Optional[str] = None,
    ):
        self.key = key
        self.name = name
        self.region = region
        self.country = country
        self.faction = faction
        self.danger = int(danger)
        self.latitude = latitude
        self.longitude = longitude
        self.base_travel_hours = int(base_travel_hours)
        self.base_risk: Dict[str, int] = base_risk or {
            "violence": 1,
            "masquerade": 1,
            "si": 1,
            "occult": 1,
        }
        self.tags: List[str] = tags or []
        self.neighbours: List[str] = neighbours or []
        self.mymaps: List[Dict[str, str]] = mymaps or []
        self.encounter_table = encounter_table or "urban_camarilla"

    @classmethod
    def from_dict(cls, data: Dict[str, any]) -> "Zone":
        return cls(
            key=data["key"],
            name=data.get("name", data["key"]),
            region=data.get("region", ""),
            country=data.get("country", ""),
            faction=data.get("faction", ""),
            danger=int(data.get("danger", 2)),
            latitude=data.get("lat"),
            longitude=data.get("lng"),
            base_travel_hours=int(data.get("base_travel_hours", 1)),
            base_risk=data.get("base_risk") or {
                "violence": int(data.get("violence_risk", 1)),
                "masquerade": int(data.get("masquerade_risk", 1)),
                "si": int(data.get("si_risk", 1)),
                "occult": int(data.get("occult_risk", 1)),
            },
            tags=data.get("tags", []),
            neighbours=data.get("neighbours", []),
            mymaps=data.get("mymaps", []),
            encounter_table=data.get("encounter_table"),
        )

    def to_dict(self) -> Dict[str, any]:
        return {
            "key": self.key,
            "name": self.name,
            "region": self.region,
            "country": self.country,
            "faction": self.faction,
            "danger": self.danger,
            "lat": self.latitude,
            "lng": self.longitude,
            "base_travel_hours": self.base_travel_hours,
            "base_risk": self.base_risk,
            "tags": self.tags,
            "neighbours": self.neighbours,
            "mymaps": self.mymaps,
            "encounter_table": self.encounter_table,
        }


class ZoneRegistry:
    """
    Registry for all world zones.

    Backed by data/zones.json which is a list of zone dicts.
    """

    def __init__(self, path: str = ZONES_JSON_PATH):
        self.path = path
        self._zones: Dict[str, Zone] = {}

    def load(self):
        try:
            with open(self.path, "r", encoding="utf-8") as f:
                data = json.load(f)
        except FileNotFoundError:
            data = []
        except Exception:
            data = []

        self._zones = {}
        for raw in data:
            try:
                z = Zone.from_dict(raw)
                self._zones[z.key] = z
            except Exception:
                continue

    def save(self):
        data = [z.to_dict() for z in self._zones.values()]
        with open(self.path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)

    def all(self) -> List[Zone]:
        return list(self._zones.values())

    def get(self, key: str) -> Optional[Zone]:
        return self._zones.get(key)

    def find(self, key_or_name: str) -> Optional[Zone]:
        """
        Try exact key, then partial key, then partial name.
        """
        p = key_or_name.lower().strip()
        if p in self._zones:
            return self._zones[p]

        # key prefix
        for k, z in self._zones.items():
            if k.lower().startswith(p):
                return z

        # name fuzzy
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
from __future__ import annotations

from typing import Dict, Any, List, Optional


class Haven:
    """
    Represents a single Haven / Domain for one or more players.
    """

    def __init__(
        self,
        id: str,
        name: str,
        zone_key: str,
        owner_ids: Optional[List[str]] = None,
        lat: Optional[float] = None,
        lng: Optional[float] = None,
        security: int = 1,
        luxury: int = 1,
        domain: Optional[Dict[str, int]] = None,
        rooms: Optional[List[str]] = None,
        tags: Optional[List[str]] = None,
        maps: Optional[List[Dict[str, str]]] = None,
    ):
        self.id = id
        self.name = name
        self.zone_key = zone_key
        self.owner_ids: List[str] = owner_ids or []
        self.lat = lat
        self.lng = lng
        self.security = int(security)
        self.luxury = int(luxury)
        self.domain: Dict[str, int] = domain or {
            "feeding": 0,
            "masquerade_buffer": 0,
            "warding_level": 0,
            "influence": 0,
        }
        self.rooms: List[str] = rooms or []
        self.tags: List[str] = tags or []
        self.maps: List[Dict[str, str]] = maps or []

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Haven":
        return cls(
            id=data["id"],
            name=data.get("name", data["id"]),
            zone_key=data.get("zone_key", ""),
            owner_ids=list(data.get("owner_ids", [])),
            lat=data.get("lat"),
            lng=data.get("lng"),
            security=int(data.get("security", 1)),
            luxury=int(data.get("luxury", 1)),
            domain=data.get("domain"),
            rooms=list(data.get("rooms", [])),
            tags=list(data.get("tags", [])),
            maps=list(data.get("maps", [])),
        )

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "name": self.name,
            "zone_key": self.zone_key,
            "owner_ids": self.owner_ids,
            "lat": self.lat,
            "lng": self.lng,
            "security": self.security,
            "luxury": self.luxury,
            "domain": self.domain,
            "rooms": self.rooms,
            "tags": self.tags,
            "maps": self.maps,
        }

    def add_owner(self, owner_id: str):
        if owner_id not in self.owner_ids:
            self.owner_ids.append(owner_id)

    def remove_owner(self, owner_id: str):
        if owner_id in self.owner_ids:
            self.owner_ids.remove(owner_id)
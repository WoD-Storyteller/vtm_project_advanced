from __future__ import annotations

from typing import Dict, Any, Optional

from core.travel.zones_loader import ZoneRegistry, Zone
from core.travel.encounters import roll_encounter, is_encounter_triggered


class TravelEngine:
    """
    Handles global travel between world zones.
    Computes:
      - destination zone
      - encounter (if any)
      - abstract time cost (hours)
    """

    def __init__(self, registry: ZoneRegistry):
        self.registry = registry

    def _get_origin_zone(self, player_data: Dict[str, Any]) -> Zone:
        loc_key = player_data.get("location_key") or self.registry.default_zone_key()
        origin = self.registry.get(loc_key)
        if not origin:
            origin = self.registry.get(self.registry.default_zone_key())
        return origin

    def resolve_zone(self, name: str) -> Optional[Zone]:
        name = name.lower()
        zone = self.registry.get(name)
        if zone:
            return zone
        return self.registry.find(name)

    def _compute_time_cost(self, origin: Zone, dest: Zone) -> int:
        """
        Simple travel time model:
        - Cost is max(origin.travel_difficulty, dest.travel_difficulty)
        - Always at least 1 hour.
        """
        return max(1, int(max(origin.travel_difficulty, dest.travel_difficulty)))

    def travel(self, player_data: Dict[str, Any], dest_name: str) -> Dict[str, Any]:
        """
        Returns:
        {
          "success": bool,
          "zone": Zone or None,
          "origin": Zone or None,
          "encounter": {text, severity} or None,
          "msg": str,
          "time_cost": int
        }
        """
        origin = self._get_origin_zone(player_data)
        dest = self.resolve_zone(dest_name)

        if not dest:
            return {
                "success": False,
                "zone": None,
                "origin": origin,
                "encounter": None,
                "msg": f"I can't find a location matching '{dest_name}'.",
                "time_cost": 0,
            }

        # Update player location
        player_data["location_key"] = dest.key

        # Time cost
        time_cost = self._compute_time_cost(origin, dest)

        # Encounter?
        encounter = None
        if is_encounter_triggered(dest.base_risk):
            encounter = roll_encounter(dest.encounter_table)

        return {
            "success": True,
            "zone": dest,
            "origin": origin,
            "encounter": encounter,
            "msg": f"You travel to **{dest.name}**.",
            "time_cost": time_cost,
        }
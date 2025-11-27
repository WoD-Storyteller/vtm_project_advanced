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

    def _compute_time_cost(self, origin: Zone, dest: Zone) -> int:
        """
        Very rough travel time in hours.

        For now:
          - use dest.base_travel_hours as main value
          - if region/country differ, + a bit
        """
        base = dest.base_travel_hours or 1

        if origin.region != dest.region:
            base += 4
        elif origin.country != dest.country:
            base += 2

        return max(1, base)

    def _resolve_zone(self, key_or_name: str) -> Optional[Zone]:
        z = self.registry.find(key_or_name)
        return z

    def travel(
        self,
        player: Dict[str, Any],
        destination_key_or_name: str,
    ) -> Dict[str, Any]:
        """
        Travel a PC from current location_key to a new zone.
        """
        origin_key = player.get("location_key") or self.registry.default_zone_key()
        origin = self.registry.get(origin_key) or self.registry.find(origin_key)

        if not origin:
            # If their origin is invalid, snap them to default
            origin = self.registry.get(self.registry.default_zone_key())

        dest = self._resolve_zone(destination_key_or_name)
        if not dest:
            return {
                "success": False,
                "msg": f"Unknown destination: `{destination_key_or_name}`",
                "zone": None,
            }

        time_cost = self._compute_time_cost(origin, dest)

        encounter = None
        if is_encounter_triggered(dest.base_risk):
            encounter = roll_encounter(dest.encounter_table)

        # Update player location key here
        player["location_key"] = dest.key

        return {
            "success": True,
            "zone": dest,
            "origin": origin,
            "encounter": encounter,
            "msg": f"You travel from **{origin.name}** to **{dest.name}**.",
            "time_cost": time_cost,
        }
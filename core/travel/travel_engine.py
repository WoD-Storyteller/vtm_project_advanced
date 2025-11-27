from __future__ import annotations

from typing import Dict, Any, Optional
from core.travel.zones_loader import ZoneRegistry, Zone
from core.travel.encounters import roll_encounter, is_encounter_triggered
import random


class TravelEngine:
    """
    Handles global travel between world zones.
    """

    def __init__(self, registry: ZoneRegistry):
        self.registry = registry

    # --------------------------------------------------
    # Resolve zone from user input or fuzzy name
    # --------------------------------------------------

    def resolve_zone(self, name: str) -> Optional[Zone]:
        name = name.lower()
        zone = self.registry.get(name)
        if zone:
            return zone
        return self.registry.find(name)

    # --------------------------------------------------
    # Travel attempt: player -> new Zone
    # --------------------------------------------------

    def travel(self, player_data: Dict[str, Any], dest_name: str) -> Dict[str, Any]:
        """
        Returns:
        {
          "success": bool,
          "zone": Zone,
          "encounter": {text, severity} or None,
          "msg": str
        }
        """

        zone = self.resolve_zone(dest_name)
        if not zone:
            return {
                "success": False,
                "zone": None,
                "encounter": None,
                "msg": f"I can't find a location matching '{dest_name}'."
            }

        # Update player location
        player_data["location_key"] = zone.key

        # Try an encounter
        encounter = None
        if is_encounter_triggered(zone.base_risk):
            encounter = roll_encounter(zone.encounter_table)

        return {
            "success": True,
            "zone": zone,
            "encounter": encounter,
            "msg": f"You travel to **{zone.name}**."
        }
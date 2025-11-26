from __future__ import annotations

from typing import Dict, Any, Optional

from core.travel.encounters import roll_encounter, Encounter
from core.travel.zones_loader import ZoneRegistry


class TravelResult:
    def __init__(
        self,
        origin,
        destination,
        encounter: Optional[Encounter],
        narrative: str,
        director_impact: Dict[str, int],
        new_location_key: str,
    ):
        self.origin = origin
        self.destination = destination
        self.encounter = encounter
        self.narrative = narrative
        self.director_impact = director_impact
        self.new_location_key = new_location_key


class TravelEngine:

    def __init__(self, registry: ZoneRegistry):
        self.registry = registry

    def get_zone(self, key: str):
        return self.registry.get(key)

    def travel(self, player_data: Dict[str, Any], dest_key: str) -> TravelResult:
        origin_key = player_data.get("location_key", self.registry.default_zone_key())
        origin = self.get_zone(origin_key)
        dest = self.get_zone(dest_key)

        if not dest:
            dest = origin

        import random
        base_risk = dest.base_risk or {}
        danger = base_risk.get("violence", 1)

        encounter = None
        if random.randint(1, 10) <= danger:
            encounter = roll_encounter(dest.encounter_table)

        name = player_data.get("name", "The Coterie")
        lines = []

        if origin_key == dest.key:
            lines.append(f"{name} moves within **{dest.name}**.")
        else:
            lines.append(f"{name} travels from **{origin.name}** to **{dest.name}**.")

        if encounter:
            lines.append(f"Encounter: **{encounter.name}**")
            lines.append(encounter.summary)
        else:
            lines.append("The journey passes without incident.")

        impact = {
            "violence": 0,
            "masquerade": 0,
            "second_inquisition": 0,
            "occult": 0,
        }

        if encounter:
            sev = encounter.base_severity
            tags = set(encounter.tags)
            if "violence" in tags:
                impact["violence"] += sev
            if "masquerade" in tags:
                impact["masquerade"] += sev
            if "second_inquisition" in tags:
                impact["second_inquisition"] += sev
            if "occult" in tags:
                impact["occult"] += sev

        player_data["location_key"] = dest.key

        return TravelResult(
            origin=origin,
            destination=dest,
            encounter=encounter,
            narrative="\n".join(lines),
            director_impact=impact,
            new_location_key=dest.key
        )
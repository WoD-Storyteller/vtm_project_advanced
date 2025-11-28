from __future__ import annotations

from typing import Dict, Any, Optional, List

from .haven_registry import HavenRegistry
from .haven_model import Haven
from core.travel.zones_loader import ZoneRegistry
from core.vtmv5 import character_model
from core.director.ai_director import _DIRECTOR_STATE


class HavenEngine:
    """
    High-level operations on Havens:
      - create
      - assign owners
      - compute domain effects
      - apply small Director adjustments
    """

    def __init__(self, haven_registry: HavenRegistry, zone_registry: ZoneRegistry):
        self.havens = haven_registry
        self.zones = zone_registry

    # -------------------------------------------------
    # Core operations
    # -------------------------------------------------
    def create_haven_for_player(
        self,
        player_id: str,
        name: str,
        zone_key: str,
        lat: float | None = None,
        lng: float | None = None,
    ) -> Haven:
        """
        Creates a new haven in the given zone and assigns the owner.
        ID is generated as: haven_<zone>_<slug of name>.
        """
        base_key = zone_key.lower().replace(" ", "_")
        slug = name.lower().replace(" ", "_")
        haven_id = f"haven_{base_key}_{slug}"

        # Ensure uniqueness
        i = 1
        unique_id = haven_id
        while self.havens.get(unique_id):
            unique_id = f"{haven_id}_{i}"
            i += 1

        h = Haven(
            id=unique_id,
            name=name,
            zone_key=zone_key.lower(),
            owner_ids=[player_id],
            lat=lat,
            lng=lng,
        )
        self.havens.upsert(h)
        self.havens.save()
        return h

    def get_player_havens(self, player_id: str) -> List[Haven]:
        return self.havens.list_for_owner(player_id)

    def get_player_havens_in_zone(self, player_id: str, zone_key: str) -> List[Haven]:
        return self.havens.list_for_owner_in_zone(player_id, zone_key)

    def get_haven_by_id_or_name(self, token: str) -> Optional[Haven]:
        h = self.havens.get(token)
        if h:
            return h
        return self.havens.find_by_name(token)

    # -------------------------------------------------
    # Director / Domain effects (light touch)
    # -------------------------------------------------
    def apply_shelter_effects(self, haven: Haven):
        """
        When a character retreats to their haven, we can gently nudge Director state:
          - security & warding lower Masquerade / SI pressure a bit
          - influence & masquerade_buffer lower city awareness slightly
        """
        sec = haven.security
        ward = haven.domain.get("warding_level", 0)
        mbuf = haven.domain.get("masquerade_buffer", 0)
        infl = haven.domain.get("influence", 0)

        # Better defenses = safer streets, less obvious chaos
        _DIRECTOR_STATE.adjust("masquerade_pressure", -max(0, sec // 2))
        _DIRECTOR_STATE.adjust("si_pressure", -max(0, ward // 2))

        # Influence / buffer dampen how big things feel to mortals
        _DIRECTOR_STATE.adjust("awareness", -max(0, (mbuf + infl) // 2))

        _DIRECTOR_STATE.save()
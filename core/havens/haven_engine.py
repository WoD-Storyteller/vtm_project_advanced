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
      - create & query
      - rest / recovery inside a haven
      - apply Director shelter effects
      - handle raids & domain upgrades
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
    # Director / Domain effects
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

    def apply_raid(self, haven: Haven, severity: int = 3) -> Dict[str, Any]:
        """
        Represents a raid / attack on a haven.
        severity: 1–5
        - Raises Director pressures
        - Damages haven security / warding / influence a bit
        """
        severity = max(1, min(5, int(severity)))

        # Director impact
        _DIRECTOR_STATE.adjust("violence_pressure", severity + 1)
        _DIRECTOR_STATE.adjust("masquerade_pressure", severity)
        _DIRECTOR_STATE.adjust("si_pressure", max(0, severity - 1))
        _DIRECTOR_STATE.adjust("awareness", severity // 2)

        # Haven damage
        haven.security = max(0, haven.security - (severity // 2))
        haven.domain["warding_level"] = max(
            0,
            haven.domain.get("warding_level", 0) - (severity // 2),
        )
        haven.domain["influence"] = max(
            0,
            haven.domain.get("influence", 0) - (severity // 2),
        )

        self.havens.upsert(haven)
        self.havens.save()
        _DIRECTOR_STATE.save()

        return {
            "haven": haven.to_dict(),
            "director": _DIRECTOR_STATE.summarize(),
            "severity": severity,
        }

    def upgrade_domain(self, haven: Haven, stat: str, delta: int) -> Haven:
        """
        ST-facing helper to tweak haven/domain stats.
        stat can be:
          - security
          - luxury
          - feeding
          - masquerade_buffer
          - warding
          - influence
        """
        stat = stat.lower().strip()
        delta = int(delta)

        if stat == "security":
            haven.security = max(0, min(5, haven.security + delta))
        elif stat == "luxury":
            haven.luxury = max(0, min(5, haven.luxury + delta))
        elif stat in ("feeding", "masquerade_buffer", "warding", "influence"):
            key_map = {
                "feeding": "feeding",
                "masquerade_buffer": "masquerade_buffer",
                "warding": "warding_level",
                "influence": "influence",
            }
            dk = key_map[stat]
            current = haven.domain.get(dk, 0)
            haven.domain[dk] = max(0, min(5, current + delta))
        else:
            # unknown stat – no change
            return haven

        self.havens.upsert(haven)
        self.havens.save()
        return haven

    # -------------------------------------------------
    # Rest / recovery inside haven
    # -------------------------------------------------
    def rest_in_haven(
        self,
        player: Dict[str, Any],
        haven: Haven,
    ) -> Dict[str, Any]:
        """
        Apply rest/recuperation effects for a PC resting in a haven.

        - Rest recovers superficial Willpower (based on luxury)
        - May reduce 1 stain if haven is comfy enough
        - May reduce hunger slightly if domain feeding is strong
        - Applies shelter effects to Director
        """
        character_model.ensure_character_state(player)

        # --- Willpower recovery ---
        wp_before = character_model.current_willpower(player)
        sup_before = player["willpower"]["superficial"]

        # Simple rule: 1 + luxury//2 superficial WP
        wp_recover = 1 + max(0, haven.luxury // 2)
        # We represent recovery as negative superficial damage
        character_model.set_willpower_damage(player, superficial_delta=-wp_recover)
        wp_after = character_model.current_willpower(player)
        sup_after = player["willpower"]["superficial"]

        # --- Stains ---
        stains_before = character_model.get_stains(player)
        stains_recovered = 0
        if haven.luxury >= 3:
            # One stain may clear after introspection & safety
            stains_recovered = 1
            character_model.adjust_stains(player, -1)
        stains_after = character_model.get_stains(player)

        # --- Hunger ---
        hunger_before = character_model.get_hunger(player)
        hunger_change = 0
        feeding_rating = haven.domain.get("feeding", 0)
        if feeding_rating >= 2 and hunger_before > 1:
            # An abstract "fridge full of bags / willing herd"
            hunger_change = -1
            character_model.set_hunger(player, hunger_before - 1)
        hunger_after = character_model.get_hunger(player)

        # --- Director shelter effect ---
        self.apply_shelter_effects(haven)
        director_summary = _DIRECTOR_STATE.summarize()

        return {
            "willpower_before": wp_before,
            "willpower_after": wp_after,
            "superficial_before": sup_before,
            "superficial_after": sup_after,
            "stains_before": stains_before,
            "stains_after": stains_after,
            "stains_recovered": stains_recovered,
            "hunger_before": hunger_before,
            "hunger_after": hunger_after,
            "hunger_change": hunger_change,
            "director": director_summary,
        }
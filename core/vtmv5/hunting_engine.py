from __future__ import annotations

from typing import Dict, Any

from . import dice, hunger, character_model
from core.travel.zones_loader import Zone


class HuntingEngine:
    """
    V5-compatible hunting system with Predator Type hooks.
    """

    def __init__(self):
        pass

    def _base_pool_for_zone(self, zone: Zone) -> Dict[str, Any]:
        """
        Compute a dice pool + narrative notes from the zone.

        This is deliberately abstract:
        - We treat zone.danger and risk profile as rough difficulty hints.
        """
        pool = 3  # base hunting skill pool
        notes = []

        if zone.danger >= 4:
            pool += 1
            notes.append("Hostile domain: danger sharpens your senses.")
        elif zone.danger <= 2:
            pool -= 1
            notes.append("Thin pickings: safe but starved streets.")

        if "rack" in zone.tags:
            pool += 1
            notes.append("Feeding ground: easy prey on the Rack.")

        if "si_hotspot" in zone.tags:
            notes.append("Second Inquisition presence makes things riskier.")

        return {"dice_pool": max(1, pool), "notes": notes}

    def _apply_predator_type_mods(
        self,
        player: Dict[str, Any],
        zone: Zone,
        base_pool: int,
        notes: list[str],
    ) -> int:
        """
        Modify pool based on predator type & zone tags.
        """
        ptype = character_model.get_predator_type_key(player)

        if not ptype:
            return base_pool

        # Very light-touch; detailed logic can go into predator_types module later
        if ptype == "sandman" and "suburb" in zone.tags:
            base_pool += 1
            notes.append("Sandman in sleepy suburbs: easy bedside meals.")

        if ptype == "farmer" and "rural" in zone.tags:
            base_pool += 1
            notes.append("Farmer among livestock & donors.")

        if ptype == "osiris" and "club" in zone.tags:
            base_pool += 1
            notes.append("Osiris in their temple of adoration.")

        if ptype == "bagger" and "hospital" in zone.tags:
            base_pool += 1
            notes.append("Bagger close to the blood supply.")

        return max(1, base_pool)

    def hunt(self, player: Dict[str, Any], zone: Zone) -> Dict[str, Any]:
        """
        Perform a full hunting action in a zone.
        """
        character_model.ensure_character_state(player)
        hunger_val = character_model.get_hunger(player)

        base = self._base_pool_for_zone(zone)
        pool = base["dice_pool"]
        notes = list(base["notes"])

        pool = self._apply_predator_type_mods(player, zone, pool, notes)

        difficulty = max(2, zone.danger)  # rough rule of thumb

        roll_result = dice.roll_pool(
            dice_pool=pool,
            hunger=hunger_val,
            difficulty=difficulty,
        )

        successes = roll_result.get("successes", 0)
        messy = roll_result.get("messy_critical", False)
        bestial = roll_result.get("bestial_failure", False)

        feed_amount = 0
        source = "human"

        if successes <= 0:
            feed_amount = 0
            notes.append("You fail to find a viable feeding opportunity.")
        elif successes == 1:
            feed_amount = 1
            notes.append("You scrape together a small meal.")
        elif successes == 2:
            feed_amount = 2
            notes.append("You feed adequately.")
        else:
            feed_amount = 3
            notes.append("You gorge yourself on a rich vessel.")

        if messy:
            notes.append("Messy critical: the Beast surges through the hunt.")
        if bestial:
            notes.append("Bestial failure taints this hunt.")

        feeding_result = hunger.apply_feeding(
            player,
            source=source,
            amount=feed_amount,
        )

        return {
            "zone_name": zone.name,
            "zone_key": zone.key,
            "dice_pool": pool,
            "hunger_before": hunger_val,
            "dice_result": roll_result,
            "feeding_result": feeding_result,
            "predator_type": character_model.get_predator_type_name(player),
            "notes": notes,
        }
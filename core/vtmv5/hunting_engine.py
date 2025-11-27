from __future__ import annotations

from typing import Dict, Any

from core.vtmv5 import dice, hunger, character_model
from core.travel.zones_loader import Zone


class HuntingEngine:
    """
    V5-compatible hunting system with Predator Type hooks.
    """

    def __init__(self):
        pass

    # ------------------------------------------------------------------
    # INTERNAL: build dice pool with Predator modifiers
    # ------------------------------------------------------------------
    def _hunt_dice_pool(self, player: Dict[str, Any], zone: Zone) -> Dict[str, Any]:
        """
        Returns the dice pool after Predator Type + zone modifiers.
        """
        pred_key = character_model.get_predator_key(player)
        character_model.ensure_character_state(player)

        # Baseline: abstract hunting dice = 4 + zone.hunting_risk
        dice_pool = 4 + int(getattr(zone, "hunting_risk", 0))
        bonus_notes = []

        # Violence risk tag
        violence_risk = zone.base_risk.get("violence", 0) if getattr(zone, "base_risk", None) else 0
        tags = zone.tags or []

        # --- Alleycat: better in violent zones ---
        if pred_key == "alleycat":
            if violence_risk >= 3:
                dice_pool += 2
                bonus_notes.append("Alleycat: +2 dice hunting in high-violence zones.")

        # --- Siren: better in nightlife / social zones ---
        elif pred_key == "siren":
            if "nightlife" in tags or "siren_feeding" in tags:
                dice_pool += 2
                bonus_notes.append("Siren: +2 dice in nightlife/social zones.")

        # --- Consensualist: penalized if zone not marked consensual ---
        elif pred_key == "consensualist":
            if "consensual" not in tags:
                dice_pool -= 2
                bonus_notes.append("Consensualist: -2 dice (zone is not consent-friendly).")

        # --- Farmer: better in animal-rich zones ---
        elif pred_key == "farmer":
            if "animal" in tags or "rural" in tags:
                dice_pool += 2
                bonus_notes.append("Farmer: +2 dice in animal/rural zones.")

        # --- Sandman: better with sleepers ---
        elif pred_key == "sandman":
            if "sleepers" in tags or "residential" in tags:
                dice_pool += 2
                bonus_notes.append("Sandman: +2 dice feeding from sleeping victims.")

        # --- Graverobber: better in death-adjacent zones ---
        elif pred_key == "graverobber":
            if any(t in tags for t in ("graveyard", "mortuary", "hospital")):
                dice_pool += 2
                bonus_notes.append("Graverobber: +2 dice in graveyards/mortuaries/hospitals.")

        # --- Bagger: better in medical zones ---
        elif pred_key == "bagger":
            if any(t in tags for t in ("hospital", "clinic", "medical")):
                dice_pool += 2
                bonus_notes.append("Bagger: +2 dice in medical zones.")

        # --- Osiris: better in cult/temple/venue spaces ---
        elif pred_key == "osiris":
            if any(t in tags for t in ("cult", "worship", "performance", "stage", "temple")):
                dice_pool += 2
                bonus_notes.append("Osiris: +2 dice in cult/temple/performance venues.")

        # --- Blood Leech: better where Kindred congregate ---
        elif pred_key == "blood_leech":
            if "kindred_activity" in tags:
                dice_pool += 2
                bonus_notes.append("Blood Leech: +2 dice where other Kindred are active.")

        # Floor at 1 die so you always roll something
        dice_pool = max(1, dice_pool)

        return {
            "dice_pool": dice_pool,
            "notes": bonus_notes,
        }

    # ------------------------------------------------------------------
    # INTERNAL: determine feeding source from predator + zone
    # ------------------------------------------------------------------
    def _determine_source(self, player: Dict[str, Any], zone: Zone) -> str:
        """
        Decide whether this hunt is effectively human/animal/bagged/vampire feeding.
        """
        pred_key = character_model.get_predator_key(player)
        tags = zone.tags or []

        source = "human"  # default

        if pred_key == "farmer":
            source = "animal"
        elif pred_key == "graverobber" and any(t in tags for t in ("graveyard", "mortuary", "hospital")):
            source = "bagged"
        elif pred_key == "bagger" and any(t in tags for t in ("hospital", "clinic", "medical")):
            source = "bagged"
        elif pred_key == "blood_leech" and "kindred_activity" in tags:
            source = "vampire"

        return source

    # ------------------------------------------------------------------
    # PUBLIC: main hunt entrypoint
    # ------------------------------------------------------------------
    def hunt(self, player: Dict[str, Any], zone: Zone) -> Dict[str, Any]:
        """
        Performs a Predator-type–aware V5 hunting roll in the given zone.

        Steps:
          • Build dice pool (with predator + zone modifiers)
          • Roll V5 pool with hunger dice
          • Determine feeding source (human/animal/bagged/vampire)
          • Apply feeding via hunger.apply_feeding
        """
        character_model.ensure_character_state(player)

        # Build pool
        dice_block = self._hunt_dice_pool(player, zone)
        pool = dice_block["dice_pool"]

        # Roll
        hunger_val = character_model.get_hunger(player)
        roll_result = dice.roll_pool(dice_pool=pool, hunger=hunger_val, difficulty=1)

        # Determine feeding source
        source = self._determine_source(player, zone)

        # Feeding strength: 1 = weak, 2 = decent, 3 = feast
        feed_amount = 1
        if roll_result["total_success"]:
            feed_amount = 2
        if roll_result["critical_pairs"] > 0:
            feed_amount = 3

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
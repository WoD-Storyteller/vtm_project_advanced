from __future__ import annotations
from typing import Dict, Any

from core.combat.advanced_combat_engine import Combatant


class CombatantFactory:
    """
    Converts Guild Player/NPC Data -> Combatant
    """

    @staticmethod
    def from_player(user_id: str, player_data: Dict[str, Any]) -> Combatant:
        attributes = player_data.get("attributes", {}) or {}
        skills = player_data.get("skills", {}) or {}
        disciplines = player_data.get("disciplines", {}) or {}

        # Health Pools
        health = player_data.get("health", {}) or {}
        hp_superficial = int(health.get("superficial", 0))
        hp_aggravated = int(health.get("aggravated", 0))
        max_hp = int(health.get("max", 10))

        # Willpower
        will = player_data.get("willpower", {}) or {}
        wp_superficial = int(will.get("superficial", 0))
        wp_aggravated = int(will.get("aggravated", 0))

        hunger = int(player_data.get("hunger", 1))
        fortitude = CombatantFactory._derive_fortitude(player_data, disciplines)

        return Combatant(
            name=player_data.get("name") or f"Player {user_id}",
            is_vampire=True,
            hp_superficial=hp_superficial,
            hp_aggravated=hp_aggravated,
            max_hp=max_hp,
            hunger=hunger,
            willpower_superficial=wp_superficial,
            willpower_aggravated=wp_aggravated,
            defense=CombatantFactory._derive_defense(attributes, skills),
            fortitude=fortitude,
            attributes=attributes,
            skills=skills,
            disciplines=disciplines,
        )

    @staticmethod
    def from_npc(name: str, npc_data: Dict[str, Any]) -> Combatant:
        attributes = npc_data.get("attributes", {}) or {}
        skills = npc_data.get("skills", {}) or {}

        health = npc_data.get("health", {}) or {}
        hp_superficial = int(health.get("superficial", 0))
        hp_aggravated = int(health.get("aggravated", 0))
        max_hp = int(health.get("max", 7))

        is_vampire = bool(npc_data.get("is_vampire", False))
        hunger = 1 if is_vampire else 0

        disciplines = npc_data.get("disciplines", {}) or {}

        return Combatant(
            name=name,
            is_vampire=is_vampire,
            hp_superficial=hp_superficial,
            hp_aggravated=hp_aggravated,
            max_hp=max_hp,
            hunger=hunger,
            willpower_superficial=int(npc_data.get("willpower_superficial", 0)),
            willpower_aggravated=int(npc_data.get("willpower_aggravated", 0)),
            defense=CombatantFactory._derive_defense(attributes, skills),
            fortitude=int(npc_data.get("fortitude", 0)),
            attributes=attributes,
            skills=skills,
            disciplines=disciplines,
        )

    @staticmethod
    def _derive_defense(attributes: Dict[str, int], skills: Dict[str, int]) -> int:
        """
        V5 defense: wits + athletics OR wits + brawl, whichever higher.
        """
        wits = attributes.get("wits", 2)
        athletics = skills.get("athletics", 0)
        brawl = skills.get("brawl", 0)
        return max(wits + athletics, wits + brawl)

    @staticmethod
    def _derive_fortitude(player_data: Dict[str, Any], disciplines: Dict[str, int]) -> int:
        # If explicitly on sheet:
        if "fortitude" in player_data:
            return int(player_data["fortitude"])

        # If discipline is on sheet:
        fortitude_disc = disciplines.get("fortitude", 0)
        if fortitude_disc:
            return int(fortitude_disc)

        # Fallback clan-based guess
        clan = (player_data.get("clan") or "").lower()
        if clan in ["gangrel", "ventrue", "ravnos"]:
            return 1

        return 0
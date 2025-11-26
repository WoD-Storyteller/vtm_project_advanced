from __future__ import annotations
from typing import Dict, Any

from core.combat.advanced_combat_engine import Combatant


class CombatantFactory:
    """
    Converts Guild Player Data -> Combatant
    Converts NPC Data -> Combatant
    """

    @staticmethod
    def from_player(user_id: str, player_data: Dict[str, Any]) -> Combatant:
        """
        Create a Combatant object from a player character sheet.
        """
        # Attributes fallback
        attributes = player_data.get("attributes", {})
        skills = player_data.get("skills", {})

        # Health Pools
        health = player_data.get("health", {})
        hp_superficial = int(health.get("superficial", 0))
        hp_aggravated = int(health.get("aggravated", 0))

        # Willpower Pools
        will = player_data.get("willpower", {})
        wp_superficial = int(will.get("superficial", 0))
        wp_aggravated = int(will.get("aggravated", 0))

        max_hp = health.get("max", 10)  # fallback if not defined

        # Hunger
        hunger = int(player_data.get("hunger", 1))

        # Fortitude
        fortitude = CombatantFactory._derive_fortitude(player_data)

        c = Combatant(
            name=player_data.get("name"),
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
        )

        return c

    @staticmethod
    def from_npc(name: str, npc_data: Dict[str, Any]) -> Combatant:
        """
        Convert NPC sheet into Combatant.
        NPCs default to mortals unless specified.
        """
        attributes = npc_data.get("attributes", {})
        skills = npc_data.get("skills", {})

        health = npc_data.get("health", {})
        hp_superficial = int(health.get("superficial", 0))
        hp_aggravated = int(health.get("aggravated", 0))
        max_hp = health.get("max", 7)

        is_vampire = npc_data.get("is_vampire", False)
        hunger = 1 if is_vampire else 0

        return Combatant(
            name=name,
            is_vampire=is_vampire,
            hp_superficial=hp_superficial,
            hp_aggravated=hp_aggravated,
            max_hp=max_hp,
            hunger=hunger,
            willpower_superficial=0,
            willpower_aggravated=0,
            defense=CombatantFactory._derive_defense(attributes, skills),
            fortitude=npc_data.get("fortitude", 0),
            attributes=attributes,
            skills=skills,
        )

    # ------------ INTERNAL HELPERS ------------ #

    @staticmethod
    def _derive_defense(attributes: Dict[str, int], skills: Dict[str, int]) -> int:
        """
        V5 defense is based on wits + athletics OR wits + brawl (whichever best).
        """
        wits = attributes.get("wits", 2)
        athletics = skills.get("athletics", 0)
        brawl = skills.get("brawl", 0)

        return max(wits + athletics, wits + brawl)

    @staticmethod
    def _derive_fortitude(player_data: Dict[str, Any]) -> int:
        """
        Estimate Fortitude score based on clan or explicit sheet entry.
        """
        # If explicitly provided
        if "fortitude" in player_data:
            return player_data["fortitude"]

        clan = player_data.get("clan", "").lower()

        # Auto-assign base fortitude for clans that inherently get it
        if clan in ["gangrel", "ventrue", "ravnos"]:
            return 1

        return 0
from __future__ import annotations
from typing import Optional, Dict, List
from random import randint

class FrenzyTrigger:
    BESTIAL_FAILURE = "bestial_failure"
    MESSY_CRITICAL = "messy_critical"
    HUNGER_FOUR = "hunger_4"
    AGGRAVATED_TAKEN = "agg_damage"
    FEAR_FIRE = "fear_fire"
    FEAR_SUN = "fear_sun"


class FrenzySystem:
    """
    Handles Frenzy triggers, rolls, and state tracking.
    """

    active_frenzies: Dict[str, Dict] = {}  # combatant_name -> data

    @staticmethod
    def check_trigger(trigger: str, combatant) -> bool:
        """
        Determine if a trigger SHOULD cause frenzy (based on hunger, humanity).
        """
        # Hunger 4+ auto-increases frenzy risk
        if combatant.hunger >= 4:
            return True

        # Fear frenzy is always possible
        if trigger in [FrenzyTrigger.FEAR_FIRE, FrenzyTrigger.FEAR_SUN]:
            return True

        # Messy crits often escalate
        if trigger == FrenzyTrigger.MESSY_CRITICAL:
            return True

        # Bestial failures almost always cause a frenzy
        if trigger == FrenzyTrigger.BESTIAL_FAILURE:
            return True

        # Taking aggravated damage can set vampires off
        if trigger == FrenzyTrigger.AGGRAVATED_TAKEN:
            return True

        return False

    @staticmethod
    def frenzy_roll(combatant, difficulty: int = 3) -> bool:
        """
        A Resolve + Composure roll.
        Hunger adds hunger dice.
        Difficulty defaults to 3 unless trigger modifies it.

        Returns:
            True = frenzy
            False = resist
        """
        resolve = combatant.attributes.get("resolve", 2)
        composure = combatant.attributes.get("composure", 2)
        pool = resolve + composure

        hunger = combatant.hunger
        hunger_dice = min(hunger, pool)
        normal = pool - hunger_dice

        rolls = [randint(1, 10) for _ in range(normal)]
        hunger_rolls = [randint(1, 10) for _ in range(hunger_dice)]

        successes = sum(1 for r in rolls + hunger_rolls if r >= 6)

        # Frenzy fails
        if successes < difficulty:
            return True  # frenzy
        return False     # resisted

    @staticmethod
    def apply_frenzy(combatant, trigger: str):
        FrenzySystem.active_frenzies[combatant.name] = {
            "trigger": trigger,
            "locked_target": None
        }

    @staticmethod
    def clear_frenzy(combatant_name: str):
        FrenzySystem.active_frenzies.pop(combatant_name, None)

    @staticmethod
    def is_frenzied(combatant_name: str) -> bool:
        return combatant_name in FrenzySystem.active_frenzies
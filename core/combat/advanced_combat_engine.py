from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from random import randint
from typing import Dict, List, Optional
import math

from core.combat.frenzy_system import FrenzySystem, FrenzyTrigger


class AttackOutcome(str, Enum):
    FAIL = "fail"
    SUCCESS = "success"
    MESSY_CRITICAL = "messy_critical"
    BESTIAL_FAILURE = "bestial_failure"


class DamageType(str, Enum):
    SUPERFICIAL = "superficial"
    AGGRAVATED = "aggravated"


@dataclass
class DiceResult:
    pool: int
    hunger: int
    normal_rolls: List[int]
    hunger_rolls: List[int]
    successes: int
    outcome: AttackOutcome


@dataclass
class Combatant:
    name: str
    is_vampire: bool = True
    hp_superficial: int = 0
    hp_aggravated: int = 0
    max_hp: int = 10
    hunger: int = 1
    willpower_superficial: int = 0
    willpower_aggravated: int = 0
    defense: int = 1
    fortitude: int = 0
    attributes: Dict[str, int] = field(default_factory=dict)
    skills: Dict[str, int] = field(default_factory=dict)

    def is_defeated(self) -> bool:
        return (self.hp_superficial + self.hp_aggravated) >= self.max_hp


class CombatEngine:
    """
    Advanced V5-style combat engine with:
    - Hunger dice
    - Messy crits / Bestial failures
    - Superficial vs Aggravated
    - Fortitude
    - Frenzy integration
    """

    def __init__(self):
        # name -> Combatant
        self.combatants: Dict[str, Combatant] = {}

    # ---------- Management ----------

    def add_combatant(self, combatant: Combatant):
        self.combatants[combatant.name] = combatant

    def get_combatant(self, name: str) -> Optional[Combatant]:
        return self.combatants.get(name)

    # ---------- Dice + Hunger ----------

    @staticmethod
    def roll_dice(pool: int, hunger: int) -> DiceResult:
        hunger = max(0, min(hunger, pool))
        normal = pool - hunger

        normal_rolls = [randint(1, 10) for _ in range(normal)]
        hunger_rolls = [randint(1, 10) for _ in range(hunger)]

        all_rolls = normal_rolls + hunger_rolls

        successes = sum(1 for r in all_rolls if r >= 6)

        tens = [r for r in all_rolls if r == 10]
        crit_pairs = len(tens) // 2
        successes += crit_pairs * 2  # V5 crit pairs

        outcome = AttackOutcome.SUCCESS

        # Messy crit / Bestial failure
        if crit_pairs > 0 and any(r == 10 for r in hunger_rolls):
            outcome = AttackOutcome.MESSY_CRITICAL
        if successes == 0 and any(r == 1 for r in hunger_rolls):
            outcome = AttackOutcome.BESTIAL_FAILURE

        # Plain failure
        if successes == 0 and outcome == AttackOutcome.SUCCESS:
            outcome = AttackOutcome.FAIL

        return DiceResult(
            pool=pool,
            hunger=hunger,
            normal_rolls=normal_rolls,
            hunger_rolls=hunger_rolls,
            successes=successes,
            outcome=outcome,
        )

    # ---------- Rouse ----------

    @staticmethod
    def rouse_check() -> bool:
        """Returns True on success, False if hunger should increase."""
        r = randint(1, 10)
        return r >= 6

    # ---------- Damage Application ----------

    def apply_damage(
        self,
        target: Combatant,
        damage: int,
        damage_type: DamageType,
    ) -> Dict[str, int]:
        """
        Apply damage under V5 rules:
        - Vampires halve superficial (round up)
        - Aggravated always full
        - Mortals treat everything as effectively lethal (we treat as aggravated)
        - Fortitude reduces
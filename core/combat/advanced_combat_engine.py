from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional
from random import randint
import math

from core.combat.attack_outcomes import AttackOutcome
from core.combat.frenzy_system import FrenzySystem, FrenzyTrigger
from core.combat.bestial_chaos import roll_bestial_chaos
from core.director.director import Director   # AI Director integration


@dataclass
class DiceResult:
    pool: int
    hunger: int
    normal_rolls: List[int]
    hunger_rolls: List[int]
    successes: int
    outcome: AttackOutcome
    bestial_chaos: Optional[str] = None


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
    def __init__(self):
        self.combatants: Dict[str, Combatant] = {}

    # ---------------------------------------------------------
    #  MANAGEMENT
    # ---------------------------------------------------------

    def add_combatant(self, combatant: Combatant):
        self.combatants[combatant.name] = combatant

    def get_combatant(self, name: str) -> Optional[Combatant]:
        return self.combatants.get(name)

    # ---------------------------------------------------------
    #  DICE + HUNGER MECHANICS
    # ---------------------------------------------------------

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
        successes += crit_pairs * 2

        # default outcome
        outcome = AttackOutcome.SUCCESS
        chaos = None

        # special hunger triggers
        has_hunger_one = any(r == 1 for r in hunger_rolls)
        messy_crit = crit_pairs > 0 and any(r == 10 for r in hunger_rolls)
        bestial_fail = (successes == 0) and has_hunger_one

        if messy_crit:
            outcome = AttackOutcome.MESSY_CRITICAL

        elif bestial_fail:
            outcome = AttackOutcome.BESTIAL_FAILURE

        # BESTIAL SUCCESS LOGIC
        elif has_hunger_one and successes > 0:
            # Not messy, not failure → BESTIAL SUCCESS
            outcome = AttackOutcome.BESTIAL_SUCCESS
            chaos = roll_bestial_chaos()

        # simple fail without beast influence
        elif successes == 0:
            outcome = AttackOutcome.FAIL

        return DiceResult(
            pool=pool,
            hunger=hunger,
            normal_rolls=normal_rolls,
            hunger_rolls=hunger_rolls,
            successes=successes,
            outcome=outcome,
            bestial_chaos=chaos
        )

    # ---------------------------------------------------------
    #  ROUSE
    # ---------------------------------------------------------

    @staticmethod
    def rouse_check() -> bool:
        return randint(1, 10) >= 6

    # ---------------------------------------------------------
    #  DAMAGE SYSTEM
    # ---------------------------------------------------------

    def apply_damage(self, target: Combatant, damage: int, aggravated: bool):
        if damage <= 0:
            return {
                "applied_superficial": 0,
                "applied_aggravated": 0,
                "remaining_hp_superficial": target.hp_superficial,
                "remaining_hp_aggravated": target.hp_aggravated,
            }

        # Fortitude negation
        damage = max(0, damage - target.fortitude)

        if aggravated:
            applied_a = min(damage, target.max_hp - target.hp_superficial - target.hp_aggravated)
            target.hp_aggravated += applied_a
            applied_s = 0
        else:
            # vampires halve superficial
            reduced = math.ceil(damage / 2)
            applied_s = min(reduced, target.max_hp - target.hp_superficial - target.hp_aggravated)
            applied_a = 0
            target.hp_superficial += applied_s

        # frenzy check for aggravated
        if applied_a > 0 and target.is_vampire:
            if FrenzySystem.check_trigger(FrenzyTrigger.AGGRAVATED_TAKEN, target):
                FrenzySystem.apply_frenzy(target, FrenzyTrigger.AGGRAVATED_TAKEN)

        return {
            "applied_superficial": applied_s,
            "applied_aggravated": applied_a,
            "remaining_hp_superficial": target.hp_superficial,
            "remaining_hp_aggravated": target.hp_aggravated,
        }

    # ---------------------------------------------------------
    #  ATTACK RESOLUTION
    # ---------------------------------------------------------

    def attack(self, attacker_name: str, defender_name: str, weapon: dict):
        attacker = self.get_combatant(attacker_name)
        defender = self.get_combatant(defender_name)

        attrs = attacker.attributes
        skills = attacker.skills

        if weapon.get("type") == "ranged":
            pool = attrs.get("dexterity", 2) + skills.get("firearms", 0)
        else:
            pool = attrs.get("strength", 2) + max(skills.get("melee", 0), skills.get("brawl", 0))

        pool += weapon.get("base_dice", 0)

        dice = self.roll_dice(pool, attacker.hunger)

        # NET SUCCESSES
        net = dice.successes - defender.defense
        damage = max(0, net - 1)  # diff 2 baseline

        # BESTIAL SUCCESS EXTRA DAMAGE
        if dice.outcome == AttackOutcome.BESTIAL_SUCCESS:
            damage += 1

        aggravated = weapon.get("damage_type") == "aggravated"

        dmg_report = self.apply_damage(defender, damage, aggravated)

        # DIRECTOR HOOKS
        if dice.outcome in [AttackOutcome.BESTIAL_SUCCESS, AttackOutcome.MESSY_CRITICAL]:
            Director.modify_influence("violence", +1)

        if dice.outcome == AttackOutcome.BESTIAL_FAILURE:
            Director.modify_influence("masquerade", +1)

        if dice.outcome == AttackOutcome.MESSY_CRITICAL:
            Director.modify_influence("violence", +2)

        if dice.outcome == AttackOutcome.BESTIAL_SUCCESS:
            Director.modify_influence("masquerade", +1)

        return {
            "attacker": attacker_name,
            "defender": defender_name,
            "weapon": weapon,
            "dice": dice,
            "net_successes": net,
            "damage": damage,
            "damage_report": dmg_report,
            "defeated": defender.is_defeated()
        }

    # ---------------------------------------------------------
    #  STATUS
    # ---------------------------------------------------------

    def status(self):
        lines = []
        for c in self.combatants.values():
            lines.append(
                f"{c.name} HP {c.hp_superficial}/{c.hp_aggravated}/{c.max_hp} – Hunger {c.hunger}"
            )
        return lines
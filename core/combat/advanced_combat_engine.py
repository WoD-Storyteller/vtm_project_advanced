from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from random import randint
from typing import Dict, List, Optional
import math

from core.combat.frenzy_system import FrenzySystem, FrenzyTrigger
from core.combat.range_and_firearms import get_range_dice_modifier, get_cover_success_penalty


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
    disciplines: Dict[str, int] = field(default_factory=dict)

    def is_defeated(self) -> bool:
        return (self.hp_superficial + self.hp_aggravated) >= self.max_hp


class CombatEngine:
    """
    Advanced V5-style combat engine:
    - Hunger dice
    - Messy / Bestial
    - Range & cover modifiers
    - Disciplines (Potence/Celerity/Fortitude)
    - Superficial vs Aggravated
    - Frenzy integration
    """

    def __init__(self):
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
        successes += crit_pairs * 2

        outcome = AttackOutcome.SUCCESS

        if crit_pairs > 0 and any(r == 10 for r in hunger_rolls):
            outcome = AttackOutcome.MESSY_CRITICAL
        if successes == 0 and any(r == 1 for r in hunger_rolls):
            outcome = AttackOutcome.BESTIAL_FAILURE
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
        r = randint(1, 10)
        return r >= 6

    # ---------- Damage ----------

    def apply_damage(
        self,
        target: Combatant,
        damage: int,
        damage_type: DamageType,
    ) -> Dict[str, int]:
        if damage <= 0:
            return {
                "applied_superficial": 0,
                "applied_aggravated": 0,
                "remaining_hp_superficial": target.hp_superficial,
                "remaining_hp_aggravated": target.hp_aggravated,
            }

        damage = max(0, damage - target.fortitude)

        applied_superficial = 0
        applied_aggravated = 0

        if target.is_vampire:
            if damage_type == DamageType.SUPERFICIAL:
                damage = math.ceil(damage / 2)
                applied_superficial = min(
                    damage,
                    target.max_hp - target.hp_superficial - target.hp_aggravated,
                )
                target.hp_superficial += applied_superficial
            else:
                applied_aggravated = min(
                    damage,
                    target.max_hp - target.hp_superficial - target.hp_aggravated,
                )
                target.hp_aggravated += applied_aggravated
        else:
            applied_aggravated = min(
                damage,
                target.max_hp - target.hp_superficial - target.hp_aggravated,
            )
            target.hp_aggravated += applied_aggravated

        if applied_aggravated > 0 and target.is_vampire:
            if FrenzySystem.check_trigger(FrenzyTrigger.AGGRAVATED_TAKEN, target):
                FrenzySystem.apply_frenzy(target, FrenzyTrigger.AGGRAVATED_TAKEN)

        return {
            "applied_superficial": applied_superficial,
            "applied_aggravated": applied_aggravated,
            "remaining_hp_superficial": target.hp_superficial,
            "remaining_hp_aggravated": target.hp_aggravated,
        }

    # ---------- Attack ----------

    def attack(
        self,
        attacker_name: str,
        defender_name: str,
        weapon: dict,
        difficulty: int = 2,
        range_band: str = "close",
        cover: str = "none",
    ) -> Dict:
        attacker = self.get_combatant(attacker_name)
        defender = self.get_combatant(defender_name)

        if not attacker or not defender:
            raise ValueError("Attacker or defender not found in combat.")

        attrs = attacker.attributes or {}
        skills = attacker.skills or {}
        discs = attacker.disciplines or {}

        w_type = weapon.get("type")
        traits = weapon.get("traits", [])

        # Attribute/skill base
        if w_type == "ranged":
            attr_val = attrs.get("dexterity", 2)
            skill_val = skills.get("firearms", 0)
        else:
            attr_val = attrs.get("strength", 2)
            skill_val = skills.get("melee", 0) or skills.get("brawl", 0)

        base_dice = weapon.get("base_dice", 0)
        pool = attr_val + skill_val + base_dice

        # Range modifiers
        pool += get_range_dice_modifier(weapon, range_band)

        # Disciplines:
        potence = int(discs.get("potence", 0))
        celerity = int(discs.get("celerity", 0))

        if w_type in ("melee", "supernatural") and potence > 0:
            pool += potence
        if w_type == "ranged" and celerity > 0:
            pool += celerity

        pool = max(1, pool)

        dice_result = self.roll_dice(pool, attacker.hunger)

        # Frenzy triggers from dice outcome
        if dice_result.outcome == AttackOutcome.BESTIAL_FAILURE:
            if FrenzySystem.check_trigger(FrenzyTrigger.BESTIAL_FAILURE, attacker):
                FrenzySystem.apply_frenzy(attacker, FrenzyTrigger.BESTIAL_FAILURE)
        elif dice_result.outcome == AttackOutcome.MESSY_CRITICAL:
            if FrenzySystem.check_trigger(FrenzyTrigger.MESSY_CRITICAL, attacker):
                FrenzySystem.apply_frenzy(attacker, FrenzyTrigger.MESSY_CRITICAL)

        net_successes = dice_result.successes - defender.defense

        # Cover applies as success penalty
        cover_penalty = get_cover_success_penalty(cover)
        net_successes -= cover_penalty

        success_margin = net_successes - difficulty + 1
        damage = max(0, success_margin)

        dmg_type = DamageType(weapon.get("damage_type", "superficial"))

        # Extra bite while frenzied
        if FrenzySystem.is_frenzied(attacker.name):
            damage += 1

        damage_report: Dict[str, int] = {}
        if damage > 0:
            damage_report = self.apply_damage(defender, damage, dmg_type)

        return {
            "attacker": attacker.name,
            "defender": defender.name,
            "weapon": weapon.get("name", "Unknown"),
            "dice": {
                "pool": dice_result.pool,
                "hunger": dice_result.hunger,
                "normal_rolls": dice_result.normal_rolls,
                "hunger_rolls": dice_result.hunger_rolls,
                "successes": dice_result.successes,
                "outcome": dice_result.outcome.value,
            },
            "net_successes": net_successes,
            "damage": damage,
            "damage_type": dmg_type.value,
            "damage_report": damage_report,
            "defender_defeated": defender.is_defeated(),
        }

    # ---------- Status ----------

    def status(self) -> List[str]:
        lines: List[str] = []
        for c in self.combatants.values():
            total = c.hp_superficial + c.hp_aggravated
            lines.append(
                f"{c.name}: {total}/{c.max_hp} "
                f"(S:{c.hp_superficial} A:{c.hp_aggravated}) "
                f"Hunger:{c.hunger} "
                f"WP(S/A):{c.willpower_superficial}/{c.willpower_aggravated}"
            )
        return lines
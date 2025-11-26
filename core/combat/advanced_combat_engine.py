from __future__ import annotations
from dataclasses import dataclass, field
from enum import Enum
from random import randint
from typing import Dict, List, Optional
import math


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
    hp_superficial: int = 10
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
        successes += crit_pairs * 2  # V5 crits: pair of 10s = +2 successes

        outcome = AttackOutcome.SUCCESS

        # Messy crit / Bestial
        if crit_pairs > 0 and any(r == 10 for r in hunger_rolls):
            outcome = AttackOutcome.MESSY_CRITICAL
        if successes == 0 and any(r == 1 for r in hunger_rolls):
            outcome = AttackOutcome.BESTIAL_FAILURE

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
        """Returns True on success, False if hunger increases."""
        r = randint(1, 10)
        return r >= 6

    # ---------- Damage Application ----------

    def apply_damage(
        self,
        target: Combatant,
        damage: int,
        damage_type: DamageType,
    ) -> Dict[str, int]:
        """Apply damage respecting V5 rules for vamps vs mortals + fortitude."""
        if damage <= 0:
            return {
                "applied_superficial": 0,
                "applied_aggravated": 0,
                "remaining_hp_superficial": target.hp_superficial,
                "remaining_hp_aggravated": target.hp_aggravated,
            }

        # Fortitude as flat reduction
        damage = max(0, damage - target.fortitude)

        applied_superficial = 0
        applied_aggravated = 0

        if target.is_vampire:
            if damage_type == DamageType.SUPERFICIAL:
                # Vampires halve superficial, round up
                damage = math.ceil(damage / 2)
                applied_superficial = min(damage, target.max_hp - target.hp_superficial - target.hp_aggravated)
                target.hp_superficial += applied_superficial
            else:
                # aggravated always full
                applied_aggravated = min(damage, target.max_hp - target.hp_superficial - target.hp_aggravated)
                target.hp_aggravated += applied_aggravated
        else:
            # Mortals: all damage is effectively lethal (we treat as aggravated)
            applied_aggravated = min(damage, target.max_hp - target.hp_superficial - target.hp_aggravated)
            target.hp_aggravated += applied_aggravated

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
    ) -> Dict:
        attacker = self.get_combatant(attacker_name)
        defender = self.get_combatant(defender_name)

        if not attacker or not defender:
            raise ValueError("Attacker or defender not in combat.")

        # Build dice pool
        attr_value = attacker.attributes.get("strength", 2)
        if weapon["type"] == "ranged":
            attr_value = attacker.attributes.get("dexterity", 2)

        if weapon["type"] == "melee" or weapon["type"] == "supernatural":
            skill_value = attacker.skills.get("melee", 0) or attacker.skills.get("brawl", 0)
        else:
            skill_value = attacker.skills.get("firearms", 0)

        base_dice = weapon.get("base_dice", 0)
        pool = attr_value + skill_value + base_dice

        # Roll
        dice_result = self.roll_dice(pool, attacker.hunger)

        # Net successes after defense & difficulty
        net_successes = dice_result.successes - defender.defense
        success_margin = net_successes - difficulty + 1  # so diff 2, 2 net = 1 margin

        damage = max(0, success_margin)
        dmg_type = DamageType(weapon.get("damage_type", "superficial"))

        damage_report = {}
        if damage > 0:
            damage_report = self.apply_damage(defender, damage, dmg_type)

        return {
            "attacker": attacker.name,
            "defender": defender.name,
            "weapon": weapon["name"],
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
        lines = []
        for c in self.combatants.values():
            total = c.hp_superficial + c.hp_aggravated
            lines.append(
                f"{c.name}: {total}/{c.max_hp} (S: {c.hp_superficial}, A: {c.hp_aggravated}), "
                f"Hunger: {c.hunger}, WP(S/A): {c.willpower_superficial}/{c.willpower_aggravated}"
            )
        return lines
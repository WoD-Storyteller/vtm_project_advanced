from dataclasses import dataclass, field
from typing import List, Dict, Optional
import random

@dataclass
class Weapon:
    name: str
    damage: int
    damage_type: str = "superficial"  # or "aggravated"
    traits: List[str] = field(default_factory=list)  # e.g. ["melee", "ranged", "concealable"]

@dataclass
class Combatant:
    name: str
    is_npc: bool = False
    initiative: int = 0
    health_max: int = 7
    health_superficial: int = 0
    health_aggravated: int = 0
    hunger: int = 1
    attributes: Dict[str, int] = field(default_factory=dict)
    skills: Dict[str, int] = field(default_factory=dict)
    disciplines: Dict[str, int] = field(default_factory=dict)
    weapons: List[Weapon] = field(default_factory=list)
    status: str = "alive"  # or "torpor", "destroyed"

    def dice_pool(self, attr: str, skill: str) -> int:
        a = self.attributes.get(attr.lower(), 0)
        s = self.skills.get(skill.lower(), 0)
        return max(1, a + s)

    def apply_damage(self, amount: int, damage_type: str = "superficial"):
        if amount <= 0 or self.status != "alive":
            return

        if damage_type == "superficial":
            # superficial stacks in pairs to become aggravated when full
            self.health_superficial += amount
            while self.health_superficial >= 2 and (self.health_aggravated + 1) <= self.health_max:
                self.health_superficial -= 2
                self.health_aggravated += 1
        else:
            self.health_aggravated += amount

        if self.health_aggravated >= self.health_max:
            self.status = "torpor" if not self.is_npc else "destroyed"

@dataclass
class CombatEncounter:
    combatants: List[Combatant] = field(default_factory=list)
    round: int = 0
    turn_index: int = 0
    log: List[str] = field(default_factory=list)

    def add_combatant(self, c: Combatant):
        self.combatants.append(c)

    def roll_initiative(self):
        for c in self.combatants:
            # Simple initiative: wits + awareness dice, but we only need ordering
            base = c.attributes.get("wits", 2) + c.skills.get("awareness", 0)
            c.initiative = base + random.randint(1, 10)
        self.combatants.sort(key=lambda x: x.initiative, reverse=True)
        self.round = 1
        self.turn_index = 0
        self.log.append(f"Round {self.round} begins. Initiative order: " +
                        ", ".join(f"{c.name}({c.initiative})" for c in self.combatants))

    def current_combatant(self) -> Optional[Combatant]:
        if not self.combatants:
            return None
        if self.turn_index >= len(self.combatants):
            return None
        return self.combatants[self.turn_index]

    def next_turn(self):
        if not self.combatants:
            return
        self.turn_index += 1
        if self.turn_index >= len(self.combatants):
            self.round += 1
            self.turn_index = 0
            self.log.append(f"Round {self.round} begins.")

    def attack(self, attacker: Combatant, defender: Combatant, weapon: Optional[Weapon] = None,
               attr: str = "dexterity", skill: str = "melee"):
        pool = attacker.dice_pool(attr, skill)
        hunger = attacker.hunger
        normal_dice = max(0, pool - hunger)
        hunger_dice = min(pool, hunger)

        results = []
        for _ in range(normal_dice):
            results.append(random.randint(1, 10))
        hunger_results = []
        for _ in range(hunger_dice):
            hunger_results.append(random.randint(1, 10))

        successes = sum(1 for r in results if r >= 6) + sum(1 for r in hunger_results if r >= 6)
        messy_crit = (any(r == 10 for r in hunger_results) and any(r == 10 for r in results))
        bestial_fail = (all(r < 6 for r in results) and any(r == 1 for r in hunger_results))

        log_line = f"{attacker.name} attacks {defender.name}: {successes} successes."
        if messy_crit:
            log_line += " Messy critical!"
        if bestial_fail:
            log_line += " Bestial failure!"

        if successes <= 0:
            self.log.append(log_line + " The attack misses.")
            return

        base_damage = 1 if weapon is None else weapon.damage
        total_damage = base_damage + max(0, successes - 1)
        dmg_type = "superficial" if weapon is None else weapon.damage_type
        defender.apply_damage(total_damage, dmg_type)
        log_line += f" Deals {total_damage} {dmg_type} damage."
        self.log.append(log_line)

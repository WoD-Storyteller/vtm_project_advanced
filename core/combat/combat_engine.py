from __future__ import annotations

from typing import Dict, Optional, List, Tuple
from random import randint

from core.combat.advanced_combat_engine import CombatEngine, Combatant


class CombatSession:
    def __init__(self, channel_id: int):
        self.channel_id = channel_id
        self.engine = CombatEngine()
        self.turn_order: List[str] = []
        self.current_index: int = 0
        # ammo[attacker_name][weapon_name] = remaining
        self.ammo: Dict[str, Dict[str, int]] = {}

    def add_combatant(self, combatant: Combatant, roll_initiative: bool = True):
        self.engine.add_combatant(combatant)
        if roll_initiative:
            dex = combatant.attributes.get("dexterity", 2)
            wits = combatant.attributes.get("wits", 2)
            initiative = randint(1, 10) + dex + wits
            combatant.attributes["initiative"] = initiative

    def build_initiative(self):
        self.turn_order = sorted(
            self.engine.combatants.keys(),
            key=lambda n: self.engine.combatants[n].attributes.get("initiative", 0),
            reverse=True,
        )
        self.current_index = 0

    def current_actor(self) -> Optional[str]:
        if not self.turn_order:
            return None
        return self.turn_order[self.current_index]

    def next_turn(self) -> Optional[str]:
        if not self.turn_order:
            return None
        self.current_index = (self.current_index + 1) % len(self.turn_order)
        return self.turn_order[self.current_index]

    # ---------- Ammo Management ----------

    def use_ammo(self, attacker_name: str, weapon: dict) -> Tuple[bool, int]:
        """
        Decrement ammo for ranged weapons. Returns (ok, remaining).
        If weapon is melee or has no magazine, always ok.
        """
        if weapon.get("type") != "ranged":
            return True, -1

        mag = int(weapon.get("magazine", 1))
        wname = weapon.get("name", "Unknown")

        user_ammo = self.ammo.setdefault(attacker_name, {})
        current = user_ammo.get(wname, mag)

        if current <= 0:
            return False, current

        current -= 1
        user_ammo[wname] = current
        return True, current

    def reload(self, attacker_name: str, weapon: dict) -> int:
        """
        Reload weapon to full magazine; returns new ammo count.
        """
        if weapon.get("type") != "ranged":
            return -1

        mag = int(weapon.get("magazine", 1))
        wname = weapon.get("name", "Unknown")
        user_ammo = self.ammo.setdefault(attacker_name, {})
        user_ammo[wname] = mag
        return mag


class CombatManager:
    def __init__(self):
        self.sessions: Dict[int, CombatSession] = {}

    def start_session(self, channel_id: int) -> CombatSession:
        session = CombatSession(channel_id)
        self.sessions[channel_id] = session
        return session

    def get_session(self, channel_id: int) -> Optional[CombatSession]:
        return self.sessions.get(channel_id)

    def end_session(self, channel_id: int):
        self.sessions.pop(channel_id, None)
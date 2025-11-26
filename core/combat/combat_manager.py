from typing import Dict, Optional, List
from core.combat.advanced_combat_engine import CombatEngine, Combatant
from random import randint


class CombatSession:
    def __init__(self, channel_id: int):
        self.channel_id = channel_id
        self.engine = CombatEngine()
        self.turn_order: List[str] = []
        self.current_index: int = 0

    def add_combatant(self, combatant: Combatant, roll_initiative: bool = True):
        self.engine.add_combatant(combatant)
        if roll_initiative:
            initiative = randint(1, 10) + combatant.attributes.get("dexterity", 2)
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


class CombatManager:
    def __init__(self):
        # channel_id -> CombatSession
        self.sessions: Dict[int, CombatSession] = {}

    def start_session(self, channel_id: int) -> CombatSession:
        session = CombatSession(channel_id)
        self.sessions[channel_id] = session
        return session

    def get_session(self, channel_id: int) -> Optional[CombatSession]:
        return self.sessions.get(channel_id)

    def end_session(self, channel_id: int):
        self.sessions.pop(channel_id, None)
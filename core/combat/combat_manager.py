from core.combat.combat_engine import CombatEngine, Combatant

class CombatManager:
    def __init__(self):
        self.sessions = {}

    def start(self, channel_id, pc_name, enemy_name):
        engine = CombatEngine()
        engine.add(Combatant(pc_name))
        engine.add(Combatant(enemy_name, npc=True))
        self.sessions[channel_id] = engine
        return engine

    def get(self, channel_id):
        return self.sessions.get(channel_id)

    def end(self, channel_id):
        self.sessions.pop(channel_id, None)
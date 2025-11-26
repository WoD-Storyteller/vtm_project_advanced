import random

class Dice:
    @staticmethod
    def roll(pool):
        rolls = [random.randint(1, 10) for _ in range(pool)]
        successes = sum(1 for r in rolls if r >= 6)
        tens = rolls.count(10)
        if tens >= 2:
            successes += (tens // 2) * 2
        return rolls, successes

class Combatant:
    def __init__(self, name, hp=10, defense=1, skills=None, attributes=None, npc=False):
        self.name = name
        self.hp = hp
        self.defense = defense
        self.npc = npc
        self.attributes = attributes or {}
        self.skills = skills or {}

    def dice_for_weapon(self, weapon):
        attr = self.attributes.get("strength", 1)
        skill = 0

        if weapon["type"] == "melee":
            skill = self.skills.get("melee", 0)
        elif weapon["type"] == "ranged":
            skill = self.skills.get("firearms", 0)

        return attr + skill + weapon["dice"]

class CombatEngine:
    def __init__(self):
        self.combatants = {}
        self.log = []

    def add(self, combatant):
        self.combatants[combatant.name] = combatant

    def attack(self, attacker_name, defender_name, weapon):
        att = self.combatants[attacker_name]
        defn = self.combatants[defender_name]

        pool = att.dice_for_weapon(weapon)
        rolls, successes = Dice.roll(pool)

        hits = max(0, successes - defn.defense)
        damage = hits if weapon["damage"] == "superficial" else hits * 2

        defn.hp -= damage

        entry = (
            f"**{attacker_name}** attacks **{defender_name}** with **{weapon['name']}**\n"
            f"Rolls: {rolls} → **{successes}** successes\n"
            f"Defense: {defn.defense}\n"
            f"Damage: **{damage}** ({weapon['damage']})\n"
            f"{defender_name} HP left: **{defn.hp}**"
        )

        self.log.append(entry)
        return entry

    def status(self):
        return "\n".join([f"{c.name}: {c.hp} HP" for c in self.combatants.values()])
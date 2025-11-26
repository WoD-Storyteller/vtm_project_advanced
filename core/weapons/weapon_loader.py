import json
import os

WEAPON_PATH = os.path.join(os.path.dirname(__file__), "weapons.json")

def load_weapons():
    with open(WEAPON_PATH, "r") as f:
        data = json.load(f)
    return {item["name"].lower(): item for item in data["weapons"]}
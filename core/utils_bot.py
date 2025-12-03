import json
import os

BOT_DATA_PATH = os.getenv("BOT_DATA_PATH", "bot_data.json")

def load_bot_data(path: str = BOT_DATA_PATH):
    if not os.path.exists(path):
        return {"guilds": {}, "characters": {}, "items": {}}
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)

def save_bot_data(path: str, data: dict):
    tmp = path + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4)
    os.replace(tmp, path)

def ensure_player(store: dict, guild_id: str, user_id: str):
    store.setdefault("guilds", {})
    store["guilds"].setdefault(guild_id, {"players": {}})
    g = store["guilds"][guild_id]
    if user_id not in g["players"]:
        g["players"][user_id] = {"character": {}, "state": {}}
    return g["players"][user_id]

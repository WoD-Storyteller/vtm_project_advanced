import json
import os

DATA_FILE = os.getenv("DATA_PATH", "vtm_data.json")

def load_data_from_file(path: str = DATA_FILE):
    """Load API-side persistent data store."""
    if not os.path.exists(path):
        return {"guilds": {}, "players": {}, "director_state": {}}
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)

def save_data(path: str, data: dict):
    """Atomic save for API store."""
    tmp = path + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4)
    os.replace(tmp, path)

def get_guild_data(store: dict, guild_id: str):
    store.setdefault("guilds", {})
    store["guilds"].setdefault(guild_id, {"players": {}, "director_state": {}})
    return store["guilds"][guild_id]

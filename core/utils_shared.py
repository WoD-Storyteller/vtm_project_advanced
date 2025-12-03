import json import os def load_data_from_file(path: 
str) -> dict:
    if not os.path.exists(path): return {} with 
    open(path, "r", encoding="utf-8") as f:
        return json.load(f) def save_data(path: str, 
data: dict):
    os.makedirs(os.path.dirname(path), 
    exist_ok=True) with open(path, "w", 
    encoding="utf-8") as f:
        json.dump(data, f, indent=4) def 
get_guild_data(store: dict, guild_id: str):
    guilds = store.setdefault("guilds", {})
    return guilds.setdefault(str(guild_id), {"players": {}, "state": {}})

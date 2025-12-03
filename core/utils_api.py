import json import os
# --------------------------------- 
# API-SIDE DATA MANAGEMENT 
# ---------------------------------
def load_json(path: str, default=None): if 
    not os.path.exists(path):
        return default if default is not 
        None else {}
    with open(path, "r", encoding="utf-8") 
    as f:
        return json.load(f) def 
save_json(path: str, data: dict):
    os.makedirs(os.path.dirname(path), 
    exist_ok=True) with open(path, "w", 
    encoding="utf-8") as f:
        json.dump(data, f, indent=4)
# --------------------------------- 
# API-SAFE GUILD ACCESS 
# ---------------------------------
def get_guild_data_api(data_store: dict, 
guild_id: int | str):
    """ API-safe version: - No Discord 
    structures - No imports from bot 
    components """ gid = str(guild_id) if 
    "guilds" not in data_store:
        data_store["guilds"] = {} if gid 
    not in data_store["guilds"]:
        data_store["guilds"][gid] = 
        {"players": {}, "state": {}}
    return data_store["guilds"][gid]

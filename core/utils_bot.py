import json import os from pathlib import 
Path
# --------------------------------- 
# BOT-SIDE DATA MANAGEMENT 
# ---------------------------------
def load_data_from_file(path: str): 
    """Loads the main VTM data-store used 
    by the Discord bot.""" if not 
    os.path.exists(path):
        return {"guilds": {}} with 
    open(path, "r", encoding="utf-8") as 
    f:
        return json.load(f) def 
save_data(path: str, data: dict):
    """Writes the bot data-store.""" 
    os.makedirs(os.path.dirname(path), 
    exist_ok=True) with open(path, "w", 
    encoding="utf-8") as f:
        json.dump(data, f, indent=4)
# --------------------------------- 
# BOT-SPECIFIC HELPERS 
# ---------------------------------
def get_guild_data(data_store: dict, 
guild_id: int | str):
    """Return or create guild block for 
    the Discord bot.""" gid = 
    str(guild_id) if "guilds" not in 
    data_store:
        data_store["guilds"] = {} if gid 
    not in data_store["guilds"]:
        data_store["guilds"][gid] = 
        {"players": {}, "state": {}}
    return data_store["guilds"][gid]

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from utils import load_data_from_file, get_guild_data, save_data

app = FastAPI(title="VtM Sandbox API (Minimal)")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.state.bot = None  # can be set from main.py if desired

_data_store = load_data_from_file()

def _get_guild(gid: str):
    return get_guild_data(_data_store, gid)

def _save():
    save_data(_data_store)

@app.get("/health")
def health():
    return {"ok": True, "message": "VtM Sandbox API running"}

@app.get("/guild/{guild_id}/info")
def guild_info(guild_id: str):
    g = _get_guild(guild_id)
    return {
        "ok": True,
        "guild_id": guild_id,
        "players": len(g.get("players", {})),
        "characters": len(g.get("characters", {})),
        "quests": len(g.get("quests", [])),
        "factions": len(g.get("factions", [])),
        "scenes": len(g.get("scenes", [])) if isinstance(g.get("scenes", []), list) else 0,
    }

@app.get("/guild/{guild_id}/players")
def guild_players(guild_id: str):
    g = _get_guild(guild_id)
    players = []
    for uid, pdata in g.get("players", {}).items():
        players.append({
            "user_id": uid,
            "name": pdata.get("name"),
            "clan": pdata.get("sheet_data", {}).get("clan"),
            "stats": pdata.get("stats", {}),
            "sheet_url": pdata.get("sheet_url"),
        })
    return {"ok": True, "players": players}

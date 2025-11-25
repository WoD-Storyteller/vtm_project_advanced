#"""
#FastAPI backend for VtM Storyteller / Player dashboards.

#This file is designed to be a self-contained, modern replacement for the old
#`api_server.py`, while still using the existing data layer in `utils.py`.

#It provides:

#- Discord OAuth login (/auth/login, /auth/callback)
#- Session token endpoint (/auth/session) used by the dashboards
#- Player character CRUD + XP + portrait upload
#- Storyteller tools:
#   - Director state (with optional "Emissary of Caine" awakening)
#    - Scene generation stub (connect to AI Director later if desired)
#    - Guild-wide character overview
#    - Player → ST requests list + resolve
#    - Dice roller + dice history log
#- Static mounts for:
#    - /dashboard   → HTML / JS / CSS dashboards
#    - /portraits   → uploaded character portraits

#You can run this with e.g.:

 #   uvicorn api_server:app --host 0.0.0.0 --port 8000

#Make sure you have environment variables set:

#    DISCORD_CLIENT_ID
#    DISCORD_CLIENT_SECRET
#    DISCORD_REDIRECT_URI     (e.g. "https://yourdomain.com/auth/callback")
#    JWT_SECRET               (any long random string)



import os
import time
import json
import random
from pathlib import Path
from typing import Dict, Any, Optional

import httpx
from fastapi import FastAPI, Request, Body, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import RedirectResponse
from fastapi.staticfiles import StaticFiles
from jose import jwt

from utils import load_data_from_file, save_data, get_guild_data

# ---------------------------------------------------------------------------
# Configuration / constants
# ---------------------------------------------------------------------------

DISCORD_CLIENT_ID = os.getenv("DISCORD_CLIENT_ID")
DISCORD_CLIENT_SECRET = os.getenv("DISCORD_CLIENT_SECRET")
DISCORD_REDIRECT_URI = os.getenv("DISCORD_REDIRECT_URI")  # must match your Discord app
DISCORD_API_BASE = "https://discord.com/api"
OAUTH_SCOPE = "identify"

JWT_SECRET = os.getenv("JWT_SECRET", "supersecretkey_change_me")
JWT_ALGO = "HS256"

BASE_DIR = Path(__file__).resolve().parent
DASHBOARD_DIR = BASE_DIR / "dashboard"
PORTRAIT_DIR = BASE_DIR / "portraits"
PORTRAIT_DIR.mkdir(exist_ok=True)

# ---------------------------------------------------------------------------
# Data store using existing utils layer
# ---------------------------------------------------------------------------

_data_store: Dict[str, Any] = load_data_from_file()
if not isinstance(_data_store, dict):
    _data_store = {}


def _save():
    """Persist the in-memory data store using existing utils.save_data."""
    save_data(_data_store)


def _get_guild(guild_id: str) -> Dict[str, Any]:
    """Get or create guild data using existing utils.get_guild_data."""
    return get_guild_data(_data_store, guild_id)


def _find_player_entry(user_id: str):
    """Search for the first guild that contains this player."""
    for gid, gdata in _data_store.items():
        if not isinstance(gdata, dict):
            continue
        players = gdata.get("players", {})
        if user_id in players:
            return gid, gdata, players[user_id]
    return None, None, None


# ---------------------------------------------------------------------------
# FastAPI app
# ---------------------------------------------------------------------------

app = FastAPI(title="VtM Storyteller API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # you can restrict this to your domain
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Static mounts for dashboards and portraits
if DASHBOARD_DIR.exists():
    app.mount("/dashboard", StaticFiles(directory=DASHBOARD_DIR), name="dashboard")

app.mount("/portraits", StaticFiles(directory=PORTRAIT_DIR), name="portraits")

# For compatibility if you want to attach the Discord bot later
app.state.bot = None


# ---------------------------------------------------------------------------
# Session token helpers
# ---------------------------------------------------------------------------

def create_session_token(user_id: str, username: str, avatar_url: str, mode: str) -> str:
    """Create a short JWT used by the dashboard for 'remember me'."""
    return jwt.encode(
        {
            "sub": user_id,
            "username": username,
            "avatar": avatar_url,
            "mode": mode,
            "exp": time.time() + 60 * 60 * 24 * 30,  # 30 days
        },
        JWT_SECRET,
        algorithm=JWT_ALGO,
    )


# ---------------------------------------------------------------------------
# OAuth endpoints
# ---------------------------------------------------------------------------

@app.get("/auth/login")
def login(mode: str = "player"):
    """
    Begin Discord OAuth.
    mode = "player" or "st" (storyteller); stored in the redirect state.
    """
    if mode not in ("player", "st"):
        mode = "player"

    if not (DISCORD_CLIENT_ID and DISCORD_REDIRECT_URI):
        return {"ok": False, "error": "Discord OAuth not configured (check env vars)."}

    url = (
        f"{DISCORD_API_BASE}/oauth2/authorize"
        f"?client_id={DISCORD_CLIENT_ID}"
        f"&redirect_uri={DISCORD_REDIRECT_URI}"
        f"&response_type=code"
        f"&scope={OAUTH_SCOPE}"
        f"&state={mode}"
    )
    return RedirectResponse(url)


@app.get("/auth/callback")
async def callback(request: Request):
    """
    Discord OAuth callback.
    Exchanges code for access token, fetches user, sets a JWT cookie + redirects
    to the appropriate dashboard (player or storyteller).
    """
    code = request.query_params.get("code")
    mode = request.query_params.get("state", "player")
    if mode not in ("player", "st"):
        mode = "player"

    if not code:
        return {"ok": False, "error": "Missing code"}

    async with httpx.AsyncClient() as client:
        token_resp = await client.post(
            f"{DISCORD_API_BASE}/oauth2/token",
            data={
                "client_id": DISCORD_CLIENT_ID,
                "client_secret": DISCORD_CLIENT_SECRET,
                "grant_type": "authorization_code",
                "code": code,
                "redirect_uri": DISCORD_REDIRECT_URI,
                "scope": OAUTH_SCOPE,
            },
            headers={"Content-Type": "application/x-www-form-urlencoded"},
        )
        token_data = token_resp.json()
        access_token = token_data.get("access_token")

        if not access_token:
            return {"ok": False, "error": "Failed to get access token", "details": token_data}

        user_resp = await client.get(
            f"{DISCORD_API_BASE}/users/@me",
            headers={"Authorization": f"Bearer {access_token}"},
        )
        user_data = user_resp.json()

    discord_id = str(user_data.get("id"))
    if not discord_id:
        return {"ok": False, "error": "Unable to read Discord user id"}

    username = user_data.get("global_name") or user_data.get("username") or "Unknown"
    disc = user_data.get("discriminator")
    if disc and disc != "0":
        display_name = f"{username}#{disc}"
    else:
        display_name = username

    avatar_hash = user_data.get("avatar")
    if avatar_hash:
        avatar_url = f"https://cdn.discordapp.com/avatars/{discord_id}/{avatar_hash}.png?size=256"
    else:
        avatar_url = f"https://cdn.discordapp.com/embed/avatars/{int(discord_id) % 5}.png"

    token = create_session_token(discord_id, display_name, avatar_url, mode)

    dest = "index.html" if mode == "st" else "player.html"
    res = RedirectResponse(f"/dashboard/{dest}")
    res.set_cookie("vtm_session", token, httponly=True, max_age=60 * 60 * 24 * 30)
    return res


@app.get("/auth/session")
def get_session(request: Request):
    """
    Return session info from the JWT cookie.
    Used by both dashboards to auto-fill user_id, username, mode, avatar.
    """
    token = request.cookies.get("vtm_session")
    if not token:
        return {"ok": False, "error": "No token"}

    try:
        data = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGO])
        return {"ok": True, "session": data}
    except Exception:
        return {"ok": False, "error": "Invalid or expired token"}


# ---------------------------------------------------------------------------
# Player character API (used by player.js)
# ---------------------------------------------------------------------------

@app.get("/player/{user_id}/characters")
def list_characters(user_id: str):
    """
    List all characters belonging to this Discord user across all guilds.
    Returns a simple list and the 'active' character id (if any).
    """
    gid, gdata, player = _find_player_entry(user_id)
    if not player:
        return {"ok": True, "characters": [], "active": None}

    chars = player.get("characters", {})
    return {
        "ok": True,
        "characters": [
            {"id": cid, "name": c.get("name"), "clan": c.get("clan")}
            for cid, c in chars.items()
        ],
        "active": player.get("active_character_id"),
    }


@app.get("/player/{user_id}/characters/{char_id}")
def get_character(user_id: str, char_id: str):
    """Fetch a single character sheet."""
    gid, gdata, player = _find_player_entry(user_id)
    if not player:
        return {"ok": False, "error": "Player not found"}

    char = player.get("characters", {}).get(char_id)
    if not char:
        return {"ok": False, "error": "Character not found"}

    return {"ok": True, "character": char}


from uuid import uuid4


@app.post("/player/{user_id}/characters")
def create_character(user_id: str, payload: dict = Body(...)):
    """
    Create a new character for this user.
    The first guild in the datastore will be used, or 'default' if none exist.
    """
    # choose a guild to attach the player to
    gid, gdata, player = _find_player_entry(user_id)
    if not gdata:
        # if no existing guild, attach to "default"
        gid = "default"
        gdata = _get_guild(gid)

    players = gdata.setdefault("players", {})
    player = players.setdefault(user_id, {"discord_id": user_id, "characters": {}, "active_character_id": None})

    chars = player.setdefault("characters", {})
    char_id = payload.get("id") or f"char_{uuid4().hex[:8]}"
    payload["id"] = char_id
    chars[char_id] = payload

    if not player.get("active_character_id"):
        player["active_character_id"] = char_id

    _save()
    return {"ok": True, "character": payload}


@app.post("/player/{user_id}/characters/{char_id}")
def update_character(user_id: str, char_id: str, payload: dict = Body(...)):
    """Update a character sheet."""
    gid, gdata, player = _find_player_entry(user_id)
    if not player:
        return {"ok": False, "error": "Player not found"}

    chars = player.setdefault("characters", {})
    if char_id not in chars:
        return {"ok": False, "error": "Character not found"}

    payload["id"] = char_id
    chars[char_id] = payload
    _save()
    return {"ok": True, "character": payload}


@app.post("/player/{user_id}/characters/{char_id}/xp")
def adjust_xp(user_id: str, char_id: str, payload: dict = Body(...)):
    """
    Adjust XP for a character.

    Request body:
    {
      "amount": int,    # positive or negative
      "reason": "string",
      "session": "string"
    }
    """
    amount = int(payload.get("amount", 0))
    reason = str(payload.get("reason", ""))
    session = payload.get("session", "")

    gid, gdata, player = _find_player_entry(user_id)
    if not player:
        return {"ok": False, "error": "Player not found"}
    char = player.get("characters", {}).get(char_id)
    if not char:
        return {"ok": False, "error": "Character not found"}

    xp = char.setdefault("xp", {"total": 0, "spent": 0, "unspent": 0, "log": []})
    if amount > 0:
        xp["total"] = xp.get("total", 0) + amount
    xp["unspent"] = xp.get("unspent", 0) + amount
    xp.setdefault("log", []).append(
        {"amount": amount, "reason": reason, "session": session, "time": int(time.time())}
    )
    _save()
    return {"ok": True, "xp": xp}


@app.post("/player/{user_id}/request")
def player_request(user_id: str, payload: dict = Body(...)):
    """Player → Storyteller request."""
    subject = payload.get("subject", "")
    detail = payload.get("detail", "")
    if not subject or not detail:
        return {"ok": False, "error": "Missing subject or detail"}

    reqs = _data_store.setdefault("requests", [])
    reqs.append(
        {
            "user_id": user_id,
            "subject": subject,
            "detail": detail,
            "timestamp": int(time.time()),
            "status": "pending",
        }
    )
    _save()
    return {"ok": True}


# Portrait upload
@app.post("/player/{user_id}/characters/{char_id}/portrait")
async def upload_portrait(user_id: str, char_id: str, file: UploadFile = File(...)):
    """Upload and attach a portrait to a character."""
    gid, gdata, player = _find_player_entry(user_id)
    if not player:
        return {"ok": False, "error": "Player not found"}
    char = player.get("characters", {}).get(char_id)
    if not char:
        return {"ok": False, "error": "Character not found"}

    ext = Path(file.filename).suffix or ".png"
    fname = f"{char_id}{ext}"
    full_path = PORTRAIT_DIR / fname
    content = await file.read()
    full_path.write_bytes(content)

    char["portrait_url"] = f"/portraits/{fname}"
    _save()
    return {"ok": True, "portrait_url": char["portrait_url"]}


# ---------------------------------------------------------------------------
# Storyteller / Director API (used by app.js)
# ---------------------------------------------------------------------------

@app.get("/guild/{guild_id}/director")
def get_director(guild_id: str):
    """
    Get (or initialize) the AI Director state for a guild.
    This can later be wired into director_system.* if desired.
    """
    g = _get_guild(guild_id)
    director = g.setdefault(
        "director",
        {
            "awakened": False,
            "avatar": {"name": "Sleeping Director"},
            "notes": "",
        },
    )
    return {"ok": True, "director": director}


@app.post("/guild/{guild_id}/director/awaken")
def director_awaken(guild_id: str):
    """Set director to awakened Emissary of Caine mode."""
    g = _get_guild(guild_id)
    director = g.setdefault("director", {})
    director["awakened"] = True
    avatar = director.setdefault("avatar", {})
    avatar.setdefault("name", "Emissary of Caine")
    _save()
    return {"ok": True, "director": director}


@app.post("/guild/{guild_id}/director/sleep")
def director_sleep(guild_id: str):
    """Put the Emissary to sleep (director inactive)."""
    g = _get_guild(guild_id)
    director = g.setdefault("director", {})
    director["awakened"] = False
    _save()
    return {"ok": True, "director": director}


@app.post("/guild/{guild_id}/director/upload")
async def director_upload(guild_id: str, file: UploadFile = File(...)):
    """
    Upload a custom Director config JSON from the ST dashboard.
    File should contain a JSON object describing director state/preferences.
    """
    g = _get_guild(guild_id)
    raw = await file.read()
    try:
        director_json = json.loads(raw.decode("utf-8"))
    except Exception as e:
        return {"ok": False, "error": f"Invalid JSON: {e}"}

    g["director"] = director_json
    _save()
    return {"ok": True, "director": director_json}


@app.post("/guild/{guild_id}/scene/generate")
async def scene_generate(guild_id: str, payload: dict = Body(...)):
    """
    Scene generation stub.

    Request body:
    {
      "location_key": "string",
      "travelers": ["char_id1", "char_id2"],
      "risk": int (1-5)
    }

    At any time you can replace this stub with a real call to your AI Director
    (e.g. director_system.engine.apply_encounter_to_director / AIDirector).
    """
    location_key = payload.get("location_key") or "unknown_location"
    travelers = payload.get("travelers", [])
    risk = int(payload.get("risk", 2))

    risk_label = "Low"
    if risk >= 4:
        risk_label = "High"
    elif risk == 3:
        risk_label = "Moderate"

    intro_text = (
        f"The coterie arrives at {location_key}. The air feels {risk_label.lower()}-dangerous. "
        f"Attending: {', '.join(travelers) if travelers else 'unknown travelers'}."
    )

    scene = {
        "intro_text": intro_text,
        "npcs": [],
        "encounter": None,
        "quest_hook": "",
        "severity": risk,
        "severity_label": risk_label,
        "director_update": None,
    }
    return {"ok": True, "scene": scene}


@app.get("/guild/{guild_id}/characters")
def all_characters(guild_id: str):
    """Guild-wide character overview used by the ST dashboard."""
    g = _get_guild(guild_id)
    results = []
    for pid, player in g.get("players", {}).items():
        for cid, char in player.get("characters", {}).items():
            results.append(
                {
                    "player_id": pid,
                    "character_id": cid,
                    "name": char.get("name"),
                    "clan": char.get("clan"),
                    "hunger": char.get("hunger", 0),
                    "health": char.get("health", {}),
                    "willpower": char.get("willpower", {}),
                    "xp": char.get("xp", {}),
                }
            )
    return {"ok": True, "characters": results}


# ---------------------------------------------------------------------------
# Requests + Dice (ST dashboard)
# ---------------------------------------------------------------------------

@app.get("/requests")
def list_requests():
    """List all player requests (global list)."""
    return {"ok": True, "requests": _data_store.get("requests", [])}


@app.post("/requests/{index}/resolve")
def resolve_request(index: int):
    """Mark a request as resolved."""
    reqs = _data_store.get("requests", [])
    if 0 <= index < len(reqs):
        reqs[index]["status"] = "resolved"
        _save()
        return {"ok": True}
    return {"ok": False, "error": "Invalid index"}


@app.post("/roll")
def roll_dice(payload: dict = Body(...)):
    """
    V5-style dice pool roller with hunger dice.

    Request body:
    {
      "pool": int,
      "hunger": int,
      "user_id": "optional"
    }
    """
    pool = int(payload.get("pool", 0))
    hunger = int(payload.get("hunger", 0))
    user_id = payload.get("user_id")

    if pool < 1:
        return {"ok": False, "error": "Pool must be at least 1"}

    hunger = max(0, min(hunger, pool))
    normal = pool - hunger

    normal_results = [random.randint(1, 10) for _ in range(normal)]
    hunger_results = [random.randint(1, 10) for _ in range(hunger)]

    successes = sum(1 for r in normal_results + hunger_results if r >= 6)
    messy_crit = bool(
        any(r == 10 for r in hunger_results) and any(r == 10 for r in normal_results)
    )
    bestial_fail = bool(successes == 0 and any(r == 1 for r in hunger_results))

    result = {
        "ok": True,
        "pool": pool,
        "hunger": hunger,
        "normal_results": normal_results,
        "hunger_results": hunger_results,
        "successes": successes,
        "messy_crit": messy_crit,
        "bestial_failure": bestial_fail,
    }

    history = _data_store.setdefault("dice_history", [])
    history.append(
        {
            "user_id": user_id,
            "timestamp": int(time.time()),
            "pool": pool,
            "hunger": hunger,
            "result": result,
        }
    )
    _save()

    return result


@app.get("/dice/history")
def dice_history():
    """Return the global dice roll history."""
    return {"ok": True, "history": _data_store.get("dice_history", [])}


# ---------------------------------------------------------------------------
# Simple health-check
# ---------------------------------------------------------------------------

@app.get("/health")
def health():
    return {"ok": True, "message": "VtM Storyteller API is running."}


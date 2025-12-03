# api/auth/routes.py

import os
import secrets
import string
from urllib.parse import urlencode

import requests
from fastapi import APIRouter, HTTPException, Request, status
from fastapi.responses import RedirectResponse
from pydantic import BaseModel

router = APIRouter()

# -------------------------------------------
# Local admin login
# -------------------------------------------

class LoginRequest(BaseModel):
    username: str
    password: str

class LoginResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"

@router.post("/auth/login", response_model=LoginResponse)
async def admin_login(req: LoginRequest):
    if req.username != "admin" or req.password != "admin":
        raise HTTPException(401, "Invalid credentials")
    return LoginResponse(access_token="admin.local.token")


# -------------------------------------------
# Discord OAuth2 login
# -------------------------------------------

DISCORD_CLIENT_ID = os.getenv("DISCORD_CLIENT_ID")
DISCORD_CLIENT_SECRET = os.getenv("DISCORD_CLIENT_SECRET")
DISCORD_REDIRECT_URI = os.getenv(
    "DISCORD_REDIRECT_URI",
    "https://bloodscriptengine.tech/oauth/callback"
)

def require_oauth():
    if not DISCORD_CLIENT_ID or not DISCORD_CLIENT_SECRET:
        raise HTTPException(500, "Discord OAuth not configured")

def make_state(request: Request):
    state = "".join(secrets.choice(string.ascii_letters) for _ in range(32))
    request.session["oauth_state"] = state
    return state

@router.get("/login")
async def login_entry(request: Request):
    return await discord_login(request)

@router.get("/oauth/discord")
async def discord_login(request: Request):
    require_oauth()
    state = make_state(request)
    params = {
        "client_id": DISCORD_CLIENT_ID,
        "redirect_uri": DISCORD_REDIRECT_URI,
        "response_type": "code",
        "scope": "identify",
        "state": state,
    }
    url = "https://discord.com/oauth2/authorize?" + urlencode(params)
    return RedirectResponse(url)

@router.get("/oauth/callback")
async def discord_callback(request: Request, code: str, state: str):

    saved = request.session.get("oauth_state")
    if not saved or saved != state:
        raise HTTPException(400, "Invalid OAuth state")

    token_data = {
        "client_id": DISCORD_CLIENT_ID,
        "client_secret": DISCORD_CLIENT_SECRET,
        "grant_type": "authorization_code",
        "code": code,
        "redirect_uri": DISCORD_REDIRECT_URI
    }

    r = requests.post("https://discord.com/api/oauth2/token", data=token_data)
    tokens = r.json()
    access = tokens.get("access_token")

    if not access:
        raise HTTPException(400, "Discord token exchange failed")

    u = requests.get(
        "https://discord.com/api/users/@me",
        headers={"Authorization": f"Bearer {access}"}
    )
    user = u.json()

    request.session["user"] = {
        "sub": user["id"],
        "username": user["username"],
        "avatar": f"https://cdn.discordapp.com/avatars/{user['id']}/{user.get('avatar')}.png",
        "mode": "player",
    }

    return RedirectResponse("/dashboard/player.html")


# -------------------------------------------
# Session check for dashboard JS
# -------------------------------------------

@router.get("/auth/session")
async def get_session(request: Request):
    u = request.session.get("user")
    if not u:
        return {"ok": False}
    return {"ok": True, "session": u}

@router.post("/auth/logout")
async def logout(request: Request):
    request.session.clear()
    return {"ok": True}

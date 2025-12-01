import os
import secrets
import string
from urllib.parse import urlencode

import requests
from fastapi import APIRouter, HTTPException, Request, status
from fastapi.responses import RedirectResponse
from pydantic import BaseModel

router = APIRouter()

# ------------------------------------------------------------
# Simple admin API login (optional, kept for tools / future use)
# ------------------------------------------------------------

class LoginRequest(BaseModel):
    username: str
    password: str


class LoginResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


@router.post("/auth/login", response_model=LoginResponse)
async def login(payload: LoginRequest):
    """
    Very basic username/password login (admin/admin by default).

    Mainly here so you still have a non-Discord way to talk to the API.
    """
    if payload.username != "admin" or payload.password != "admin":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials",
        )

    fake_token = "example.jwt.token"
    return LoginResponse(access_token=fake_token)


# ------------------------------------------------------------
# Discord OAuth2 login for the dashboard
# ------------------------------------------------------------

DISCORD_CLIENT_ID = os.getenv("DISCORD_CLIENT_ID")
DISCORD_CLIENT_SECRET = os.getenv("DISCORD_CLIENT_SECRET")
DISCORD_REDIRECT_URI = os.getenv(
    "DISCORD_REDIRECT_URI",
    "https://bloodscriptengine.tech/oauth/callback",
)
DISCORD_SCOPE = os.getenv("DISCORD_OAUTH_SCOPE", "identify")


def _require_discord_config():
    if not DISCORD_CLIENT_ID or not DISCORD_CLIENT_SECRET:
        raise HTTPException(
            status_code=500,
            detail=(
                "Discord OAuth not configured on server "
                "(missing DISCORD_CLIENT_ID / DISCORD_CLIENT_SECRET)."
            ),
        )


def _make_state(request: Request) -> str:
    state = "".join(secrets.choice(string.ascii_letters + string.digits) for _ in range(32))
    request.session["oauth_state"] = state
    return state


@router.get("/login")
async def login_entry(request: Request):
    """
    Entry point used by /login on the domain.

    Immediately hands off to the Discord OAuth flow.
    """
    return await discord_login(request)


@router.get("/oauth/discord")
async def discord_login(request: Request):
    """Start the Discord OAuth2 flow and redirect the user to Discord."""
    _require_discord_config()

    state = _make_state(request)
    params = {
        "client_id": DISCORD_CLIENT_ID,
        "redirect_uri": DISCORD_REDIRECT_URI,
        "response_type": "code",
        "scope": DISCORD_SCOPE,
        "state": state,
        "prompt": "consent",
    }
    url = "https://discord.com/oauth2/authorize?" + urlencode(params)
    return RedirectResponse(url)


@router.get("/oauth/callback")
async def discord_callback(
    request: Request,
    code: str | None = None,
    state: str | None = None,
):
    """
    Handle Discord's callback, store the user in the session, and redirect to the dashboard.
    """
    _require_discord_config()

    if not code:
        raise HTTPException(status_code=400, detail="Missing ?code from Discord")

    saved_state = request.session.get("oauth_state")
    if not saved_state or state != saved_state:
        raise HTTPException(status_code=400, detail="Invalid OAuth state")

    # Exchange the code for tokens
    token_data = {
        "client_id": DISCORD_CLIENT_ID,
        "client_secret": DISCORD_CLIENT_SECRET,
        "grant_type": "authorization_code",
        "code": code,
        "redirect_uri": DISCORD_REDIRECT_URI,
    }
    headers = {"Content-Type": "application/x-www-form-urlencoded"}

    token_resp = requests.post(
        "https://discord.com/api/oauth2/token",
        data=token_data,
        headers=headers,
    )
    if token_resp.status_code != 200:
        raise HTTPException(status_code=400, detail="Failed to exchange code with Discord")

    tokens = token_resp.json()
    access_token = tokens.get("access_token")
    if not access_token:
        raise HTTPException(status_code=400, detail="No access_token returned by Discord")

    # Fetch user profile
    user_resp = requests.get(
        "https://discord.com/api/users/@me",
        headers={"Authorization": f"Bearer {access_token}"},
    )
    if user_resp.status_code != 200:
        raise HTTPException(status_code=400, detail="Failed to fetch user profile from Discord")

    user = user_resp.json()

    avatar_hash = user.get("avatar")
    if avatar_hash:
        avatar_url = f"https://cdn.discordapp.com/avatars/{user['id']}/{avatar_hash}.png"
    else:
        avatar_url = ""

    # Store a compact session object for the dashboard JS
    request.session["user"] = {
        "sub": user["id"],
        "username": user.get("username"),
        "avatar": avatar_url,
        "mode": "player",
    }
    request.session.pop("oauth_state", None)

    # Send them to the dashboard – player sheet by default
    return RedirectResponse(url="/dashboard/player.html")


# ------------------------------------------------------------
# Session introspection for the dashboard JS
# ------------------------------------------------------------

@router.get("/auth/session")
async def get_session(request: Request):
    """
    Return the current logged-in Discord user for the dashboard.

    This is what /dashboard/js/app.js and /dashboard/js/player.js call.
    """
    user = request.session.get("user")
    if not user:
        return {"ok": False}
    return {"ok": True, "session": user}


@router.post("/auth/logout")
async def logout(request: Request):
    request.session.clear()
    return {"ok": True}
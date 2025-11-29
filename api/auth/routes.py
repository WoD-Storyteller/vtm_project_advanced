"""
Discord OAuth + session endpoints for the dashboard & player sheet.

Front-end expectations (from dashboard/js/*.js):
  - GET /auth/session  -> { ok: bool, session?: { sub, username, mode, avatar } }
  - GET /auth/login?mode=st|player  -> redirect to Discord OAuth
  - GET /auth/callback?code=...     -> completes OAuth, stores session, redirects to dashboard
  - POST /auth/logout               -> clears session

You MUST configure the following environment variables:

  DISCORD_CLIENT_ID
  DISCORD_CLIENT_SECRET
  DISCORD_REDIRECT_URI   (e.g. "https://your.domain/auth/callback")

Optionally:

  ST_DASH_URL            (default "/dashboard/index.html")
  PLAYER_DASH_URL        (default "/dashboard/player.html")
"""

from __future__ import annotations

import os
from typing import Optional

import httpx
from fastapi import APIRouter, Request, HTTPException, status
from fastapi.responses import RedirectResponse, JSONResponse
from pydantic import BaseModel

router = APIRouter(prefix="/auth", tags=["auth"])

DISCORD_CLIENT_ID = os.getenv("DISCORD_CLIENT_ID")
DISCORD_CLIENT_SECRET = os.getenv("DISCORD_CLIENT_SECRET")
DISCORD_REDIRECT_URI = os.getenv("DISCORD_REDIRECT_URI")

ST_DASH_URL = os.getenv("ST_DASH_URL", "/dashboard/index.html")
PLAYER_DASH_URL = os.getenv("PLAYER_DASH_URL", "/dashboard/player.html")


class SessionPayload(BaseModel):
    ok: bool
    session: Optional[dict] = None


def _require_oauth_config():
    if not (DISCORD_CLIENT_ID and DISCORD_CLIENT_SECRET and DISCORD_REDIRECT_URI):
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Discord OAuth is not configured on the server.",
        )


@router.get("/login")
async def login(request: Request, mode: str = "st"):
    """
    Start Discord OAuth login.

    `mode` is "st" (Storyteller) or "player". We pass it via `state`
    so the callback knows which dashboard to send the user to.
    """
    _require_oauth_config()

    mode = mode if mode in ("st", "player") else "st"

    import urllib.parse

    params = {
        "client_id": DISCORD_CLIENT_ID,
        "redirect_uri": DISCORD_REDIRECT_URI,
        "response_type": "code",
        "scope": "identify",
        "state": mode,
        "prompt": "consent",
    }
    url = "https://discord.com/api/oauth2/authorize?" + urllib.parse.urlencode(params)
    return RedirectResponse(url, status_code=status.HTTP_302_FOUND)


@router.get("/callback")
async def callback(request: Request, code: str, state: Optional[str] = None):
    """
    Discord OAuth2 callback.

    Exchanges `code` for an access token, fetches the user profile,
    stores it in the signed server-side session, and redirects to the
    appropriate dashboard.
    """
    _require_oauth_config()

    token_data = {
        "client_id": DISCORD_CLIENT_ID,
        "client_secret": DISCORD_CLIENT_SECRET,
        "grant_type": "authorization_code",
        "code": code,
        "redirect_uri": DISCORD_REDIRECT_URI,
        "scope": "identify",
    }

    async with httpx.AsyncClient() as client:
        token_resp = await client.post(
            "https://discord.com/api/oauth2/token",
            data=token_data,
            headers={"Content-Type": "application/x-www-form-urlencoded"},
        )
        if token_resp.status_code != 200:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail=f"Discord token exchange failed ({token_resp.status_code})",
            )
        token_json = token_resp.json()
        access_token = token_json.get("access_token")
        if not access_token:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Discord did not return an access token.",
            )

        user_resp = await client.get(
            "https://discord.com/api/users/@me",
            headers={"Authorization": f"Bearer {access_token}"},
        )
        if user_resp.status_code != 200:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Failed to fetch Discord user profile.",
            )
        user = user_resp.json()

    # Build avatar URL (may be None)
    avatar_hash = user.get("avatar")
    user_id = user["id"]
    if avatar_hash:
        avatar_url = f"https://cdn.discordapp.com/avatars/{user_id}/{avatar_hash}.png"
    else:
        # Default avatar
        # https://cdn.discordapp.com/embed/avatars/{discriminator % 5}.png
        disc = user.get("discriminator")
        try:
            disc_int = int(disc) if disc is not None else 0
        except ValueError:
            disc_int = 0
        avatar_url = f"https://cdn.discordapp.com/embed/avatars/{disc_int % 5}.png"

    mode = state if state in ("st", "player") else "st"

    # Store in session for /auth/session + dashboards
    s = request.session
    s["sub"] = user_id
    s["username"] = user.get("global_name") or user.get("username") or f"User {user_id}"
    s["avatar"] = avatar_url
    s["mode"] = mode

    target = PLAYER_DASH_URL if mode == "player" else ST_DASH_URL
    return RedirectResponse(target, status_code=status.HTTP_302_FOUND)


@router.get("/session", response_model=SessionPayload)
async def session_info(request: Request):
    """
    Used by the dashboards (JS) to discover the logged-in user.

    Response:
      { "ok": true, "session": { "sub": "...", "username": "...", "mode": "...", "avatar": "..." } }
      { "ok": false, "session": null }  # if not logged in
    """
    s = request.session
    user_id = s.get("sub")
    if not user_id:
        return SessionPayload(ok=False, session=None)

    payload = {
        "sub": user_id,
        "username": s.get("username"),
        "mode": s.get("mode", "st"),
        "avatar": s.get("avatar"),
    }
    return SessionPayload(ok=True, session=payload)


@router.post("/logout")
async def logout(request: Request):
    """
    Clears the current session and returns a simple JSON payload.
    The front-end can then redirect back to /auth/login.
    """
    request.session.clear()
    return JSONResponse({"ok": True})
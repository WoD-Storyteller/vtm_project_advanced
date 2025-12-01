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

# ------------------------------------------------------------
# Simple admin API login (kept for tools / future use)
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
    This is mainly here so you still have a non-Discord way to talk
    to the API if you need it later.
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
            detail="Discord OAuth not configured (missing DISCORD_CLIENT_ID / SECRET).",
        )


def _make_state(request: Request) -> str:
    state = "".join(secrets.choice(string.ascii_letters + string.digits) for _ in range(32))
    request.session["oauth_state"] = state
    return state


@router.get("/auth/login")
async def discord_login(request: Request, mode: str = "player"):
    """
    Entry point used by the dashboard (links like /auth/login?mode=st).

    Starts the Discord OAuth2 flow and redirects the user to Discord.
    """
    _require_discord_config()

    # remember desired
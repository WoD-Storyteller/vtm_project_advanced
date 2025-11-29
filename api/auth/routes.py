from fastapi import APIRouter, Request, HTTPException
from fastapi.responses import RedirectResponse
import httpx
import os

router = APIRouter()

DISCORD_CLIENT_ID = os.getenv("DISCORD_CLIENT_ID")
DISCORD_CLIENT_SECRET = os.getenv("DISCORD_CLIENT_SECRET")
DISCORD_REDIRECT_URI = os.getenv("DISCORD_REDIRECT_URI", "https://bloodscriptengine.tech/oauth/callback")

DISCORD_API = "https://discord.com/api"


@router.get("/auth/login")
async def discord_login():
    url = (
        f"{DISCORD_API}/oauth2/authorize"
        f"?client_id={DISCORD_CLIENT_ID}"
        f"&redirect_uri={DISCORD_REDIRECT_URI}"
        f"&response_type=code"
        f"&scope=identify"
    )
    return RedirectResponse(url)


@router.get("/oauth/callback")
async def discord_callback(request: Request, code: str = None):
    if not code:
        raise HTTPException(400, "Missing code")

    # Exchange code for access token
    async with httpx.AsyncClient() as client:
        token_res = await client.post(
            f"{DISCORD_API}/oauth2/token",
            data={
                "client_id": DISCORD_CLIENT_ID,
                "client_secret": DISCORD_CLIENT_SECRET,
                "grant_type": "authorization_code",
                "code": code,
                "redirect_uri": DISCORD_REDIRECT_URI,
            },
            headers={"Content-Type": "application/x-www-form-urlencoded"}
        )

    if token_res.status_code != 200:
        raise HTTPException(401, "OAuth token exchange failed")

    access_token = token_res.json()["access_token"]

    # Fetch Discord profile
    async with httpx.AsyncClient() as client:
        user_res = await client.get(
            f"{DISCORD_API}/users/@me",
            headers={"Authorization": f"Bearer {access_token}"}
        )

    if user_res.status_code != 200:
        raise HTTPException(401, "OAuth user fetch failed")

    user = user_res.json()

    # Store session
    request.session["user"] = user

    return RedirectResponse("/dashboard")


@router.post("/auth/logout")
async def logout(request: Request):
    request.session.clear()
    return {"ok": True}
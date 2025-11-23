
import os
import requests
from fastapi import APIRouter, Request
from fastapi.responses import RedirectResponse

router = APIRouter()

CLIENT_ID = os.getenv("DISCORD_CLIENT_ID")
CLIENT_SECRET = os.getenv("DISCORD_CLIENT_SECRET")
REDIRECT_URI = "https://bloodscriptengine.tech/oauth/callback"

@router.get("/login")
async def login():
    url = (
        "https://discord.com/api/oauth2/authorize"
        f"?client_id={CLIENT_ID}"
        f"&redirect_uri={REDIRECT_URI}"
        "&response_type=code"
        "&scope=identify"
    )
    return RedirectResponse(url)

@router.get("/oauth/callback")
async def oauth_callback(request: Request, code: str=None):
    if not code:
        return {"error": "Missing OAuth Code"}

    data = {
        "client_id": CLIENT_ID,
        "client_secret": CLIENT_SECRET,
        "grant_type": "authorization_code",
        "code": code,
        "redirect_uri": REDIRECT_URI,
    }

    headers = {"Content-Type": "application/x-www-form-urlencoded"}

    token = requests.post("https://discord.com/api/oauth2/token", data=data, headers=headers).json()
    access = token.get("access_token")

    user = requests.get("https://discord.com/api/v10/users/@me",
        headers={"Authorization": f"Bearer {access}"}
    ).json()

    request.session["discord_user"] = user
    return RedirectResponse("/dashboard.html")

def get_current_user(request: Request):
    return request.session.get("discord_user")

import secrets
import httpx
from fastapi import APIRouter, Request
from fastapi.responses import RedirectResponse, JSONResponse

from auth_config import (
    DISCORD_CLIENT_ID,
    DISCORD_CLIENT_SECRET,
    DISCORD_REDIRECT_URI,
    DISCORD_AUTHORIZE_URL,
    DISCORD_TOKEN_URL,
    DISCORD_USER_URL,
    OAUTH_SCOPES
)

router = APIRouter()

# Simple in-memory store for state tokens
oauth_states = {}


@router.get("/login")
async def login():
    # Generate secure random state to prevent CSRF
    state = secrets.token_hex(16)
    oauth_states[state] = True

    # Build Discord OAuth URL
    url = (
        f"{DISCORD_AUTHORIZE_URL}"
        f"?client_id={DISCORD_CLIENT_ID}"
        f"&redirect_uri={DISCORD_REDIRECT_URI}"
        f"&response_type=code"
        f"&scope={OAUTH_SCOPES}"
        f"&state={state}"
    )

    return RedirectResponse(url)


@router.get("/oauth/callback")
async def oauth_callback(request: Request):
    code = request.query_params.get("code")
    state = request.query_params.get("state")

    if not code or not state:
        return JSONResponse({"error": "Missing code or state"}, status_code=400)

    if state not in oauth_states:
        return JSONResponse({"error": "Invalid or expired state"}, status_code=400)

    # Exchange authorization code for access token
    async with httpx.AsyncClient() as client:
        token_response = await client.post(
            DISCORD_TOKEN_URL,
            data={
                "client_id": DISCORD_CLIENT_ID,
                "client_secret": DISCORD_CLIENT_SECRET,
                "grant_type": "authorization_code",
                "code": code,
                "redirect_uri": DISCORD_REDIRECT_URI,
            },
            headers={"Content-Type": "application/x-www-form-urlencoded"},
        )

    if token_response.status_code != 200:
        return JSONResponse(
            {"error": "Failed to exchange OAuth token"},
            status_code=token_response.status_code
        )

    token_json = token_response.json()
    access_token = token_json["access_token"]

    # Fetch Discord user info
    async with httpx.AsyncClient() as client:
        user_response = await client.get(
            DISCORD_USER_URL,
            headers={"Authorization": f"Bearer {access_token}"}
        )

    if user_response.status_code != 200:
        return JSONResponse(
            {"error": "Failed to fetch Discord user"},
            status_code=user_response.status_code
        )

    user = user_response.json()

    # Return user data (can plug into database or JWT from here)
    return JSONResponse({
        "id": user["id"],
        "username": f"{user['username']}#{user['discriminator']}",
        "avatar": user["avatar"],
        "access_token": access_token
    })

# api/auth/routes.py
from __future__ import annotations

import jwt
import httpx
from fastapi import APIRouter, Depends, Header, HTTPException

from api.config import settings
from api.models import OAuthRequest, Role, User

router = APIRouter()


DISCORD_TOKEN_URL = "https://discord.com/api/oauth2/token"
DISCORD_ME_URL = "https://discord.com/api/users/@me"


def create_jwt(user: User) -> str:
    payload = {
        "sub": user.id,
        "name": user.display_name,
        "roles": [r.value for r in user.roles],
    }
    return jwt.encode(payload, settings.jwt_secret, algorithm=settings.jwt_algorithm)


def parse_jwt(token: str) -> User:
    try:
        decoded = jwt.decode(
            token,
            settings.jwt_secret,
            algorithms=[settings.jwt_algorithm],
        )
    except jwt.PyJWTError:
        raise HTTPException(status_code=401, detail="Invalid token")

    roles = [Role(r) for r in decoded.get("roles", [])]
    return User(
        id=str(decoded.get("sub")),
        display_name=str(decoded.get("name")),
        roles=roles,
    )


def get_current_user(authorization: str | None = Header(default=None)) -> User:
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Missing Authorization header")
    token = authorization.split(" ", 1)[1]
    return parse_jwt(token)


@router.post("/oauth/callback")
async def oauth_callback(body: OAuthRequest) -> dict:
    """
    Called by the Windows app after Discord redirects back to
    http://localhost:8765/callback and the app gets a ?code.
    """
    if body.redirect_uri != settings.redirect_uri:
        raise HTTPException(status_code=400, detail="redirect_uri mismatch")

    data = {
        "client_id": settings.discord_client_id,
        "client_secret": settings.discord_client_secret,
        "grant_type": "authorization_code",
        "code": body.code,
        "redirect_uri": body.redirect_uri,
    }

    async with httpx.AsyncClient() as client:
        resp = await client.post(DISCORD_TOKEN_URL, data=data)

    if resp.status_code != 200:
        raise HTTPException(
            status_code=resp.status_code,
            detail=f"Discord token error: {resp.text}",
        )

    token_data = resp.json()
    discord_access_token = token_data.get("access_token")
    if not discord_access_token:
        raise HTTPException(status_code=500, detail="No access_token from Discord")

    # Fetch Discord user
    headers = {"Authorization": f"Bearer {discord_access_token}"}
    async with httpx.AsyncClient() as client:
        me_resp = await client.get(DISCORD_ME_URL, headers=headers)

    if me_resp.status_code != 200:
        raise HTTPException(
            status_code=me_resp.status_code,
            detail=f"Discord /users/@me error: {me_resp.text}",
        )

    me = me_resp.json()
    user = User(
        id=str(me["id"]),
        display_name=me.get("global_name") or me.get("username") or "Discord User",
        # You said: "Bot" and "all of them" – for now, give both roles.
        roles=[Role.player, Role.st],
    )

    jwt_token = create_jwt(user)
    return {"access_token": jwt_token, "user": user.dict()}


@router.get("/me", response_model=User)
async def me(user: User = Depends(get_current_user)) -> User:
    """Used by the Windows app to test the JWT + show who is logged in."""
    return user

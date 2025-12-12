from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import httpx

app = FastAPI()

class OAuthPayload(BaseModel):
    code: str
    redirect_uri: str

DISCORD_TOKEN_URL = "https://discord.com/api/oauth2/token"
DISCORD_ME_URL = "https://discord.com/api/users/@me"

@app.post("/oauth/callback")
async def oauth_callback(payload: OAuthPayload):
    data = {
        "client_id": "<YOUR_CLIENT_ID>",
        "client_secret": "<YOUR_CLIENT_SECRET>",
        "grant_type": "authorization_code",
        "code": payload.code,
        "redirect_uri": payload.redirect_uri,
    }

    async with httpx.AsyncClient() as client:
        token_res = await client.post(DISCORD_TOKEN_URL, data=data)

    if token_res.status_code != 200:
        raise HTTPException(status_code=400, detail=token_res.text)

    token_json = token_res.json()
    access_token = token_json.get("access_token")

    if not access_token:
        raise HTTPException(status_code=400, detail="No access_token from Discord")

    async with httpx.AsyncClient() as client:
        user_res = await client.get(
            DISCORD_ME_URL,
            headers={"Authorization": f"Bearer {access_token}"}
        )

    return {
        "access_token": access_token,
        "user": user_res.json(),
    }
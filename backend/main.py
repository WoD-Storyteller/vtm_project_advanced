
from fastapi import FastAPI, Request
from fastapi.responses import RedirectResponse
from auth.session import add_session_middleware
from auth.discord_oauth import router as discord_oauth_router, get_current_user

app = FastAPI()

add_session_middleware(app, secret_key="CHANGE_ME_SECRET")

app.include_router(discord_oauth_router)

@app.get("/dashboard/{path:path}")
async def dashboard_gatekeeper(request: Request, path: str):
    user = get_current_user(request)
    if not user:
        return RedirectResponse("/login")
    return {"status": "ok", "user": user}

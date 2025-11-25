# api/main.py
import logging
from fastapi import FastAPI
from dotenv import load_dotenv

from api.config import settings
from api.auth.session import add_session_middleware
from api.auth.routes import router as auth_router

load_dotenv()

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)

app = FastAPI(title="VTM API", version="1.0.0")

add_session_middleware(app, secret_key=settings.SECRET_KEY)

app.include_router(auth_router, prefix="/auth", tags=["auth"])

@app.get("/")
async def root():
    return {"status": "ok", "service": "vtm_api"}

# api/main.py

import logging
import os

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv

# --- Load environment variables ---
load_dotenv()

# --- Logging ---
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("vtm_api")

# --- App ---
app = FastAPI(
    title="Blood Script Engine API",
    version="1.0.0",
)

# --- CORS (Flutter + localhost + domain) ---
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost",
        "http://localhost:8765",
        "https://bloodscriptengine.tech",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# =====================================================
# ROUTE REGISTRATION
# =====================================================

# Auth / OAuth / Session
from api.auth.routes import router as auth_router
from api.auth.session import add_session_middleware

add_session_middleware(
    app,
    secret_key=os.getenv("SECRET_KEY", "dev-secret"),
)

app.include_router(auth_router, prefix="/auth", tags=["auth"])

# Alerts (player + ST)
from api.alert_routes import router as alerts_router
app.include_router(alerts_router, tags=["alerts"])

# Maps / Director state
from api.map_routes import router as map_router
app.include_router(map_router, tags=["maps"])

# =====================================================
# ROOT / HEALTH
# =====================================================

@app.get("/")
async def root():
    return {
        "status": "ok",
        "service": "Blood Script Engine API",
    }

@app.get("/health")
async def health():
    return {"status": "healthy"}
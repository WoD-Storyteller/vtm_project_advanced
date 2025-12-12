# api/main.py
import logging
import os

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv

from api.alert_routes import router as alerts_router
from api.auth.routes import router as auth_router
from api.auth.session import add_session_middleware
from api.config import settings

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)


def create_app() -> FastAPI:
    load_dotenv()

    app = FastAPI(
        title="Blood Script Bot API",
        description="Backend API for the Blood Script Windows Dashboard",
        version="1.0.0",
    )

    # CORS for the Windows Flutter app
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.allowed_origins,
        allow_methods=["*"],
        allow_headers=["*"],
        allow_credentials=True,
    )

    # Session middleware (mostly legacy / harmless now)
    secret_key = os.getenv("SECRET_KEY", "dev-session-key")
    add_session_middleware(app, secret_key=secret_key)

    # Routers
    app.include_router(auth_router)
    app.include_router(alerts_router)

    @app.get("/")
    async def root():
        return {"message": "Blood Script Bot API is running", "version": "1.0.0"}

    return app


app = create_app()

# api/config.py
import os
from pydantic import BaseModel


class Settings(BaseModel):
    # Discord OAuth app
    discord_client_id: str
    discord_client_secret: str

    # Must match your Discord app redirect + Flutter config
    redirect_uri: str = "http://localhost:8765/callback"

    # JWT used by the Windows client
    jwt_secret: str = "change-me"
    jwt_algorithm: str = "HS256"

    # CORS – keep wide open for now (Windows app only)
    allowed_origins: list[str] = ["*"]


def load_settings() -> Settings:
    raw = {
        "discord_client_id": os.getenv("DISCORD_CLIENT_ID", ""),
        "discord_client_secret": os.getenv("DISCORD_CLIENT_SECRET", ""),
        "redirect_uri": os.getenv("REDIRECT_URI", "http://localhost:8765/callback"),
        "jwt_secret": os.getenv("JWT_SECRET", "change-me"),
        "jwt_algorithm": os.getenv("JWT_ALGORITHM", "HS256"),
    }
    return Settings(**raw)


settings = load_settings()

# api/config.py
from pydantic import BaseSettings

class Settings(BaseSettings):
    SECRET_KEY: str

    GOOGLE_API_KEY: str
    DISCORD_BOT_TOKEN: str
    BOT_OWNER_ID: str

    class Config:
        env_file = ".env"

settings = Settings()

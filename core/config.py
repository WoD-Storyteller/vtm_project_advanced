# core/config.py
import os
from dotenv import load_dotenv
import google.generativeai as genai

load_dotenv()

GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
DISCORD_BOT_TOKEN = os.getenv("DISCORD_BOT_TOKEN")
BOT_OWNER_ID_RAW = os.getenv("BOT_OWNER_ID")

if not GOOGLE_API_KEY:
    raise RuntimeError("GOOGLE_API_KEY missing from environment/.env")

if not DISCORD_BOT_TOKEN:
    raise RuntimeError("DISCORD_BOT_TOKEN missing from environment/.env")

if not BOT_OWNER_ID_RAW:
    raise RuntimeError("BOT_OWNER_ID missing from environment/.env")

try:
    BOT_OWNER_ID = int(BOT_OWNER_ID_RAW)
except ValueError:
    raise RuntimeError("BOT_OWNER_ID must be an integer")

# Configure Gemini
genai.configure(api_key=GOOGLE_API_KEY)

ai_model_json = genai.GenerativeModel(
    "gemini-2.0-flash",
    generation_config={"response_mime_type": "application/json"},
)

ai_model_text = genai.GenerativeModel("gemini-2.0-flash")

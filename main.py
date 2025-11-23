import logging
logging.basicConfig(level=logging.INFO)
from fastapi import FastAPI
import discord
from discord.ext import commands
import os
import google.generativeai as genai
from utils import load_data_from_file, save_data
from dotenv import load_dotenv

from auth.discord_oauth import router as discord_oauth_router
from auth.session import add_session_middleware
import os

load_dotenv()

app = FastAPI()

add_session_middleware(app, secret_key=os.getenv("SECRET_KEY"))
app.include_router(discord_oauth_router)

# rest of your existing routes...

# your existing routes continue...
@app.get("/")
async def root():
    return {"message": "hello"}
# --- CONFIG --- test
GOOGLE_API_KEY = os.environ.get("GOOGLE_API_KEY")
DISCORD_BOT_TOKEN = os.environ.get("DISCORD_BOT_TOKEN")
BOT_OWNER_ID = os.environ.get("BOT_OWNER_ID")

if not GOOGLE_API_KEY or not DISCORD_BOT_TOKEN:
    print("ERROR: API Keys not set in environment variables or .env file.")
    exit()

if not BOT_OWNER_ID:
    print("ERROR: BOT_OWNER_ID not set in environment variables or .env file.")
    exit()

# --- SETUP ---
genai.configure(api_key=GOOGLE_API_KEY)
ai_model_json = genai.GenerativeModel(
    'gemini-2.0-flash',
    generation_config={"response_mime_type": "application/json"}
)
ai_model_text = genai.GenerativeModel('gemini-2.0-flash')

intents = discord.Intents.default()
intents.message_content = True
intents.members = True

class StorytellerBot(commands.Bot):
    def __init__(self, owner_id):
        super().__init__(
            command_prefix="!", 
            intents=intents, 
            help_command=None,
            owner_id=owner_id
        )
        
        # --- DATA MIGRATION & LOADING ---
        raw_data = load_data_from_file()
        if "patrons" in raw_data and "guilds" in raw_data:
            # print("Patron-based data file found. Extracting guilds for beta mode.")
            self.data_store = raw_data.get("guilds", {})
            save_data(self.data_store)
        else:
            # print("Legacy or new beta data file found.")
            self.data_store = raw_data

        self.ai_model_json = ai_model_json
        self.ai_model_text = ai_model_text
    
    async def setup_hook(self):
        cogs_to_load = ['admin', 'player', 'storyteller', 'scene', 'combat', 'hunting', 'disciplines']
        for cog in cogs_to_load:
            try:
                await self.load_extension(f"cogs.{cog}")
                print(f"Loaded cog: {cog}")
            except Exception as e:
                print(f"Failed to load cog {cog}: {e}")
        print("All Cogs loaded.")

    def save_data(self):
        save_data(self.data_store)

bot = StorytellerBot(owner_id=int(BOT_OWNER_ID))

@bot.event
async def on_ready():
    print(f'Logged in as {bot.user}')
    print(f'Bot Owner ID: {bot.owner_id}')
    print(f'Tracking {len(bot.data_store.get("guilds", {}))} servers.')
 
if __name__ == "__main__":
    bot.run(DISCORD_BOT_TOKEN)
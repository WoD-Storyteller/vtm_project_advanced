# bot/bot.py

import logging
import discord
from discord.ext import commands
import google.generativeai as genai

from api.config import settings


# ------------- Logging -------------
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [BOT] %(levelname)s: %(message)s"
)


# ------------- Bot Factory -------------
def create_bot() -> commands.Bot:
    intents = discord.Intents.default()
    intents.message_content = True  # Required for message-based commands

    bot = commands.Bot(command_prefix="!", intents=intents)

    # Load all cogs cleanly
    initial_cogs = [
        "bot.cogs.admin",
        "bot.cogs.storyteller",
        "bot.cogs.player",
        "bot.cogs.combat",
        "bot.cogs.hunting",
        "bot.cogs.scene",
    ]

    for cog in initial_cogs:
        try:
            bot.load_extension(cog)
            logging.info(f"Loaded cog: {cog}")
        except Exception as e:
            logging.error(f"Failed to load cog {cog}: {e}")

    @bot.event
    async def on_ready():
        logging.info(f"Bot logged in as {bot.user} (ID: {bot.user.id})")

    return bot


# ------------- Bot Runner -------------
def run_bot():
    # Gemini config
    genai.configure(api_key=settings.GOOGLE_API_KEY)

    bot = create_bot()
    bot.run(settings.DISCORD_BOT_TOKEN)


if __name__ == "__main__":
    run_bot()

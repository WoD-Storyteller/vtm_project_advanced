# bot/bot.py
import discord
from discord.ext import commands
import google.generativeai as genai

from api.config import settings

def create_bot():
    intents = discord.Intents.default()
    intents.message_content = True

    bot = commands.Bot(command_prefix="!", intents=intents)

    bot.load_extension("bot.cogs.storyteller")
    bot.load_extension("bot.cogs.player")
    bot.load_extension("bot.cogs.travel")
    bot.load_extension("bot.cogs.hunt")

    @bot.event
    async def on_ready():
        print(f"Logged in as {bot.user}")

    return bot

def run_bot():
    genai.configure(api_key=settings.GOOGLE_API_KEY)
    bot = create_bot()
    bot.run(settings.DISCORD_BOT_TOKEN)

if __name__ == "__main__":
    run_bot()

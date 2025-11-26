import os
import discord
from discord.ext import commands
from dotenv import load_dotenv

load_dotenv()

TOKEN = os.getenv("DISCORD_BOT_TOKEN")

class VTM(commands.Bot):
    def __init__(self):
        intents = discord.Intents.all()
        super().__init__(command_prefix="!", intents=intents)

    async def setup_hook(self):
        await self.load_extension("cogs.admin")
        await self.load_extension("cogs.player")
        await self.load_extension("cogs.hunting")
        await self.load_extension("cogs.scene")
        await self.load_extension("cogs.combat")
        await self.load_extension("cogs.storyteller")

    async def on_ready(self):
        print(f"Bot online as {self.user}")

bot = VTM()
bot.run(TOKEN)
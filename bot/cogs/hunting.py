from discord.ext import commands
from core.vampires.hunting import perform_hunt

class Hunting(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name="feed")
    async def feed(self, ctx, zone: str = "urban"):
        """Another hook into the hunting system."""
        result = perform_hunt(zone, hunger=1)
        await ctx.send(f"You fed in `{zone}` → {result['result']}")

async def setup(bot):
    await bot.add_cog(Hunting(bot))

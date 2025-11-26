from discord.ext import commands
from core.vampires.hunting import perform_hunt

class Player(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name="hunt")
    async def hunt(self, ctx, zone: str = "urban"):
        """Basic hunger system."""
        result = perform_hunt(zone, hunger=2)
        await ctx.send(f"You hunted in `{zone}` → {result['result']}")

async def setup(bot):
    await bot.add_cog(Player(bot))

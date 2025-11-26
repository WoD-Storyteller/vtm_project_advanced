from discord.ext import commands

class Combat(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name="attack")
    async def attack(self, ctx, target: str):
        await ctx.send(f"You attack `{target}`! (combat system WIP)")

async def setup(bot):
    await bot.add_cog(Combat(bot))

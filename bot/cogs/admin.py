from discord.ext import commands

class Admin(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name="reload")
    async def reload(self, ctx, cog: str):
        """Reload a specific cog file."""
        try:
            self.bot.unload_extension(f"bot.cogs.{cog}")
            self.bot.load_extension(f"bot.cogs.{cog}")
            await ctx.send(f"Reloaded `{cog}`.")
        except Exception as e:
            await ctx.send(f"Error: `{str(e)}`")

async def setup(bot):
    await bot.add_cog(Admin(bot))

from discord.ext import commands
from core.vampires.scenes import generate_scene_description

class Scene(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name="describe")
    async def describe(self, ctx, *, location: str):
        text = generate_scene_description(location)
        await ctx.send(text)

async def setup(bot):
    await bot.add_cog(Scene(bot))

from discord.ext import commands
from core.director.AIDirector import AIDirector

director = AIDirector()

class Storyteller(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name="scene")
    async def generate_scene(self, ctx, *, location: str):
        """Generate a VtM story scene using the AI Director."""
        result = director.generate_scene(location, travelers=[], risk=2)
        await ctx.send(result.get("intro_text", "No scene generated."))

async def setup(bot):
    await bot.add_cog(Storyteller(bot))

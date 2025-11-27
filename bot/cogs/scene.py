import discord
from discord.ext import commands


class SceneCog(commands.Cog):
    """
    Lightweight manual scene tools.

    Commands:
      !scene start <location>  – mark a scene as started in this channel
      !scene end               – end the current scene
      !scene narrate <text>    – echo narration in a formatted way
    """

    def __init__(self, bot):
        self.bot = bot
        self.active_scenes = {}  # channel_id -> location string

    @commands.group(name="scene", invoke_without_command=True)
    async def scene(self, ctx: commands.Context):
        await ctx.reply("Use: !scene start <location>, !scene end, !scene narrate <text>")

    @scene.command(name="start")
    async def scene_start(self, ctx: commands.Context, *, location: str):
        """
        Start a scene in this channel with a location label.
        """
        self.active_scenes[ctx.channel.id] = location
        await ctx.send(f"**Scene started in {location}.**")

    @scene.command(name="end")
    async def scene_end(self, ctx: commands.Context):
        """
        End the current scene in this channel.
        """
        self.active_scenes.pop(ctx.channel.id, None)
        await ctx.send("**Scene ended.**")

    @scene.command(name="narrate")
    async def scene_narrate(self, ctx: commands.Context, *, text: str):
        """
        Simple formatted narration helper.
        """
        location = self.active_scenes.get(ctx.channel.id, "Unknown Location")
        embed = discord.Embed(
            title=f"Scene – {location}",
            description=text,
            color=discord.Color.blurple(),
        )
        embed.set_footer(text=f"Narrated by {ctx.author.display_name}")
        await ctx.send(embed=embed)


async def setup(bot):
    await bot.add_cog(SceneCog(bot))
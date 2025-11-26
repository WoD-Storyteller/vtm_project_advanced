import discord
from discord.ext import commands
from core.vampires.scenes import generate_scene_response

class SceneCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.active_scenes = {}

    @commands.group(name="scene", invoke_without_command=True)
    async def scene(self, ctx):
        await ctx.reply("Use: !scene start <location>, !scene end, !scene narrate <text>")

    @scene.command(name="start")
    async def scene_start(self, ctx, *, location):
        self.active_scenes[ctx.channel.id] = location
        await ctx.send(f"**Scene started in {location}.**")

    @scene.command(name="end")
    async def scene_end(self, ctx):
        self.active_scenes.pop(ctx.channel.id, None)
        await ctx.send("**Scene ended.**")

    @scene.command(name="narrate")
    async def scene_narrate(self, ctx, *, text):
        resp = generate_scene_response(text)
        await ctx.send(resp)

async def setup(bot):
    await bot.add_cog(SceneCog(bot))
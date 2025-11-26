import discord
from discord.ext import commands
from core.utils import get_guild_data
from core.vampires.hunting import predator_hunt, simple_feed
from core.vampires.scenes import generate_scene_description
from core.hunters.travel import travel_to

class PlayerCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name="sheet")
    async def sheet(self, ctx, *, name=None):
        data = get_guild_data(ctx.guild.id)
        char = data["characters"].get(str(ctx.author.id))
        if not char:
            return await ctx.reply("No sheet found.")
        await ctx.send(embed=discord.Embed(
            title=f"{char['name']}'s Sheet",
            description=f"Clan: {char['clan']}\nHunger: {char['hunger']}\nHP: {char['hp']}"
        ))

    @commands.command(name="stats")
    async def stats(self, ctx):
        data = get_guild_data(ctx.guild.id)
        char = data["characters"].get(str(ctx.author.id))
        if not char:
            return await ctx.reply("You have no character.")
        await ctx.reply(f"HP: {char['hp']} | Hunger: {char['hunger']}")

    @commands.command(name="say")
    async def say(self, ctx, *, speech):
        await ctx.send(f"**{ctx.author.display_name}:** {speech}")

    @commands.command(name="travel")
    async def travel(self, ctx, *, location):
        result = travel_to(ctx.guild.id, ctx.author.id, location)
        await ctx.reply(result)

    @commands.command(name="hunt")
    async def hunt(self, ctx, *, predator_type=None):
        data = get_guild_data(ctx.guild.id)
        char = data["characters"].get(str(ctx.author.id))

        if not char:
            return await ctx.reply("You have no character.")

        if predator_type or char.get("predator_type"):
            result = predator_hunt(ctx.guild.id, ctx.author.id, predator_type)
        else:
            result = simple_feed(ctx.guild.id, ctx.author.id)

        await ctx.reply(result)

    @commands.command(name="fear")
    async def fear(self, ctx, *, target):
        await ctx.reply(f"You intimidate **{target}**. They flinch.")

    @commands.command(name="roll")
    async def roll(self, ctx, *, dice_pool):
        await ctx.reply(f"Rolling **{dice_pool}** (placeholder).")

async def setup(bot):
    await bot.add_cog(PlayerCog(bot))
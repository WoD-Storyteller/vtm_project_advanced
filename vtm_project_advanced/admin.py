import discord
from discord.ext import commands

class AdminCommands(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
    async def cog_check(self, ctx):
        return await self.bot.is_owner(ctx.author)
    @commands.command()
    async def admin_test(self, ctx):
        await ctx.send("Admin online.")
async def setup(bot):
    await bot.add_cog(AdminCommands(bot))
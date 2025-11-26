import discord
from discord.ext import commands

class AdminCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name="admin_test")
    @commands.is_owner()
    async def admin_test(self, ctx):
        await ctx.reply("Admin online.")

async def setup(bot):
    await bot.add_cog(AdminCog(bot))
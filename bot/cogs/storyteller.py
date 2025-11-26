import discord
from discord.ext import commands
from core.utils import get_guild_data, save_data
from core.director.AIDirector import AIDirector

class StorytellerCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.group(name="st")
    async def st(self, ctx):
        if not ctx.author.guild_permissions.administrator:
            return await ctx.reply("ST only.")
        if ctx.invoked_subcommand is None:
            await ctx.reply("ST commands: npc, char, setchannel, narrate")

    @st.group(name="npc")
    async def st_npc(self, ctx):
        pass

    @st_npc.command(name="add")
    async def npc_add(self, ctx, *, name):
        data = get_guild_data(ctx.guild.id)
        data["npcs"][name] = {"name": name}
        save_data(data)
        await ctx.reply(f"NPC **{name}** added.")

    @st_npc.command(name="clear")
    async def npc_clear(self, ctx):
        data = get_guild_data(ctx.guild.id)
        data["npcs"] = {}
        save_data(data)
        await ctx.reply("All NPCs cleared.")

    @st_npc.command(name="avatar")
    async def npc_avatar(self, ctx, name, url):
        data = get_guild_data(ctx.guild.id)
        data["npcs"][name]["avatar"] = url
        save_data(data)
        await ctx.reply(f"Avatar updated for {name}.")

    @st_npc.command(name="bio")
    async def npc_bio(self, ctx, name, *, bio):
        data = get_guild_data(ctx.guild.id)
        data["npcs"][name]["bio"] = bio
        save_data(data)
        await ctx.reply(f"Bio updated for {name}.")

    @st.group(name="char")
    async def st_char(self, ctx):
        pass

    @st_char.command(name="setstats")
    async def st_setstats(self, ctx, name, stat, value: int):
        data = get_guild_data(ctx.guild.id)
        data["characters"][name][stat] = value
        save_data(data)
        await ctx.reply(f"{name}'s {stat} updated.")

    @st_char.command(name="inspect")
    async def st_inspect(self, ctx, name):
        data = get_guild_data(ctx.guild.id)
        char = data["characters"].get(name)
        if not char:
            return await ctx.reply("Character not found.")
        await ctx.send(f"```{char}```")

    @st.command(name="setchannel")
    async def setchannel(self, ctx, channel: discord.TextChannel):
        data = get_guild_data(ctx.guild.id)
        data["admin_channel"] = channel.id
        save_data(data)
        await ctx.reply(f"Admin channel set to {channel.mention}.")

    @st.command(name="narrate")
    async def narrate(self, ctx, *, text):
        director = AIDirector()
        result = await director.generate_scene_from_text(text)
        await ctx.send(result)

async def setup(bot):
    await bot.add_cog(StorytellerCog(bot))